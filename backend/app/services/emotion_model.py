"""Emotion Model Service — ML inference for session emotion classification.

Loads the trained XGBoost model from ml/artifacts and predicts emotions
from the 8 behavioral features extracted by feature_worker.py.
"""

import logging
import pickle
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path("/app/ml_artifacts")

VALENCE_MAP = {
    'confusion': -0.3,
    'frustration': -0.7,
    'delight': 0.8,
    'anxiety': -0.5,
    'hesitation': -0.1,
    'focus': 0.3,
    'boredom': -0.2,
    'satisfaction': 0.7,
}

AROUSAL_MAP = {
    'confusion': 0.6,
    'frustration': 0.8,
    'delight': 0.7,
    'anxiety': 0.9,
    'hesitation': 0.4,
    'focus': 0.7,
    'boredom': 0.1,
    'satisfaction': 0.3,
}

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


class EmotionModel:
    _model = None
    _scaler = None
    _encoder = None
    _loaded = False
    _load_attempted = False

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
            logger.info("Emotion model loaded successfully")
            return True
        except FileNotFoundError as e:
            logger.warning(f"Emotion model artifacts not found: {e}")
            return False
        except Exception as e:
            logger.warning(f"Emotion model loading failed: {e}")
            return False

    @classmethod
    def predict(cls, features: dict) -> dict | None:
        """Predict emotion from behavioral features.

        Args:
            features: Dict with the 8 feature names as keys

        Returns:
            Dict with primary_emotion, confidence, all_scores, valence, arousal
            or None if model is not available
        """
        if not cls.load():
            return None

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
            }
        except Exception as e:
            logger.error(f"Emotion prediction failed: {e}")
            return None

    @classmethod
    def is_available(cls) -> bool:
        """Check if the emotion model is loaded and available."""
        return cls.load() and cls._model is not None
