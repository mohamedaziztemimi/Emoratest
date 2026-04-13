"""Emotion classifier for behavioral signals.

Classifies 8 emotions (confusion, frustration, delight, boredom, anxiety,
focus, hesitation, satisfaction) from extracted behavioral features.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
from pathlib import Path

# Try to import XGBoost, fallback to sklearn
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    from sklearn.ensemble import GradientBoostingClassifier

if TYPE_CHECKING:
    pass


# ── Emotion Enum ────────────────────────────────────────────────────────


class Emotion(str, Enum):
    """8 emotion categories for classification."""

    CONFUSION = "confusion"
    FRUSTRATION = "frustration"
    DELIGHT = "delight"
    BOREDOM = "boredom"
    ANXIETY = "anxiety"
    FOCUS = "focus"
    HESITATION = "hesitation"
    SATISFACTION = "satisfaction"

    @classmethod
    def all_emotions(cls) -> list[str]:
        """Get list of all emotion strings."""
        return [e.value for e in cls]


# ── Valence-Arousal Mapping ────────────────────────────────────────────

# Hardcoded valence (-1 to 1) and arousal (0 to 1) for each emotion
VALENCE_AROUSAL = {
    Emotion.CONFUSION: (-0.3, 0.6),
    Emotion.FRUSTRATION: (-0.7, 0.8),
    Emotion.DELIGHT: (0.8, 0.7),
    Emotion.BOREDOM: (-0.2, 0.1),
    Emotion.ANXIETY: (-0.5, 0.9),
    Emotion.FOCUS: (0.3, 0.7),
    Emotion.HESITATION: (-0.1, 0.4),
    Emotion.SATISFACTION: (0.7, 0.3),
}


# ── Rule-Based Overrides ────────────────────────────────────────────────────


class RuleOverrides:
    """Rule-based emotion overrides applied on top of model predictions."""

    @staticmethod
    def apply(features: np.ndarray, feature_names: list[str]) -> dict[str, float]:
        """Apply rule-based overrides to emotion scores.

        Rules:
        - rage_click_count >= 3 → force frustration += 0.3
        - scroll_reversal_count >= 5 + cursor_idle_ratio > 0.6 → confusion += 0.2
        - session_duration > 300s + click_heatmap_entropy > 0.8 → delight += 0.15

        Args:
            features: Feature array.
            feature_names: List of feature names matching array indices.

        Returns:
            Dict mapping emotion to confidence adjustment.
        """
        adjustments = {emotion: 0.0 for emotion in Emotion.all_emotions()}

        try:
            # Create feature dict for easy lookup
            feature_dict = dict(zip(feature_names, features))

            # Rule 1: Rage clicks indicate frustration
            rage_click_idx = feature_names.index("click_rage_click_count")
            rage_clicks = feature_dict["click_rage_click_count"]

            if rage_clicks >= 3:
                adjustments[Emotion.FRUSTRATION.value] += 0.3

            # Rule 2: Scroll reversals + high idle ratio indicate confusion
            scroll_reversal_idx = feature_names.index("scroll_reversal_count")
            idle_ratio_idx = feature_names.index("mouse_cursor_idle_ratio")
            scroll_reversals = feature_dict["scroll_reversal_count"]
            idle_ratio = feature_dict["mouse_cursor_idle_ratio"]

            if scroll_reversals >= 5 and idle_ratio > 0.6:
                adjustments[Emotion.CONFUSION.value] += 0.2

            # Rule 3: Long session + high entropy indicates delight (engagement spread)
            duration_idx = feature_names.index("dwell_total_session_duration")
            entropy_idx = feature_names.index("click_heatmap_entropy")
            duration = feature_dict["dwell_total_session_duration"]
            entropy = feature_dict["click_heatmap_entropy"]

            if duration > 300 and entropy > 0.8:
                adjustments[Emotion.DELIGHT.value] += 0.15

            # Rule 4: High form abandonment + hesitation → anxiety
            abandon_idx = feature_names.index("dwell_form_abandon_count")
            hesitation_features = [
                "mouse_hover_duration_on_cta",
                "mouse_velocity_mean",
            ]
            if all(f in feature_names for f in hesitation_features):
                abandons = feature_dict["dwell_form_abandon_count"]
                hover_duration = feature_dict["mouse_hover_duration_on_cta"]
                velocity = feature_dict["mouse_velocity_mean"]

                if abandons >= 2 and (hover_duration > 2000 or velocity < 50):
                    adjustments[Emotion.ANXIETY.value] += 0.15
                    adjustments[Emotion.HESITATION.value] += 0.15

            # Rule 5: High reading pauses + low velocity → focus
            reading_pause_idx = feature_names.index("scroll_reading_pause_count")
            reading_pauses = feature_dict["scroll_reading_pause_count"]

            if reading_pauses >= 5 and velocity < 100:
                adjustments[Emotion.FOCUS.value] += 0.2

            # Rule 6: High dead clicks + idle → boredom
            dead_click_idx = feature_names.index("click_dead_click_count")
            dead_clicks = feature_dict["click_dead_click_count"]

            if dead_clicks >= 3 and idle_ratio > 0.7:
                adjustments[Emotion.BOREDOM.value] += 0.2

            # Rule 7: Low double-click rate + smooth movement → satisfaction
            double_click_idx = feature_names.index("click_double_click_rate")
            velocity_std_idx = feature_names.index("mouse_velocity_std")
            double_click_rate = feature_dict["click_double_click_rate"]
            velocity_std = feature_dict["mouse_velocity_std"]

            if double_click_rate < 0.05 and velocity_std < 50:
                adjustments[Emotion.SATISFACTION.value] += 0.15

        except (ValueError, KeyError):
            pass

        return adjustments


# ── Result Classes ────────────────────────────────────────────────────


@dataclass
class EmotionResult:
    """Result of emotion classification."""

    primary_emotion: str
    confidence: float
    all_scores: dict[str, float]
    valence: float  # -1 to 1
    arousal: float  # 0 to 1
    rule_adjustments: dict[str, float] | None = None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "primary_emotion": self.primary_emotion,
            "confidence": round(self.confidence, 4),
            "all_scores": {k: round(v, 4) for k, v in self.all_scores.items()},
            "valence": round(self.valence, 4),
            "arousal": round(self.arousal, 4),
            "rule_adjustments": self.rule_adjustments,
        }


# ── Emotion Classifier ───────────────────────────────────────────────────


class EmotionClassifier:
    """Emotion classifier using Gradient Boosting with rule-based overrides.

    Architecture:
    - XGBoost (preferred) or sklearn GradientBoostingClassifier (fallback)
    - Rule-based override layer applied to model predictions
    - Valence-arousal mapping from primary emotion
    """

    def __init__(self, use_xgboost: bool = True, n_estimators: int = 100):
        """Initialize emotion classifier.

        Args:
            use_xgboost: Prefer XGBoost if available.
            n_estimators: Number of trees in the ensemble.
        """
        self.use_xgboost = use_xgboost and HAS_XGBOOST
        self.n_estimators = n_estimators
        self.feature_names: list[str] = []
        self.emotions: list[str] = Emotion.all_emotions()
        self.model = None
        self.is_fitted = False

        # Initialize model
        if self.use_xgboost:
            self.model = xgb.XGBClassifier(
                n_estimators=n_estimators,
                max_depth=6,
                learning_rate=0.1,
                objective="multi:softprob",
                num_class=8,
                random_state=42,
                eval_metric="mlogloss",
            )
        else:
            self.model = GradientBoostingClassifier(
                n_estimators=n_estimators,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
            )

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: list[str] | None = None,
    ) -> dict:
        """Train the emotion classifier.

        Args:
            X: Feature matrix of shape (n_samples, n_features).
            y: Emotion labels (strings).
            feature_names: List of feature names.

        Returns:
            Dict with training metrics.
        """
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]

        # Encode labels to integers
        label_to_idx = {emotion: idx for idx, emotion in enumerate(self.emotions)}
        idx_to_label = {idx: emotion for emotion, idx in label_to_idx.items()}
        y_encoded = np.array([label_to_idx[label] for label in y])

        # Train model
        if self.use_xgboost:
            self.model.fit(
                X,
                y_encoded,
                verbose=False,
            )
        else:
            self.model.fit(X, y_encoded)

        self.is_fitted = True

        # Calculate training metrics
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            confusion_matrix,
        )

        y_pred = self.model.predict(X)

        metrics = {
            "accuracy": accuracy_score(y_encoded, y_pred),
            "precision": precision_score(y_encoded, y_pred, average="weighted", zero_division=0),
            "recall": recall_score(y_encoded, y_pred, average="weighted", zero_division=0),
            "f1": f1_score(y_encoded, y_pred, average="weighted", zero_division=0),
            "confusion_matrix": confusion_matrix(y_encoded, y_pred).tolist(),
            "label_mapping": idx_to_label,
        }

        return metrics

    def predict(self, features: np.ndarray) -> EmotionResult:
        """Predict emotion for a single feature vector.

        Args:
            features: Feature vector of shape (n_features,).

        Returns:
            EmotionResult with primary emotion, confidence, valence, arousal.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be trained before prediction")

        # Get prediction probabilities
        if self.use_xgboost:
            probs = self.model.predict_proba(features.reshape(1, -1))[0]
        else:
            probs = self.model.predict_proba(features.reshape(1, -1))[0]

        # Create score dict
        scores = {emotion: probs[i] for i, emotion in enumerate(self.emotions)}

        # Apply rule-based overrides
        adjustments = RuleOverrides.apply(features, self.feature_names or [])

        # Apply adjustments to scores
        for emotion, adj in adjustments.items():
            if emotion in scores:
                scores[emotion] = np.clip(scores[emotion] + adj, 0.0, 1.0)

        # Find primary emotion (highest score)
        primary_emotion = max(scores, key=scores.get)
        confidence = scores[primary_emotion]

        # Get valence and arousal for primary emotion
        valence, arousal = VALENCE_AROUSAL.get(Emotion(primary_emotion), (0.0, 0.5))

        return EmotionResult(
            primary_emotion=primary_emotion,
            confidence=float(confidence),
            all_scores=scores,
            valence=float(valence),
            arousal=float(arousal),
            rule_adjustments=adjustments,
        )

    def predict_batch(self, features_list: list[np.ndarray]) -> list[EmotionResult]:
        """Predict emotions for multiple feature vectors.

        Args:
            features_list: List of feature vectors.

        Returns:
            List of EmotionResult objects.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be trained before prediction")

        results = []
        for features in features_list:
            results.append(self.predict(features))
        return results

    def save_model(self, path: str | Path) -> None:
        """Save trained model to disk.

        Args:
            path: Path to save model (supports .json, .xgb, .pkl).
        """
        path = Path(path)

        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted model")

        # Save model-specific format
        if self.use_xgboost:
            # Save XGBoost model
            self.model.save_model(str(path.with_suffix(".json")))
            # Also save feature names and metadata
            metadata = {
                "feature_names": self.feature_names,
                "emotions": self.emotions,
                "use_xgboost": True,
                "n_estimators": self.n_estimators,
            }
            with open(path.with_suffix(".metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)
        else:
            # Save sklearn model
            import joblib
            joblib.dump(self.model, path.with_suffix(".pkl"))
            metadata = {
                "feature_names": self.feature_names,
                "emotions": self.emotions,
                "use_xgboost": False,
                "n_estimators": self.n_estimators,
            }
            with open(path.with_suffix(".metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)

    def load_model(self, path: str | Path) -> None:
        """Load trained model from disk.

        Args:
            path: Path to load model from.
        """
        path = Path(path)

        # Load metadata
        metadata_path = path.with_suffix(".metadata.json")
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            self.feature_names = metadata.get("feature_names", [])
            self.emotions = metadata.get("emotions", Emotion.all_emotions())
            self.n_estimators = metadata.get("n_estimators", 100)
            self.use_xgboost = metadata.get("use_xgboost", HAS_XGBOOST)
        else:
            # Try to determine format from path
            self.use_xgboost = path.suffix == ".json"

        # Load model
        if self.use_xgboost and HAS_XGBOOST:
            self.model = xgb.XGBClassifier()
            self.model.load_model(str(path))
        else:
            import joblib
            self.model = joblib.load(str(path.with_suffix(".pkl")))

        self.is_fitted = True


# ── Synthetic Data Generation ───────────────────────────────────────────────


def generate_synthetic_training_data(n: int = 5000) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic training data for bootstrapping.

    Creates labeled samples based on rule patterns:
    - Rage clicks → frustration
    - High scroll reversals + idle → confusion
    - Long session + high entropy → delight
    - Low activity + dead clicks → boredom
    - High burst activity → anxiety
    - Smooth reading pauses → focus
    - High hover on CTA + low velocity → hesitation
    - Balanced engagement → satisfaction

    Args:
        n: Number of samples to generate.

    Returns:
        Tuple of (X, y) where X is (n, 28) and y is (n,) labels.
    """
    np.random.seed(42)

    # Initialize feature arrays
    X = np.zeros((n, 28))
    y = np.zeros(n, dtype=object)

    # Feature name mapping (must match BehavioralFeatureExtractor.FEATURE_NAMES)
    feature_names = [
        # Mouse features (8)
        "mouse_velocity_mean",
        "mouse_velocity_std",
        "mouse_velocity_max",
        "mouse_direction_changes_per_sec",
        "mouse_hover_duration_on_cta",
        "mouse_cursor_idle_ratio",
        "mouse_backtrack_ratio",
        "mouse_movement_total_distance",
        # Click features (4)
        "click_rage_click_count",
        "click_dead_click_count",
        "click_heatmap_entropy",
        "click_double_click_rate",
        # Scroll features (4)
        "scroll_depth_max",
        "scroll_reversal_count",
        "scroll_speed_variance",
        "scroll_reading_pause_count",
        # Dwell features (4)
        "dwell_total_session_duration",
        "dwell_active_engagement_ratio",
        "dwell_tab_switch_count",
        "dwell_form_abandon_count",
        # Combined features (8)
        "session_total_events",
        "session_events_per_second",
        "session_mouse_click_ratio",
        "session_scroll_click_ratio",
        "session_idle_periods",
        "session_burst_activity_count",
        "session_form_interaction_duration",
        "session_cta_click_count",
    ]

    # Generate samples for each emotion
    samples_per_emotion = n // 8

    for emotion_idx, emotion in enumerate(Emotion.all_emotions()):
        start_idx = emotion_idx * samples_per_emotion
        end_idx = start_idx + samples_per_emotion

        # Generate features based on emotion patterns
        for i in range(start_idx, end_idx):
            if emotion == Emotion.FRUSTRATION.value:
                # High rage clicks, high velocity, high backtrack
                X[i] = _generate_frustration_features()
            elif emotion == Emotion.CONFUSION.value:
                # High scroll reversals, high idle, low velocity
                X[i] = _generate_confusion_features()
            elif emotion == Emotion.DELIGHT.value:
                # Long session, high entropy, balanced metrics
                X[i] = _generate_delight_features()
            elif emotion == Emotion.BOREDOM.value:
                # Low velocity, high dead clicks, high idle
                X[i] = _generate_boredom_features()
            elif emotion == Emotion.ANXIETY.value:
                # High burst activity, high form abandonment
                X[i] = _generate_anxiety_features()
            elif emotion == Emotion.FOCUS.value:
                # Smooth movement, reading pauses, low rage clicks
                X[i] = _generate_focus_features()
            elif emotion == Emotion.HESITATION.value:
                # High hover on CTA, low velocity
                X[i] = _generate_hesitation_features()
            else:  # SATISFACTION
                # Balanced engagement, smooth movement
                X[i] = _generate_satisfaction_features()

            y[i] = emotion

    return X, y


