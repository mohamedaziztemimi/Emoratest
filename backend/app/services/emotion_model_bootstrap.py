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
    Adds 20-25% noise/overlap between profiles to prevent overconfidence.
    """
    np.random.seed(42)

    X = np.zeros((n, len(FEATURE_NAMES)))
    y = np.zeros(n, dtype=object)

    samples_per_emotion = n // 4

    for emotion_idx, emotion in enumerate(EMOTIONS):
        start_idx = emotion_idx * samples_per_emotion
        end_idx = start_idx + samples_per_emotion

        # Base profiles - with intentional overlap
        for i in range(start_idx, end_idx):
            # Add 25% noise: 1 in 4 samples gets "confused" features from another emotion
            noise_sample = np.random.random() < 0.25

            if emotion == 'frustrated':
                if noise_sample:
                    # 25% chance: looks more like confused or engaged (overlap)
                    overlap_type = np.random.choice(['confused_overlap', 'engaged_overlap'])
                    if overlap_type == 'confused_overlap':
                        # High hesitation but moderate rage (confused-like)
                        X[i] = [
                            np.random.uniform(0.5, 0.8),   # hesitation_score
                            np.random.uniform(1, 6),       # price_dwell_time_s
                            np.random.uniform(0.15, 0.5),  # rage_click_score (moderate - overlap)
                            np.random.uniform(2, 6),       # scroll_retreat_count (overlap)
                            np.random.uniform(0, 2),       # exit_intent_count
                            np.random.uniform(2, 15),      # checkout_hesitation_s
                            np.random.uniform(8000, 50000), # velocity_variance (overlap)
                            np.random.uniform(45, 300),    # session_duration_s
                        ]
                    else:  # engaged_overlap
                        # Longer duration but still frustrated
                        X[i] = [
                            np.random.uniform(0.3, 0.7),   # hesitation_score (lower overlap)
                            np.random.uniform(5, 15),      # price_dwell_time_s (engaged-like)
                            np.random.uniform(0.2, 0.6),   # rage_click_score
                            np.random.uniform(0, 3),       # scroll_retreat_count
                            np.random.uniform(0, 2),       # exit_intent_count
                            np.random.uniform(0, 8),       # checkout_hesitation_s
                            np.random.uniform(5000, 30000), # velocity_variance (overlap)
                            np.random.uniform(120, 480),   # session_duration_s (engaged-like)
                        ]
                else:
                    # Classic frustrated: high rage, high velocity, high hesitation
                    X[i] = [
                        np.random.uniform(0.45, 0.9),  # hesitation_score (high, with lower overlap)
                        np.random.uniform(0, 6),       # price_dwell_time_s (overlap range)
                        np.random.uniform(0.25, 0.85),  # rage_click_score (high)
                        np.random.uniform(0, 4),       # scroll_retreat_count (overlap)
                        np.random.uniform(0, 2),       # exit_intent_count
                        np.random.uniform(0, 12),      # checkout_hesitation_s
                        np.random.uniform(8000, 80000), # velocity_variance (high)
                        np.random.uniform(45, 480),    # session_duration_s (overlap)
                    ]

            elif emotion == 'confused':
                if noise_sample:
                    # 25% chance: looks like frustrated or disengaged
                    overlap_type = np.random.choice(['frustrated_overlap', 'disengaged_overlap'])
                    if overlap_type == 'frustrated_overlap':
                        # Higher rage, less scroll retreat
                        X[i] = [
                            np.random.uniform(0.4, 0.75),  # hesitation_score
                            np.random.uniform(1, 5),       # price_dwell_time_s
                            np.random.uniform(0.2, 0.55),  # rage_click_score (frustrated-like)
                            np.random.uniform(1, 5),       # scroll_retreat_count (lower)
                            np.random.uniform(0, 3),       # exit_intent_count
                            np.random.uniform(3, 20),      # checkout_hesitation_s
                            np.random.uniform(3000, 45000), # velocity_variance (overlap)
                            np.random.uniform(25, 240),    # session_duration_s
                        ]
                    else:  # disengaged_overlap
                        # Lower activity but still confused
                        X[i] = [
                            np.random.uniform(0.25, 0.65), # hesitation_score (lower)
                            np.random.uniform(0, 4),       # price_dwell_time_s
                            np.random.uniform(0, 0.25),    # rage_click_score (low)
                            np.random.uniform(2, 6),       # scroll_retreat_count
                            np.random.uniform(0, 2),       # exit_intent_count
                            np.random.uniform(2, 15),      # checkout_hesitation_s
                            np.random.uniform(500, 15000), # velocity_variance (disengaged-like)
                            np.random.uniform(15, 120),    # session_duration_s (shorter)
                        ]
                else:
                    # Classic confused: high scroll retreats, moderate hesitation
                    X[i] = [
                        np.random.uniform(0.35, 0.8),  # hesitation_score (with overlap)
                        np.random.uniform(0, 6),       # price_dwell_time_s (overlap)
                        np.random.uniform(0, 0.4),     # rage_click_score (low-moderate)
                        np.random.uniform(3, 10),      # scroll_retreat_count (high)
                        np.random.uniform(1, 5),       # exit_intent_count
                        np.random.uniform(5, 35),      # checkout_hesitation_s
                        np.random.uniform(1000, 30000), # velocity_variance (with overlap)
                        np.random.uniform(25, 320),    # session_duration_s (overlap)
                    ]

            elif emotion == 'engaged':
                if noise_sample:
                    # 25% chance: looks like confused or has shorter duration
                    overlap_type = np.random.choice(['confused_overlap', 'shorter_engaged'])
                    if overlap_type == 'confused_overlap':
                        # More hesitation, some scroll retreats
                        X[i] = [
                            np.random.uniform(0.15, 0.5), # hesitation_score (higher overlap)
                            np.random.uniform(4, 20),     # price_dwell_time_s
                            np.random.uniform(0.05, 0.3), # rage_click_score (slightly higher)
                            np.random.uniform(1, 5),      # scroll_retreat_count (overlap)
                            np.random.uniform(0, 2),      # exit_intent_count
                            np.random.uniform(1, 10),     # checkout_hesitation_s
                            np.random.uniform(2500, 28000), # velocity_variance
                            np.random.uniform(80, 480),   # session_duration_s
                        ]
                    else:  # shorter_engaged
                        # Shorter but still engaged
                        X[i] = [
                            np.random.uniform(0.05, 0.35), # hesitation_score
                            np.random.uniform(3, 15),      # price_dwell_time_s
                            np.random.uniform(0, 0.2),     # rage_click_score
                            np.random.uniform(0, 4),       # scroll_retreat_count
                            np.random.uniform(0, 2),       # exit_intent_count
                            np.random.uniform(0, 8),       # checkout_hesitation_s
                            np.random.uniform(2000, 25000), # velocity_variance
                            np.random.uniform(50, 200),    # session_duration_s (shorter - overlap)
                        ]
                else:
                    # Classic engaged: low hesitation, low rage, long duration
                    X[i] = [
                        np.random.uniform(0, 0.35),    # hesitation_score (low, with overlap)
                        np.random.uniform(4, 28),      # price_dwell_time_s (overlap)
                        np.random.uniform(0, 0.2),     # rage_click_score (low)
                        np.random.uniform(0, 4),       # scroll_retreat_count (overlap)
                        np.random.uniform(0, 2),       # exit_intent_count
                        np.random.uniform(0, 8),       # checkout_hesitation_s
                        np.random.uniform(2500, 38000), # velocity_variance (with overlap)
                        np.random.uniform(70, 900),    # session_duration_s (wide range)
                    ]

            else:  # disengaged
                if noise_sample:
                    # 25% chance: looks like confused or has slightly more activity
                    overlap_type = np.random.choice(['confused_overlap', 'mild_activity'])
                    if overlap_type == 'confused_overlap':
                        # More like confused but still short
                        X[i] = [
                            np.random.uniform(0.1, 0.4),  # hesitation_score (higher)
                            np.random.uniform(1, 5),      # price_dwell_time_s
                            np.random.uniform(0, 0.25),   # rage_click_score
                            np.random.uniform(1, 4),      # scroll_retreat_count (overlap)
                            np.random.uniform(0, 2),      # exit_intent_count
                            np.random.uniform(0, 5),      # checkout_hesitation_s
                            np.random.uniform(800, 12000), # velocity_variance (overlap)
                            np.random.uniform(8, 80),     # session_duration_s (overlap)
                        ]
                    else:  # mild_activity
                        # Slightly more activity but still disengaged
                        X[i] = [
                            np.random.uniform(0.05, 0.35), # hesitation_score
                            np.random.uniform(1, 6),       # price_dwell_time_s (more)
                            np.random.uniform(0, 0.25),    # rage_click_score
                            np.random.uniform(0, 3),       # scroll_retreat_count
                            np.random.uniform(0, 2),       # exit_intent_count
                            np.random.uniform(0, 4),       # checkout_hesitation_s
                            np.random.uniform(600, 8000),  # velocity_variance (higher)
                            np.random.uniform(5, 90),      # session_duration_s (overlap)
                        ]
                else:
                    # Classic disengaged: very short, low activity
                    X[i] = [
                        np.random.uniform(0, 0.3),     # hesitation_score (with overlap)
                        np.random.uniform(0, 5),       # price_dwell_time_s (overlap)
                        np.random.uniform(0, 0.25),    # rage_click_score (with overlap)
                        np.random.uniform(0, 3),       # scroll_retreat_count (overlap)
                        np.random.uniform(0, 2),       # exit_intent_count
                        np.random.uniform(0, 3),       # checkout_hesitation_s
                        np.random.uniform(400, 7000),  # velocity_variance (with overlap)
                        np.random.uniform(4, 75),      # session_duration_s (with overlap)
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
