"""Unit tests for Emotion ML pipeline.

Covers: feature extraction from sample events,
prediction output shape, valence range validation,
and synthetic data generation.
"""

from __future__ import annotations

import numpy as np
import pytest
from ml.src.emotion_classifier import (
    VALENCE_AROUSAL,
    Emotion,
    EmotionClassifier,
    EmotionResult,
    generate_synthetic_training_data,
)
from ml.src.feature_extractor import BehavioralFeatureExtractor, Event

# ── Sample Event Generators ────────────────────────────────────────────────


def make_mouse_events(n: int = 50) -> list[Event]:
    """Generate sample mouse move events."""
    events = []
    for i in range(n):
        events.append(Event(
            type="mouse_move",
            x=float(np.random.randint(0, 100)),
            y=float(np.random.randint(0, 100)),
            timestamp=i * 0.1,
        ))
    return events


def make_click_events(n: int = 10, selector: str = "button") -> list[Event]:
    """Generate sample click events."""
    events = []
    for i in range(n):
        events.append(Event(
            type="click",
            x=float(np.random.randint(0, 100)),
            y=float(np.random.randint(0, 100)),
            timestamp=i * 2.0,
            target_selector=selector,
        ))
    return events


def make_scroll_events(n: int = 20) -> list[Event]:
    """Generate sample scroll events."""
    events = []
    for i in range(n):
        events.append(Event(
            type="scroll",
            timestamp=i * 3.0,
            metadata={
                "direction": "down" if np.random.random() > 0.3 else "up",
                "delta": np.random.randint(10, 100),
                "viewport_pct": np.random.randint(0, 100),
            },
        ))
    return events


def make_mixed_events() -> list[Event]:
    """Generate mixed event stream with all types."""
    events = []
    timestamp = 0

    # Mouse moves
    for i in range(30):
        timestamp += 0.05
        events.append(Event(
            type="mouse_move",
            x=float(np.random.randint(0, 100)),
            y=float(np.random.randint(0, 100)),
            timestamp=timestamp,
        ))

    # Clicks
    for i in range(5):
        timestamp += 2.0
        events.append(Event(
            type="click",
            x=float(np.random.randint(0, 100)),
            y=float(np.random.randint(0, 100)),
            timestamp=timestamp,
            target_selector="button",
        ))

    # Scrolls
    for i in range(10):
        timestamp += 3.0
        events.append(Event(
            type="scroll",
            timestamp=timestamp,
            metadata={
                "direction": "down",
                "delta": np.random.randint(20, 50),
                "viewport_pct": int(timestamp / 10) % 100,
            },
        ))

    # Focus/blur for form tracking
    events.append(Event(type="focus", timestamp=timestamp + 1, target_selector="input#email"))
    timestamp += 2
    events.append(Event(type="blur", timestamp=timestamp, target_selector="input#email"))

    # Exit intent
    events.append(Event(type="exit_intent", timestamp=timestamp + 0.5))

    return events


# ── Feature Extraction Tests ────────────────────────────────────────────