# ── Synthetic Feature Generators ─────────────────────────────────────────


def _generate_frustration_features() -> np.ndarray:
    """Generate features for frustration emotion."""
    features = np.random.randn(28) * 0.1
    # High rage clicks (index 8)
    features[8] = np.random.randint(3, 8)
    # High velocity (indices 0-2)
    features[0:3] += np.random.uniform(50, 100, 3)
    # High backtrack (index 6)
    features[6] = np.random.uniform(0.4, 0.8)
    # Normalize
    return np.abs(features)


def _generate_confusion_features() -> np.ndarray:
    """Generate features for confusion emotion."""
    features = np.random.randn(28) * 0.1
    # High scroll reversals (index 12)
    features[12] = np.random.randint(5, 15)
    # High idle ratio (index 5)
    features[5] = np.random.uniform(0.6, 0.9)
    # Low velocity (indices 0-2)
    features[0:3] -= np.random.uniform(20, 40, 3)
    return np.abs(features)


def _generate_delight_features() -> np.ndarray:
    """Generate features for delight emotion."""
    features = np.random.randn(28) * 0.1
    # Long session (index 16)
    features[16] = np.random.uniform(200, 600)
    # High entropy (index 10)
    features[10] = np.random.uniform(0.7, 0.95)
    # Balanced metrics
    features[8] = np.random.uniform(0, 1)  # Low rage clicks
    return np.abs(features)


