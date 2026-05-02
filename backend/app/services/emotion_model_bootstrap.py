"""Emotion Model Bootstrap — trains model on startup if artifacts don't exist.

This ensures the emotion ML pipeline works immediately without requiring
manual model training. Uses synthetic data generation for bootstrapping.
"""
import logging
import pickle
from pathlib import Path

import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    from sklearn.ensemble import GradientBoostingClassifier

from app.services.emotion_model import EmotionModel, FEATURE_NAMES

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path("/app/ml_artifacts")

# Emotion labels - 4 emotion system (consolidated from 8)
EMOTIONS = [
    'frustrated',   # negative, high arousal
    'confused',     # negative, medium arousal
    'engaged',      # positive, medium arousal
    'disengaged',   # negative, low arousal
]

# Valence and arousal mappings - must match emotion_model.py
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


def generate_synthetic_features(n: int = 2000) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic training data for the 8 behavioral features.

    Uses the 4-emotion system: frustrated, confused, engaged, disengaged.
    """
    np.random.seed(42)

    X = np.zeros((n, len(FEATURE_NAMES)))
    y = np.zeros(n, dtype=object)

    samples_per_emotion = n // 4

    for emotion_idx, emotion in enumerate(EMOTIONS):
        start_idx = emotion_idx * samples_per_emotion
        end_idx = start_idx + samples_per_emotion

        for i in range(start_idx, end_idx):
            if emotion == 'frustrated':
                # High rage clicks, high velocity variance, high hesitation
                X[i] = [
                    np.random.uniform(0.5, 0.9),   # hesitation_score (high)
                    np.random.uniform(0, 5),       # price_dwell_time_s
                    np.random.uniform(0.3, 0.8),   # rage_click_score (high)
                    np.random.uniform(0, 2),       # scroll_retreat_count
                    np.random.uniform(0, 1),       # exit_intent_count
                    np.random.uniform(0, 10),      # checkout_hesitation_s
                    np.random.uniform(10000, 80000), # velocity_variance (high)
                    np.random.uniform(60, 600),    # session_duration_s
                ]
            elif emotion == 'confused':
                # High scroll retreats, moderate hesitation, low rage
                X[i] = [
                    np.random.uniform(0.4, 0.8),   # hesitation_score (moderate-high)
                    np.random.uniform(0, 5),       # price_dwell_time_s
                    np.random.uniform(0, 0.3),     # rage_click_score (low)
                    np.random.uniform(3, 10),      # scroll_retreat_count (high)
                    np.random.uniform(1, 4),       # exit_intent_count
                    np.random.uniform(5, 30),      # checkout_hesitation_s
                    np.random.uniform(1000, 20000), # velocity_variance (low-moderate)
                    np.random.uniform(30, 300),    # session_duration_s
                ]
            elif emotion == 'engaged':
                # Low hesitation, low rage, good duration, smooth velocity
                X[i] = [
                    np.random.uniform(0, 0.3),     # hesitation_score (low)
                    np.random.uniform(5, 25),      # price_dwell_time_s (reading)
                    np.random.uniform(0, 0.15),    # rage_click_score (very low)
                    np.random.uniform(0, 3),       # scroll_retreat_count (low)
                    np.random.uniform(0, 1),       # exit_intent_count (low)
                    np.random.uniform(0, 5),       # checkout_hesitation_s (low)
                    np.random.uniform(3000, 35000), # velocity_variance (smooth)
                    np.random.uniform(120, 900),   # session_duration_s (long)
                ]
            else:  # disengaged
                # Very short sessions, low activity, low velocity
                X[i] = [
                    np.random.uniform(0, 0.2),     # hesitation_score (low)
                    np.random.uniform(0, 3),       # price_dwell_time_s
                    np.random.uniform(0, 0.2),     # rage_click_score (low)
                    np.random.uniform(0, 2),       # scroll_retreat_count (low)
                    np.random.uniform(0, 1),       # exit_intent_count (low)
                    np.random.uniform(0, 2),       # checkout_hesitation_s (low)
                    np.random.uniform(500, 5000),  # velocity_variance (very low)
                    np.random.uniform(5, 60),      # session_duration_s (very short)
                ]

            y[i] = emotion

    return X, y


def bootstrap_emotion_model() -> bool:
    """Train and save emotion model if artifacts don't exist.

    Returns True if model is available (either loaded or newly trained).
    """
    # Check if model already exists
    model_path = ARTIFACTS_DIR / "emotion_v1.pkl"
    if model_path.exists():
        logger.info("Emotion model artifacts already exist")
        return True

    # Create artifacts directory
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Bootstrapping emotion model with synthetic training data...")

    try:
        # Generate training data
        X, y = generate_synthetic_features(n=2000)

        # Encode labels
        encoder = LabelEncoder()
        y_encoded = encoder.fit_transform(y)

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Train model
        if HAS_XGBOOST:
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                objective='multi:softprob',
                num_class=4,
                random_state=42,
                eval_metric='mlogloss',
            )
            model.fit(X_scaled, y_encoded, verbose=False)
        else:
            model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
            )
            model.fit(X_scaled, y_encoded)

        # Save model artifacts
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)

        with open(ARTIFACTS_DIR / "emotion_v1_scaler.pkl", 'wb') as f:
            pickle.dump(scaler, f)

        with open(ARTIFACTS_DIR / "emotion_v1_encoder.pkl", 'wb') as f:
            pickle.dump(encoder, f)

        logger.info(f"Emotion model bootstrap complete. Artifacts saved to {ARTIFACTS_DIR}")

        # Verify the model works
        EmotionModel._load_attempted = False  # Reset flag
        EmotionModel._loaded = False
        result = EmotionModel.predict({
            'hesitation_score': 0.5,
            'price_dwell_time_s': 5.0,
            'rage_click_score': 0.2,
            'scroll_retreat_count': 2,
            'exit_intent_count': 1,
            'checkout_hesitation_s': 10.0,
            'velocity_variance': 15000,
            'session_duration_s': 120,
        })

        if result:
            logger.info(f"Model verification successful: {result['primary_emotion']}")
        else:
            logger.warning("Model verification returned None")

        return True

    except Exception as e:
        logger.error(f"Emotion model bootstrap failed: {e}")
        return False


# ── FastAPI startup event ────────────────────────────────────────────────

def on_startup():
    """FastAPI startup handler to bootstrap emotion model."""
    bootstrap_emotion_model()