class TestBehavioralFeatureExtractor:
    """Tests for BehavioralFeatureExtractor."""

    def test_init(self):
        """Extractor initializes with default window."""
        extractor = BehavioralFeatureExtractor()
        assert extractor.window_seconds == 5.0
        assert extractor.scaler_fitted is False

    def test_feature_names_count(self):
        """Extract 28 feature names."""
        assert len(BehavioralFeatureExtractor.FEATURE_NAMES) == 28

    def test_feature_names_list(self):
        """Feature names include all expected features."""
        names = BehavioralFeatureExtractor.FEATURE_NAMES
        assert "mouse_velocity_mean" in names
        assert "click_rage_click_count" in names
        assert "scroll_depth_max" in names
        assert "dwell_total_session_duration" in names

    def test_extract_from_empty_events(self):
        """Extract features from empty event list returns zeros."""
        extractor = BehavioralFeatureExtractor()
        features = extractor.transform([])

        assert features.shape == (28,)
        assert np.all(features == 0)

    def test_extract_output_shape(self):
        """Extracted features have correct shape (28,)."""
        extractor = BehavioralFeatureExtractor()
        events = make_mixed_events()
        features = extractor.transform(events)

        assert features.shape == (28,)

    def test_extract_mouse_features(self):
        """Mouse features are extracted correctly."""
        extractor = BehavioralFeatureExtractor()
        events = make_mouse_events(100)
        features = extractor.transform(events)

        # Mouse features are indices 0-7
        mouse_features = features[0:8]

        # Check some features are non-zero
        assert mouse_features[0] > 0  # velocity_mean
        assert mouse_features[7] > 0  # total_distance

    def test_extract_click_features(self):
        """Click features are extracted correctly."""
        extractor = BehavioralFeatureExtractor()
        events = make_click_events(20)
        features = extractor.transform(events)

        # Click features are indices 8-11
        click_features = features[8:12]

        # Should have click data
        assert click_features[0] >= 0  # rage_click_count

    def test_extract_scroll_features(self):
        """Scroll features are extracted correctly."""
        extractor = BehavioralFeatureExtractor()
        events = make_scroll_events(30)
        features = extractor.transform(events)

        # Scroll features are indices 12-15
        scroll_features = features[12:16]

        # Should have scroll data
        assert scroll_features[0] >= 0  # scroll_depth_max
        assert scroll_features[1] >= 0  # scroll_reversal_count

    def test_extract_dwell_features(self):
        """Dwell features are extracted correctly."""
        extractor = BehavioralFeatureExtractor()
        events = make_mixed_events()
        features = extractor.transform(events)

        # Dwell features are indices 16-19
        dwell_features = features[16:20]

        # Should have duration
        assert dwell_features[0] > 0  # total_session_duration

    def test_extract_combined_features(self):
        """Combined features are extracted correctly."""
        extractor = BehavioralFeatureExtractor()
        events = make_mixed_events()
        features = extractor.transform(events)

        # Combined features are indices 20-27
        combined_features = features[20:28]

        # Should have total events
        assert combined_features[0] > 0  # total_events

    def test_rage_click_detection(self):
        """Rage clicks are detected (3+ clicks on same element)."""
        extractor = BehavioralFeatureExtractor()
        # Create 5 clicks on same button within 1 second
        events = [
            Event(type="click", target_selector="button", timestamp=t * 0.1, x=50, y=50)
            for t in range(5)
        ]
        features = extractor.transform(events)

        rage_click_idx = 8  # click_rage_click_count
        assert features[rage_click_idx] >= 1

    def test_fit_transform_scales(self):
        """fit_transform properly scales features."""
        extractor = BehavioralFeatureExtractor()
        data = [make_mixed_events() for _ in range(10)]

        # Fit and transform
        scaled = extractor.fit_transform(data)

        assert scaled.shape == (10, 28)
        assert extractor.scaler_fitted is True

    def test_transform_after_fit(self):
        """Transform after fit uses fitted scaler."""
        extractor = BehavioralFeatureExtractor()
        data = [make_mixed_events() for _ in range(5)]

        extractor.fit_scaler([extractor.transform(e) for e in data])

        # Transform with fitted scaler
        features = extractor.transform(make_mixed_events())

        assert features.shape == (28,)

    def test_convert_dict_to_event(self):
        """Event.from_dict correctly creates Event from dict."""
        dict_event = {
            "type": "click",
            "x": 50.0,
            "y": 100.0,
            "timestamp": 123456.0,
            "element_id": "button",
            "value": "submit",
        }
        event = Event.from_dict(dict_event)

        assert event.type == "click"
        assert event.x == 50.0
        assert event.y == 100.0
        assert event.target_selector == "button"


# ── Emotion Classifier Tests ───────────────────────────────────────────


