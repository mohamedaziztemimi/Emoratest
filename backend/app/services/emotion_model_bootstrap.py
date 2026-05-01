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

# Emotion labels
EMOTIONS = [
    'confusion',
    'frustration',
    'delight',
    'boredom',
    'anxiety',
    'focus',
    'hesitation',
    'satisfaction',
]

# Valence and arousal mappings
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


def generate_synthetic_features(n: int = 2000) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic training data for the 8 behavioral features.

    Simplified version that matches the feature_worker.py feature names.
    """
    np.random.seed(42)

    X = np.zeros((n, len(FEATURE_NAMES)))
    y = np.zeros(n, dtype=object)

    samples_per_emotion = n // 8

    for emotion_idx, emotion in enumerate(EMOTIONS):
        start_idx = emotion_idx * samples_per_emotion
        end_idx = start_idx + samples_per_emotion

        for i in range(start_idx, end_idx):
            if emotion == 'frustration':
                # High rage clicks, high velocity variance
                X[i] = [
                    np.random.uniform(0.5, 0.9),   # hesitation_score (0-1 scale, high for frustration)
                    np.random.uniform(0, 5),       # price_dwell_time_s
                    np.random.uniform(0.3, 0.8),   # rage_click_score
                    np.random.uniform(0, 2),       # scroll_retreat_count
                    np.random.uniform(0, 1),       # exit_intent_count
                    np.random.uniform(0, 10),      # checkout_hesitation_s
                    np.random.uniform(10000, 80000), # velocity_variance
                    np.random.uniform(60, 600),    # session_duration_s
                ]
            elif emotion == 'confusion':
                # High scroll retreats, low velocity
                X[i] = [
                    np.random.uniform(0.4, 0.8),   # hesitation_score
                    np.random.uniform(0, 5),       # price_dwell_time_s
                    np.random.uniform(0, 0.3),     # rage_click_score
                    np.random.uniform(3, 10),      # scroll_retreat_count (high)
                    np.random.uniform(1, 4),       # exit_intent_count
                    np.random.uniform(5, 30),      # checkout_hesitation_s
                    np.random.uniform(1000, 20000), # velocity_variance
                    np.random.uniform(30, 300),    # session_duration_s
                ]
            elif emotion == 'delight':
                # Balanced, long session
                X[i] = [
                    np.random.uniform(0, 0.3),     # hesitation_score (low)
                    np.random.uniform(5, 20),      # price_dwell_time_s (engaged)
                    np.random.uniform(0, 0.2),     # rage_click_score (low)
                    np.random.uniform(0, 3),       # scroll_retreat_count (low)
                    np.random.uniform(0, 1),       # exit_intent_count (low)
                    np.random.uniform(0, 5),       # checkout_hesitation_s (low)
                    np.random.uniform(2000, 30000), # velocity_variance (moderate)
                    np.random.uniform(180, 900),   # session_duration_s (long)
                ]
            elif emotion == 'boredom':
                # Low activity, low velocity
                X[i] = [
                    np.random.uniform(0, 0.2),     # hesitation_score
                    np.random.uniform(0, 3),       # price_dwell_time_s
                    np.random.uniform(0, 0.2),     # rage_click_score
                    np.random.uniform(0, 2),       # scroll_retreat_count
                    np.random.uniform(0, 1),       # exit_intent_count
                    np.random.uniform(0, 2),       # checkout_hesitation_s
                    np.random.uniform(500, 5000),  # velocity_variance (low)
                    np.random.uniform(10, 60),     # session_duration_s (short)
                ]
            elif emotion == 'anxiety':
                # High hesitation, high exit intent
                X[i] = [
                    np.random.uniform(0.5, 0.9),   # hesitation_score (high)
                    np.random.uniform(0, 10),      # price_dwell_time_s
                    np.random.uniform(0.1, 0.5),   # rage_click_score
                    np.random.uniform(2, 8),       # scroll_retreat_count
                    np.random.uniform(2, 6),       # exit_intent_count (high)
                    np.random.uniform(15, 60),     # checkout_hesitation_s (high)
                    np.random.uniform(5000, 50000), # velocity_variance
                    np.random.uniform(60, 300),    # session_duration_s
                ]
            elif emotion == 'focus':
                # Smooth movement, low hesitation
                X[i] = [
                    np.random.uniform(0, 0.2),     # hesitation_score (low)
                    np.random.uniform(5, 25),      # price_dwell_time_s (reading)
                    np.random.uniform(0, 0.1),     # rage_click_score (very low)
                    np.random.uniform(0, 2),       # scroll_retreat_count (low)
                    np.random.uniform(0, 1),       # exit_intent_count (low)
                    np.random.uniform(0, 3),       # checkout_hesitation_s
                    np.random.uniform(3000, 25000), # velocity_variance (smooth)
                    np.random.uniform(120, 600),   # session_duration_s
                ]
            elif emotion == 'hesitation':
                # High hesitation, moderate velocity
                X[i] = [
                    np.random.uniform(0.6, 0.95),  # hesitation_score (very high)
                    np.random.uniform(3, 15),      # price_dwell_time_s
                    np.random.uniform(0, 0.3),     # rage_click_score
                    np.random.uniform(1, 5),       # scroll_retreat_count
                    np.random.uniform(1, 3),       # exit_intent_count
                    np.random.uniform(10, 45),     # checkout_hesitation_s
                    np.random.uniform(2000, 40000), # velocity_variance
                    np.random.uniform(60, 240),    # session_duration_s
                ]
            else:  # satisfaction
                # Balanced everything
                X[i] = [
                    np.random.uniform(0, 0.3),     # hesitation_score (low)
                    np.random.uniform(3, 15),      # price_dwell_time_s
                    np.random.uniform(0, 0.15),    # rage_click_score (low)
                    np.random.uniform(0, 3),       # scroll_retreat_count
                    np.random.uniform(0, 2),       # exit_intent_count (low)
                    np.random.uniform(0, 8),       # checkout_hesitation_s
                    np.random.uniform(5000, 35000), # velocity_variance
                    np.random.uniform(90, 600),    # session_duration_s
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
                num_class=8,
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