def _generate_boredom_features() -> np.ndarray:
    """Generate features for boredom emotion."""
    features = np.random.randn(28) * 0.1
    # Low velocity (indices 0-2)
    features[0:3] -= np.random.uniform(30, 60, 3)
    # High dead clicks (index 9)
    features[9] = np.random.randint(3, 10)
    # High idle ratio (index 5)
    features[5] = np.random.uniform(0.7, 0.95)
    # Low event rate (index 17)
    features[17] = np.random.uniform(0.1, 0.5)
    return np.abs(features)


def _generate_anxiety_features() -> np.ndarray:
    """Generate features for anxiety emotion."""
    features = np.random.randn(28) * 0.1
    # High burst activity (index 22)
    features[22] = np.random.randint(5, 15)
    # High form abandonment (index 19)
    features[19] = np.random.randint(2, 8)
    # High scroll variance (index 13)
    features[13] = np.random.uniform(50, 200)
    return np.abs(features)


def _generate_focus_features() -> np.ndarray:
    """Generate features for focus emotion."""
    features = np.random.randn(28) * 0.1
    # Smooth movement (low std, index 1)
    features[1] = np.random.uniform(5, 20)
    # Reading pauses (index 15)
    features[15] = np.random.randint(5, 12)
    # Low rage clicks (index 8)
    features[8] = np.random.uniform(0, 1)
    # High engagement ratio (index 17)
    features[17] = np.random.uniform(0.7, 0.95)
    return np.abs(features)


def _generate_hesitation_features() -> np.ndarray:
    """Generate features for hesitation emotion."""
    features = np.random.randn(28) * 0.1
    # High hover on CTA (index 4)
    features[4] = np.random.uniform(3000, 8000)
    # Low velocity (indices 0-2)
    features[0:3] -= np.random.uniform(20, 50, 3)
    # High direction changes (index 3)
    features[3] = np.random.uniform(2, 5)
    return np.abs(features)


def _generate_satisfaction_features() -> np.ndarray:
    """Generate features for satisfaction emotion."""
    features = np.random.randn(28) * 0.1
    # Balanced metrics
    features[0:28] = np.abs(features)
    # Moderate velocity (indices 0-2)
    features[0:3] = np.random.uniform(30, 70, 3)
    # Low double-click rate (index 11)
    features[11] = np.random.uniform(0, 0.1)
    # High engagement (index 17)
    features[17] = np.random.uniform(0.8, 0.95)
    # Low idle ratio (index 5)
    features[5] = np.random.uniform(0.1, 0.3)
    return features
