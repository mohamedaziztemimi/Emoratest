"""ML module for EmoraTest emotion classification.

Exports:
- BehavioralFeatureExtractor: Extract 28 features from event streams
- EmotionClassifier: Classify 8 emotions from features
- Emotion: Emotion enum with 8 categories
- generate_synthetic_training_data: Bootstrap training data
"""

from ml.src.emotion_classifier import (
    VALENCE_AROUSAL,
    Emotion,
    EmotionClassifier,
    EmotionResult,
    generate_synthetic_training_data,
)
from ml.src.feature_extractor import (
    BehavioralFeatureExtractor,
    Event,
)

__all__ = [
    "BehavioralFeatureExtractor",
    "Event",
    "Emotion",
    "EmotionClassifier",
    "EmotionResult",
    "VALENCE_AROUSAL",
    "generate_synthetic_training_data",
]