class TestEmotionClassifier:
    """Tests for EmotionClassifier."""

    def test_init_default(self):
        """Classifier initializes with default parameters."""
        classifier = EmotionClassifier()

        assert classifier.n_estimators == 100
        assert classifier.is_fitted is False
        assert classifier.emotions == Emotion.all_emotions()

    def test_emotions_list(self):
        """All 8 emotions are defined."""
        emotions = Emotion.all_emotions()

        assert len(emotions) == 8
        assert "confusion" in emotions
        assert "frustration" in emotions
        assert "delight" in emotions
        assert "boredom" in emotions
        assert "anxiety" in emotions
        assert "focus" in emotions
        assert "hesitation" in emotions
        assert "satisfaction" in emotions

    def test_train_sets_fitted(self):
        """Training sets fitted flag to True."""
        classifier = EmotionClassifier()

        X, y = generate_synthetic_training_data(n=100)
        metrics = classifier.train(X, y, BehavioralFeatureExtractor.FEATURE_NAMES)

        assert classifier.is_fitted is True
        assert "accuracy" in metrics
        assert "confusion_matrix" in metrics

    def test_predict_requires_training(self):
        """Predict raises error if model not trained."""
        classifier = EmotionClassifier()

        features = np.random.randn(28)

        with pytest.raises(RuntimeError, match="must be trained"):
            classifier.predict(features)

    def test_predict_output_type(self):
        """Predict returns EmotionResult."""
        classifier = EmotionClassifier()

        X, y = generate_synthetic_training_data(n=100)
        classifier.train(X, y, BehavioralFeatureExtractor.FEATURE_NAMES)

        features = X[0]
        result = classifier.predict(features)

        assert isinstance(result, EmotionResult)

    def test_predict_output_structure(self):
        """Predict result has all required fields."""
        classifier = EmotionClassifier()

        X, y = generate_synthetic_training_data(n=100)
        classifier.train(X, y, BehavioralFeatureExtractor.FEATURE_NAMES)

        features = X[0]
        result = classifier.predict(features)

        assert isinstance(result.primary_emotion, str)
        assert isinstance(result.confidence, float)
        assert isinstance(result.all_scores, dict)
        assert isinstance(result.valence, float)
        assert isinstance(result.arousal, float)
        assert isinstance(result.rule_adjustments, dict)

    def test_predict_all_scores_emotions(self):
        """All scores dict contains all 8 emotions."""
        classifier = EmotionClassifier()

        X, y = generate_synthetic_training_data(n=100)
        classifier.train(X, y, BehavioralFeatureExtractor.FEATURE_NAMES)

        features = X[0]
        result = classifier.predict(features)

        for emotion in Emotion.all_emotions():
            assert emotion in result.all_scores

    def test_predict_primary_emotion_is_valid(self):
        """Primary emotion is one of the 8 defined emotions."""
        classifier = EmotionClassifier()

        X, y = generate_synthetic_training_data(n=100)
        classifier.train(X, y, BehavioralFeatureExtractor.FEATURE_NAMES)

        features = X[0]
        result = classifier.predict(features)

        assert result.primary_emotion in Emotion.all_emotions()

    def test_predict_confidence_range(self):
        """Confidence is between 0 and 1."""
        classifier = EmotionClassifier()

        X, y = generate_synthetic_training_data(n=100)
        classifier.train(X, y, BehavioralFeatureExtractor.FEATURE_NAMES)

        for features in X[:10]:
            result = classifier.predict(features)
            assert 0.0 <= result.confidence <= 1.0

    def test_predict_batch(self):
        """predict_batch returns list of results."""
        classifier = EmotionClassifier()

        X, y = generate_synthetic_training_data(n=100)
        classifier.train(X, y, BehavioralFeatureExtractor.FEATURE_NAMES)

        features_list = X[:5]
        results = classifier.predict_batch(features_list)

        assert len(results) == 5
        assert all(isinstance(r, EmotionResult) for r in results)

    def test_save_load_model(self):
        """Save and load model preserves state."""
        import os
        import tempfile

        classifier = EmotionClassifier()

        X, y = generate_synthetic_training_data(n=100)
        classifier.train(X, y, BehavioralFeatureExtractor.FEATURE_NAMES)

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "test_model")

            # Save
            classifier.save_model(model_path)

            # Create new classifier and load
            new_classifier = EmotionClassifier()
            new_classifier.load_model(model_path)

            assert new_classifier.is_fitted is True
            assert new_classifier.feature_names == classifier.feature_names

            # Both should give same predictions
            features = X[0]
            result1 = classifier.predict(features)
            result2 = new_classifier.predict(features)

            assert result1.primary_emotion == result2.primary_emotion

    def test_save_unfitted_raises(self):
        """Saving unfitted model raises error."""
        import os
        import tempfile

        classifier = EmotionClassifier()

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "test_model")

            with pytest.raises(RuntimeError, match="unfitted"):
                classifier.save_model(model_path)


