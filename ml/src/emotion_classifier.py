"""Emotion classifier for behavioral signals.

Classifies 4 scientifically-grounded emotions (frustrated, confused, engaged, disengaged)
from extracted behavioral features.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

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
    """4 emotion categories for classification.

    These emotions are scientifically distinguishable from mouse behavior alone:
    - FRUSTRATED: High rage clicks, high velocity variance, erratic movement
    - CONFUSED: High scroll retreats, direction changes, hesitation
    - ENGAGED: Steady interaction, good session duration, CTA clicks
    - DISENGAGED: Very short sessions, low event count, high idle ratio
    """

    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    ENGAGED = "engaged"
    DISENGAGED = "disengaged"

    @classmethod
    def all_emotions(cls) -> list[str]:
        """Get list of all emotion strings."""
        return [e.value for e in cls]


# ── Valence-Arousal Mapping ────────────────────────────────────────────

# Hardcoded valence (-1 to 1) and arousal (0 to 1) for each emotion
VALENCE_AROUSAL = {
    Emotion.FRUSTRATED: (-0.7, 0.8),   # Negative valence, high arousal (agitated)
    Emotion.CONFUSED: (-0.3, 0.6),     # Slightly negative valence, medium-high arousal (uncertain)
    Emotion.ENGAGED: (0.7, 0.5),       # Positive valence, medium arousal (focused)
    Emotion.DISENGAGED: (-0.4, 0.1),   # Negative valence, low arousal (withdrawn)
}


# Rule-based overrides removed — using pure ML predictions
# The classifier now relies entirely on the trained XGBoost/sklearn model
# without any heuristic adjustments. Model should be trained on
# representative data to capture these patterns directly.


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
                num_class=4,
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
            confusion_matrix,
            f1_score,
            precision_score,
            recall_score,
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

        # Get prediction probabilities from pure ML model
        if self.use_xgboost:
            probs = self.model.predict_proba(features.reshape(1, -1))[0]
        else:
            probs = self.model.predict_proba(features.reshape(1, -1))[0]

        # Create score dict directly from model probabilities
        scores = {emotion: probs[i] for i, emotion in enumerate(self.emotions)}

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
            rule_adjustments=None,
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
            with open(metadata_path) as f:
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
    - Frustrated: High rage clicks, high velocity variance, high hesitation
    - Confused: High scroll retreat count, medium hesitation, many direction changes
    - Engaged: Steady velocity, good session duration, low rage clicks, CTA clicks present
    - Disengaged: Very short sessions, low event count, high idle ratio, minimal interaction

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

    # Generate samples for each emotion (4 emotions)
    samples_per_emotion = n // 4

    for emotion_idx, emotion in enumerate(Emotion.all_emotions()):
        start_idx = emotion_idx * samples_per_emotion
        end_idx = start_idx + samples_per_emotion

        # Generate features based on emotion patterns
        for i in range(start_idx, end_idx):
            if emotion == Emotion.FRUSTRATED.value:
                # High rage clicks, high velocity variance, high hesitation
                X[i] = _generate_frustrated_features()
            elif emotion == Emotion.CONFUSED.value:
                # High scroll reversals, medium hesitation, many direction changes
                X[i] = _generate_confused_features()
            elif emotion == Emotion.ENGAGED.value:
                # Steady velocity, good session duration, low rage clicks, CTA clicks
                X[i] = _generate_engaged_features()
            else:  # DISENGAGED
                # Very short sessions, low event count, high idle ratio
                X[i] = _generate_disengaged_features()

            y[i] = emotion

    return X, y


# ── Synthetic Feature Generators ─────────────────────────────────────────


def _generate_frustrated_features() -> np.ndarray:
    """Generate features for frustrated emotion."""
    features = np.random.randn(28) * 0.1
    # High rage clicks (index 8)
    features[8] = np.random.randint(3, 8)
    # High velocity variance (index 1)
    features[1] += np.random.uniform(50, 100)
    # High backtrack ratio (index 6)
    features[6] = np.random.uniform(0.4, 0.8)
    # Short to medium session (index 16)
    features[16] = np.random.uniform(10, 120)
    # Normalize
    return np.abs(features)


def _generate_confused_features() -> np.ndarray:
    """Generate features for confused emotion."""
    features = np.random.randn(28) * 0.1
    # High scroll reversals (index 12)
    features[12] = np.random.randint(5, 15)
    # High direction changes (index 3)
    features[3] = np.random.uniform(2, 5)
    # Medium idle ratio (index 5)
    features[5] = np.random.uniform(0.4, 0.7)
    # Low to medium velocity (indices 0-2)
    features[0:3] -= np.random.uniform(10, 30, 3)
    return np.abs(features)


def _generate_engaged_features() -> np.ndarray:
    """Generate features for engaged emotion."""
    features = np.random.randn(28) * 0.1
    # Steady velocity (low std, index 1)
    features[1] = np.random.uniform(10, 40)
    # Long session (index 16)
    features[16] = np.random.uniform(100, 600)
    # Low rage clicks (index 8)
    features[8] = np.random.uniform(0, 1)
    # CTA clicks present (index 27)
    features[27] = np.random.randint(1, 5)
    # High engagement ratio (index 17)
    features[17] = np.random.uniform(0.7, 0.95)
    # Low idle ratio (index 5)
    features[5] = np.random.uniform(0.1, 0.4)
    return np.abs(features)


def _generate_disengaged_features() -> np.ndarray:
    """Generate features for disengaged emotion."""
    features = np.random.randn(28) * 0.1
    # Very short session (index 16)
    features[16] = np.random.uniform(1, 15)
    # Low event count (index 17)
    features[17] = np.random.uniform(0.05, 0.3)
    # High idle ratio (index 5)
    features[5] = np.random.uniform(0.7, 0.95)
    # Low velocity overall (indices 0-2)
    features[0:3] -= np.random.uniform(20, 50, 3)
    # Few interactions
    features[8] = np.random.uniform(0, 1)  # Low rage clicks
    features[27] = 0  # No CTA clicks
    return np.abs(features)
