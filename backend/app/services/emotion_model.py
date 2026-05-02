"""Emotion Model Service — ML inference for session emotion classification.

Loads the trained XGBoost model from ml/artifacts and predicts emotions
from the 8 behavioral features extracted by feature_worker.py.

Falls back to heuristic-based emotion prediction when models are unavailable.
"""

import logging
import pickle
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path("/app/ml_artifacts")

VALENCE_MAP = {
    'frustrated': -0.7,
    'confused': -0.3,
    'engaged': 0.7,
    'disengaged': -0.4,
}

AROUSAL_MAP = {
    'frustrated': 0.8,
    'confused': 0.6,
    'engaged': 0.5,
    'disengaged': 0.1,
}

# All emotions for consistent ordering
ALL_EMOTIONS = ['frustrated', 'confused', 'engaged', 'disengaged']

FEATURE_NAMES = [
    'hesitation_score',
    'price_dwell_time_s',
    'rage_click_score',
    'scroll_retreat_count',
    'exit_intent_count',
    'checkout_hesitation_s',
    'velocity_variance',
    'session_duration_s',
]


def _heuristic_emotion_predict(features: dict) -> dict:
    """Fallback heuristic emotion prediction when ML model is unavailable.

    Uses behavioral signals to predict 4 emotions based on domain rules:
    - frustrated: High rage clicks, high velocity variance, high hesitation
    - confused: High scroll retreats, direction changes, scroll reversals
    - engaged: Steady velocity, good session duration, low rage clicks, CTA clicks
    - disengaged: Very short sessions, low event count, high idle ratio

    Args:
        features: Dict with the 8 feature names as keys

    Returns:
        Dict with primary_emotion, confidence, all_scores, valence, arousal
    """
    f = features

    # Initialize all emotion scores to baseline
    scores = {emotion: 0.1 for emotion in ALL_EMOTIONS}

    rage_score = float(f.get('rage_click_score', 0))
    retreat_count = float(f.get('scroll_retreat_count', 0))
    exit_count = float(f.get('exit_intent_count', 0))
    duration = float(f.get('session_duration_s', 0))
    hesitation = float(f.get('hesitation_score', 0))
    velocity_var = float(f.get('velocity_variance', 0))
    checkout_hesitation = float(f.get('checkout_hesitation_s', 0))
    price_dwell = float(f.get('price_dwell_time_s', 0))

    # FRUSTRATED signals: High rage clicks, high velocity variance, high hesitation
    if rage_score > 0.3:
        scores['frustrated'] += min(rage_score * 1.5, 0.6)
    if velocity_var > 500000:
        scores['frustrated'] += 0.3
    if hesitation > 0.6:
        scores['frustrated'] += 0.2

    # CONFUSED signals: High scroll retreats, direction changes
    if retreat_count > 3:
        scores['confused'] += min(retreat_count * 0.1, 0.5)
    if velocity_var > 200000 and velocity_var < 500000:
        scores['confused'] += 0.2

    # ENGAGED signals: Steady interaction, good duration, low rage clicks
    if duration > 30 and rage_score < 0.2:
        scores['engaged'] += 0.4
    if rage_score < 0.1 and retreat_count < 2 and exit_count < 1:
        scores['engaged'] += 0.3
    if price_dwell > 3 and rage_score < 0.2:
        scores['engaged'] += 0.2

    # DISENGAGED signals: Very short sessions, low event count, high idle ratio
    if duration < 10:
        scores['disengaged'] += 0.4
    if duration < 10 and rage_score < 0.1:
        scores['disengaged'] += 0.3

    # Normalize
    total = sum(scores.values())
    if total > 0:
        scores = {k: round(v / total, 4) for k, v in scores.items()}

    primary_emotion = max(scores, key=scores.get)
    confidence = scores[primary_emotion]

    return {
        'primary_emotion': primary_emotion,
        'confidence': confidence,
        'all_scores': scores,
        'valence': VALENCE_MAP.get(primary_emotion, 0.0),
        'arousal': AROUSAL_MAP.get(primary_emotion, 0.5),
        '_fallback': True,
    }


class EmotionModel:
    _model = None
    _scaler = None
    _encoder = None
    _loaded = False
    _load_attempted = False
    _using_fallback = False
    ARTIFACTS_DIR = ARTIFACTS_DIR

    @classmethod
    def load(cls) -> bool:
        """Load the emotion model artifacts from disk.

        Returns True if loading succeeded, False otherwise.
        Only attempts loading once — subsequent calls return cached result.
        """
        if cls._load_attempted:
            return cls._model is not None

        cls._load_attempted = True
        cls._loaded = True

        try:
            with open(ARTIFACTS_DIR / "emotion_v1.pkl", "rb") as f:
                cls._model = pickle.load(f)
            with open(ARTIFACTS_DIR / "emotion_v1_scaler.pkl", "rb") as f:
                cls._scaler = pickle.load(f)
            with open(ARTIFACTS_DIR / "emotion_v1_encoder.pkl", "rb") as f:
                cls._encoder = pickle.load(f)
            logger.info("Emotion model loaded successfully from %s", ARTIFACTS_DIR)
            cls._using_fallback = False
            return True
        except FileNotFoundError as e:
            logger.critical("ML MODEL NOT FOUND at %s — falling back to heuristic predictions! Please ensure ml/artifacts is copied into the Docker image.", ARTIFACTS_DIR)
            logger.critical("Heuristic predictions are LESS ACCURATE than the trained XGBoost model.")
            cls._using_fallback = True
            return False
        except Exception as e:
            logger.critical("ML MODEL loading failed: %s — falling back to heuristic predictions!", e)
            cls._using_fallback = True
            return False

    @classmethod
    def predict(cls, features: dict) -> dict | None:
        """Predict emotion from behavioral features.

        Args:
            features: Dict with the 8 feature names as keys

        Returns:
            Dict with primary_emotion, confidence, all_scores, valence, arousal
            Uses heuristic fallback if ML model is unavailable
        """
        # Try ML model first
        if cls.load() and cls._model is not None:
            try:
                X = np.array([[
                    float(features.get(f, 0))
                    for f in FEATURE_NAMES
                ]])
                X_scaled = cls._scaler.transform(X)
                proba = cls._model.predict_proba(X_scaled)[0]
                pred_idx = int(proba.argmax())
                primary = cls._encoder.inverse_transform([pred_idx])[0]
                confidence = float(proba[pred_idx])
                all_scores = {
                    cls._encoder.inverse_transform([i])[0]: float(p)
                    for i, p in enumerate(proba)
                }
                return {
                    'primary_emotion': primary,
                    'confidence': confidence,
                    'all_scores': all_scores,
                    'valence': VALENCE_MAP.get(primary, 0.0),
                    'arousal': AROUSAL_MAP.get(primary, 0.5),
                    '_fallback': False,
                }
            except Exception as e:
                logger.error(f"Emotion prediction failed: {e}. Falling back to heuristic.")

        # Use heuristic fallback
        logger.warning("Using heuristic fallback for emotion prediction — ML model not available. Results are less accurate.")
        return _heuristic_emotion_predict(features)

    @classmethod
    def is_available(cls) -> bool:
        """Check if the emotion model is loaded and available."""
        return cls._load_attempted and cls._model is not None

    @classmethod
    def using_fallback(cls) -> bool:
        """Check if we're using heuristic fallback instead of ML model."""
        cls.load()  # Ensure we've attempted loading
        return cls._using_fallback