# ── Valence-Arousal Tests ───────────────────────────────────────────


class TestValenceArousal:
    """Tests for valence-arousal mapping."""

    def test_valence_arousal_has_all_emotions(self):
        """All 8 emotions have valence-arousal values."""
        for emotion in Emotion:
            assert emotion in VALENCE_AROUSAL

    def test_valence_range_valid(self):
        """Valence values are in valid range (-1 to 1)."""
        for emotion, (valence, arousal) in VALENCE_AROUSAL.items():
            assert -1.0 <= valence <= 1.0

    def test_arousal_range_valid(self):
        """Arousal values are in valid range (0 to 1)."""
        for emotion, (valence, arousal) in VALENCE_AROUSAL.items():
            assert 0.0 <= arousal <= 1.0

    def test_negative_emotions_have_negative_valence(self):
        """Negative emotions (frustration, confusion, anxiety, boredom) have negative valence."""
        negative_emotions = [
            Emotion.FRUSTRATION,
            Emotion.CONFUSION,
            Emotion.ANXIETY,
            Emotion.BOREDOM,
        ]

        for emotion in negative_emotions:
            valence, _ = VALENCE_AROUSAL[emotion]
            assert valence < 0

    def test_positive_emotions_have_positive_valence(self):
        """Positive emotions (delight, satisfaction, focus) have positive valence."""
        positive_emotions = [
            Emotion.DELIGHT,
            Emotion.SATISFACTION,
            Emotion.FOCUS,
        ]

        for emotion in positive_emotions:
            valence, _ = VALENCE_AROUSAL[emotion]
            assert valence > 0

    def test_high_arousal_emotions(self):
        """High arousal emotions have arousal > 0.7."""
        high_arousal = [
            Emotion.FRUSTRATION,
            Emotion.ANXIETY,
        ]

        for emotion in high_arousal:
            _, arousal = VALENCE_AROUSAL[emotion]
            assert arousal > 0.7

    def test_frustration_extremes(self):
        """Frustration has extreme negative valence and high arousal."""
        valence, arousal = VALENCE_AROUSAL[Emotion.FRUSTRATION]

        assert valence == -0.7
        assert arousal == 0.8

    def test_delight_extremes(self):
        """Delight has extreme positive valence and high arousal."""
        valence, arousal = VALENCE_AROUSAL[Emotion.DELIGHT]

        assert valence == 0.8
        assert arousal == 0.7


# ── EmotionResult Tests ─────────────────────────────────────────────────


class TestEmotionResult:
    """Tests for EmotionResult dataclass."""

    def test_to_dict_structure(self):
        """to_dict returns correct structure."""
        result = EmotionResult(
            primary_emotion="delight",
            confidence=0.85,
            all_scores={"delight": 0.85, "frustration": 0.15},
            valence=0.8,
            arousal=0.7,
            rule_adjustments={},
        )

        data = result.to_dict()

        assert data["primary_emotion"] == "delight"
        assert data["confidence"] == 0.85
        assert "all_scores" in data
        assert "valence" in data
        assert "arousal" in data
        assert "rule_adjustments" in data

    def test_to_dict_rounds_values(self):
        """to_dict rounds values to 4 decimal places."""
        result = EmotionResult(
            primary_emotion="delight",
            confidence=0.854321,
            all_scores={"delight": 0.854321, "frustration": 0.145679},
            valence=0.812345,
            arousal=0.765432,
        )

        data = result.to_dict()

        assert data["confidence"] == 0.8543
        assert data["all_scores"]["delight"] == 0.8543
        assert data["valence"] == 0.8123
        assert data["arousal"] == 0.7654


# ── Synthetic Data Tests ────────────────────────────────────────────────


class TestSyntheticDataGeneration:
    """Tests for synthetic training data generation."""

    def test_generate_output_shape(self):
        """Generated data has correct shape."""
        n = 5000
        X, y = generate_synthetic_training_data(n=n)

        assert X.shape == (n, 28)
        assert y.shape == (n,)

    def test_generate_balanced_labels(self):
        """Generated labels are balanced across 8 emotions."""
        n = 8000  # Must be divisible by 8
        X, y = generate_synthetic_training_data(n=n)

        from collections import Counter
        label_counts = Counter(y)

        # Each emotion should have n/8 samples
        expected_per_emotion = n // 8
        for emotion in Emotion.all_emotions():
            assert label_counts[emotion] == expected_per_emotion

    def test_generate_labels_are_valid(self):
        """All generated labels are valid emotions."""
        X, y = generate_synthetic_training_data(n=100)

        for label in y:
            assert label in Emotion.all_emotions()

    def test_generate_frustration_pattern(self):
        """Frustration samples have high rage clicks."""
        n = 1000
        X, y = generate_synthetic_training_data(n=n)

        # Get frustration samples
        frustration_indices = [i for i, label in enumerate(y) if label == Emotion.FRUSTRATION.value]
        frustration_samples = X[frustration_indices]

        # Check rage_click_count (index 8) is high
        rage_clicks = frustration_samples[:, 8]
        assert np.mean(rage_clicks) >= 2

    def test_generate_delight_pattern(self):
        """Delight samples have high session duration."""
        n = 1000
        X, y = generate_synthetic_training_data(n=n)

        # Get delight samples
        delight_indices = [i for i, label in enumerate(y) if label == Emotion.DELIGHT.value]
        delight_samples = X[delight_indices]

        # Check session duration (index 16) is high
        durations = delight_samples[:, 16]
        assert np.mean(durations) > 100

    def test_generate_confusion_pattern(self):
        """Confusion samples have high scroll reversals."""
        n = 1000
        X, y = generate_synthetic_training_data(n=n)

        # Get confusion samples
        confusion_indices = [i for i, label in enumerate(y) if label == Emotion.CONFUSION.value]
        confusion_samples = X[confusion_indices]

        # Check scroll reversals (index 12) is high
        reversals = confusion_samples[:, 12]
        assert np.mean(reversals) >= 3

    def test_reproducible_with_seed(self):
        """Synthetic data generation is reproducible."""
        X1, y1 = generate_synthetic_training_data(n=100)
        X2, y2 = generate_synthetic_training_data(n=100)

        np.testing.assert_array_equal(X1, X2)
        np.testing.assert_array_equal(y1, y2)


# ── Integration Tests ───────────────────────────────────────────────────


class TestEmotionPipelineIntegration:
    """Integration tests for full emotion classification pipeline."""

    def test_full_pipeline(self):
        """Test complete pipeline: extract features -> classify."""
        # Setup
        extractor = BehavioralFeatureExtractor()
        classifier = EmotionClassifier()

        # Generate and fit
        X, y = generate_synthetic_training_data(n=500)
        metrics = classifier.train(X, y, extractor.FEATURE_NAMES)

        assert classifier.is_fitted is True
        assert "accuracy" in metrics

        # Test prediction
        features = X[0]
        result = classifier.predict(features)

        assert result.primary_emotion in Emotion.all_emotions()
        assert 0.0 <= result.valence <= 1.0
        assert 0.0 <= result.arousal <= 1.0

    def test_end_to_end_from_events(self):
        """Test complete flow from raw events to emotion prediction."""
        extractor = BehavioralFeatureExtractor()
        classifier = EmotionClassifier()

        # Train classifier
        X, y = generate_synthetic_training_data(n=500)
        classifier.train(X, y, extractor.FEATURE_NAMES)

        # Extract features from events
        events = make_mixed_events()
        features = extractor.transform(events)

        # Predict emotion
        result = classifier.predict(features)

        # Validate result
        assert result.primary_emotion in Emotion.all_emotions()
        assert isinstance(result.confidence, float)
        assert isinstance(result.valence, float)
        assert isinstance(result.arousal, float)
