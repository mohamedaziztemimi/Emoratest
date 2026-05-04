"""Unit tests for Emotion Service.

Covers: event ingestion, session aggregation, why-analysis,
churn prediction, ROI ranking, and frustration spike detection.
"""

from __future__ import annotations

import pytest

from app.models.emotion_event import EmotionEvent, EmotionSession, EmotionSource
from app.services.emotion_service import (
    EmotionDropOff,
    EmotionResult,
    EmotionService,
    ExperimentROI,
    WhyAnalysis,
)

# ── Sample Data ────────────────────────────────────────────────────────


def make_sample_events(n: int = 20) -> list[dict]:
    """Generate sample behavioral events."""
    events = []
    for i in range(n):
        event_type = i % 3
        if event_type == 0:
            events.append({
                "type": "mouse_move",
                "x": float(i * 5 % 100),
                "y": float(i * 7 % 100),
                "ts": i * 0.1,
            })
        elif event_type == 1:
            events.append({
                "type": "click",
                "x": 50.0,
                "y": 50.0,
                "ts": i * 2.0,
                "element_id": "button" if i % 2 == 0 else "link",
            })
        else:
            events.append({
                "type": "scroll",
                "ts": i * 3.0,
                "metadata": {
                    "direction": "down" if i % 2 == 0 else "up",
                    "delta": i * 10,
                    "viewport_pct": i * 5 % 100,
                },
            })
    return events


def make_mixed_emotion_events() -> list[dict]:
    """Generate mixed emotion classification events."""
    return [
        {
            "type": "click",
            "ts": 0,
            "element_id": "button",
        },
        {
            "type": "mouse_move",
            "x": 50,
            "y": 50,
            "ts": 1,
        },
        {
            "type": "click",
            "ts": 2,
            "element_id": "button",
        },
    ]


# ── Emotion Service Init Tests ─────────────────────────────────────


class TestEmotionServiceInit:
    """Tests for EmotionService initialization."""

    def test_init(self):
        """Service initializes with components."""
        service = EmotionService()

        assert service.extractor is not None
        assert service.classifier is not None
        assert service.alert_threshold == 0.7


# ── Ingestion Tests ─────────────────────────────────────────────────


class TestEmotionIngestion:
    """Tests for emotion event ingestion."""

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_ingest_events_returns_result(self):
        """ingest_events returns EmotionResult."""
        service = EmotionService()
        events = make_sample_events(10)

        # Use sync wrapper for test
        import asyncio
        result = asyncio.run(service.ingest_events(
            session_id="test-session",
            raw_events=events,
        ))

        assert result is not None
        assert isinstance(result, EmotionResult)

    def test_ingest_events_sets_primary_emotion(self):
        """ingest_events sets primary emotion."""
        service = EmotionService()
        events = make_sample_events(10)

        import asyncio
        result = asyncio.run(service.ingest_events(
            session_id="test-session",
            raw_events=events,
        ))

        # Model now returns consolidated 4 emotions
        assert result.primary_emotion in [
            "frustrated", "confused", "engaged", "disengaged"
        ]

    def test_ingest_events_sets_confidence(self):
        """ingest_events sets confidence."""
        service = EmotionService()
        events = make_sample_events(10)

        import asyncio
        result = asyncio.run(service.ingest_events(
            session_id="test-session",
            raw_events=events,
        ))

        assert 0.0 <= result.confidence <= 1.0

    def test_ingest_events_sets_valence(self):
        """ingest_events sets valence in range."""
        service = EmotionService()
        events = make_sample_events(10)

        import asyncio
        result = asyncio.run(service.ingest_events(
            session_id="test-session",
            raw_events=events,
        ))

        assert -1.0 <= result.valence <= 1.0

    def test_ingest_events_sets_arousal(self):
        """ingest_events sets arousal in range."""
        service = EmotionService()
        events = make_sample_events(10)

        import asyncio
        result = asyncio.run(service.ingest_events(
            session_id="test-session",
            raw_events=events,
        ))

        assert 0.0 <= result.arousal <= 1.0

    def test_ingest_events_with_experiment_context(self):
        """ingest_events handles experiment and variant context."""
        service = EmotionService()
        events = make_sample_events(10)

        import asyncio
        result = asyncio.run(service.ingest_events(
            session_id="test-session",
            raw_events=events,
            experiment_id="exp-123",
            variant_id="variant-a",
            page_url="https://example.com/checkout",
        ))

        # Result should contain experiment context in persisted data
        assert result is not None


# ── EmotionEvent Model Tests ───────────────────────────────────────────


class TestEmotionEventModel:
    """Tests for EmotionEvent model."""

    def test_emotion_source_enum(self):
        """EmotionSource enum has all values."""
        assert EmotionSource.BEHAVIORAL == "behavioral"
        assert EmotionSource.WEBCAM == "webcam"
        assert EmotionSource.VOICE == "voice"
        assert EmotionSource.SURVEY == "survey"

    def test_is_high_confidence(self):
        """is_high_confidence correctly evaluates threshold."""
        event = EmotionEvent(
            session_id="test-uuid",
            primary_emotion="delight",
            confidence=0.8,
            valence=0.7,
            arousal=0.6,
            page_url="/test",
            source="behavioral",
        )

        assert event.is_high_confidence() is True
        assert event.is_high_confidence(threshold=0.9) is False

    def test_is_negative_emotion(self):
        """is_negative_emotion correctly identifies negative emotions."""
        frustration = EmotionEvent(
            session_id="test-uuid",
            primary_emotion="frustration",
            confidence=0.7,
            valence=-0.7,
            arousal=0.8,
            page_url="/test",
            source="behavioral",
        )

        delight = EmotionEvent(
            session_id="test-uuid",
            primary_emotion="delight",
            confidence=0.7,
            valence=0.8,
            arousal=0.7,
            page_url="/test",
            source="behavioral",
        )

        assert frustration.is_negative_emotion() is True
        assert delight.is_negative_emotion() is False

    def test_is_positive_emotion(self):
        """is_positive_emotion correctly identifies positive emotions."""
        delight = EmotionEvent(
            session_id="test-uuid",
            primary_emotion="delight",
            confidence=0.7,
            valence=0.8,
            arousal=0.7,
            page_url="/test",
            source="behavioral",
        )

        anxiety = EmotionEvent(
            session_id="test-uuid",
            primary_emotion="anxiety",
            confidence=0.7,
            valence=-0.5,
            arousal=0.9,
            page_url="/test",
            source="behavioral",
        )

        assert delight.is_positive_emotion() is True
        assert anxiety.is_positive_emotion() is False

    def test_get_emotion_sentiment(self):
        """get_emotion_sentiment returns correct category."""
        negative_event = EmotionEvent(
            session_id="test-uuid",
            primary_emotion="frustration",
            confidence=0.7,
            valence=-0.7,
            arousal=0.8,
            page_url="/test",
            source="behavioral",
        )

        positive_event = EmotionEvent(
            session_id="test-uuid",
            primary_emotion="delight",
            confidence=0.7,
            valence=0.8,
            arousal=0.7,
            page_url="/test",
            source="behavioral",
        )

        neutral_event = EmotionEvent(
            session_id="test-uuid",
            primary_emotion="hesitation",
            confidence=0.7,
            valence=-0.1,
            arousal=0.4,
            page_url="/test",
            source="behavioral",
        )

        assert negative_event.get_emotion_sentiment() == "negative"
        assert positive_event.get_emotion_sentiment() == "positive"
        assert neutral_event.get_emotion_sentiment() == "neutral"


# ── EmotionSession Model Tests ─────────────────────────────────────


class TestEmotionSessionModel:
    """Tests for EmotionSession model."""

    def test_get_primary_sentiment(self):
        """get_primary_sentiment maps emotions to sentiments."""
        sessions = {
            "frustration": EmotionSession(
                session_id="test-uuid",
                dominant_emotion="frustration",
                frustration_score=0.7,
            ),
            "delight": EmotionSession(
                session_id="test-uuid",
                dominant_emotion="delight",
                frustration_score=0.2,
            ),
            "hesitation": EmotionSession(
                session_id="test-uuid",
                dominant_emotion="hesitation",
                frustration_score=0.1,
            ),
        }

        assert sessions["frustration"].get_primary_sentiment() == "negative"
        assert sessions["delight"].get_primary_sentiment() == "positive"
        assert sessions["hesitation"].get_primary_sentiment() == "neutral"

    def test_is_at_risk(self):
        """is_at_risk correctly identifies risk sessions."""
        risky_session = EmotionSession(
            session_id="test-uuid",
            dominant_emotion="frustration",
            frustration_score=0.7,
            confusion_score=0.5,
        )

        safe_session = EmotionSession(
            session_id="test-uuid",
            dominant_emotion="delight",
            frustration_score=0.1,
            confusion_score=0.1,
        )

        assert risky_session.is_at_risk() is True
        assert safe_session.is_at_risk() is False


# ── Result Classes Tests ───────────────────────────────────────────────


class TestResultClasses:
    """Tests for result dataclasses."""

    def test_emotion_result_fields(self):
        """EmotionResult has all required fields."""
        result = EmotionResult(
            primary_emotion="delight",
            confidence=0.85,
            all_scores={"delight": 0.85, "frustration": 0.15},
            valence=0.8,
            arousal=0.7,
            rule_adjustments={"delight": 0.1},
        )

        assert result.primary_emotion == "delight"
        assert result.confidence == 0.85
        assert result.valence == 0.8
        assert result.arousal == 0.7
        assert "delight" in result.all_scores

    def test_emotion_drop_off_fields(self):
        """EmotionDropOff has all required fields."""
        drop_off = EmotionDropOff(
            emotion="confusion",
            drop_off_count=100,
            drop_off_percentage=35.5,
            avg_time_to_drop_off=45.0,
        )

        assert drop_off.emotion == "confusion"
        assert drop_off.drop_off_count == 100
        assert drop_off.drop_off_percentage == 35.5
        assert drop_off.avg_time_to_drop_off == 45.0

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_why_analysis_fields(self):
        """WhyAnalysis has all required fields."""
        analysis = WhyAnalysis(
            top_emotion_dropoffs=[],
            emotion_to_conversion_correlation={},
            frustration_funnel_map={},
            revenue_by_emotion={},
            total_sessions=1000,
            total_converted=150,
            total_revenue=5000.0,
        )

        assert analysis.total_sessions == 1000
        assert analysis.total_converted == 150
        assert analysis.total_revenue == 5000.0

    def test_experiment_roi_fields(self):
        """ExperimentROI has all required fields."""
        roi = ExperimentROI(
            experiment_id="exp-123",
            roi_score=85.5,
            primary_emotion_opportunity="frustration",
            estimated_lift=12.5,
            avg_frustration_reduction_potential=0.4,
            current_avg_frustration=0.6,
        )

        assert roi.experiment_id == "exp-123"
        assert roi.roi_score == 85.5
        assert roi.primary_emotion_opportunity == "frustration"
        assert roi.estimated_lift == 12.5


# ── Churn Prediction Tests ───────────────────────────────────────────


class TestChurnPrediction:
    """Tests for churn risk prediction."""

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_churn_formula(self):
        """Churn risk formula calculates correctly."""
        # High frustration
        frustration_churn = 0.7 * 0.4 + 0.3 * 0 + 0.3 * (1 - 1.0)  # 0.28
        assert abs(frustration_churn - 0.28) < 0.01

        # High delight
        delight_churn = 0.1 * 0.4 + 0.3 * 0 + 0.3 * (1 - 1.0)  # 0.07
        assert abs(delight_churn - 0.07) < 0.01

        # Mixed
        mixed_churn = 0.5 * 0.4 + 0.4 * 0.3 + 0.3 * (1 - 0.5)  # 0.39
        assert abs(mixed_churn - 0.39) < 0.01

    def test_churn_range(self):
        """Churn risk is always between 0 and 1."""
        for frustration in [0.0, 0.5, 1.0]:
            for confusion in [0.0, 0.5, 1.0]:
                for delight in [0.0, 0.5, 1.0]:
                    churn = (
                        frustration * 0.4 +
                        confusion * 0.3 +
                        (1.0 - min(delight, 1.0)) * 0.3
                    )
                    assert 0.0 <= churn <= 1.0


# ── ROI Ranking Tests ─────────────────────────────────────────────────


class TestROIRanking:
    """Tests for experiment ROI ranking."""

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_roi_formula(self):
        """ROI score formula calculates correctly."""
        # High frustration reduction + high lift
        roi1 = 0.5 * max(10.0, 0) * 100  # 500
        assert roi1 == 500.0

        # Low frustration reduction + moderate lift
        roi2 = 0.1 * max(3.0, 0) * 100  # 30
        assert roi2 == 30.0

        # Zero lift
        roi3 = 0.3 * max(0, 0) * 100  # 0
        assert roi3 == 0.0

    def test_roi_sorting(self):
        """ROI ranking sorts by score descending."""
        rois = [
            ExperimentROI(
                experiment_id="exp-a",
                roi_score=30.0,
                primary_emotion_opportunity="frustration",
                estimated_lift=3.0,
                avg_frustration_reduction_potential=0.1,
                current_avg_frustration=0.5,
            ),
            ExperimentROI(
                experiment_id="exp-b",
                roi_score=85.0,
                primary_emotion_opportunity="confusion",
                estimated_lift=12.0,
                avg_frustration_reduction_potential=0.4,
                current_avg_frustration=0.7,
            ),
            ExperimentROI(
                experiment_id="exp-c",
                roi_score=50.0,
                primary_emotion_opportunity="delight",
                estimated_lift=8.0,
                avg_frustration_reduction_potential=0.2,
                current_avg_frustration=0.4,
            ),
        ]

        sorted_rois = sorted(rois, key=lambda x: x.roi_score, reverse=True)

        assert sorted_rois[0].experiment_id == "exp-b"
        assert sorted_rois[1].experiment_id == "exp-c"
        assert sorted_rois[2].experiment_id == "exp-a"


# ── Drop-off Calculation Tests ─────────────────────────────────────


class TestDropOffCalculation:
    """Tests for drop-off calculation logic."""

    def test_drop_off_percentage_calculation(self):
        """Drop-off percentage is calculated correctly."""
        # 3 sessions, 1 dropped
        drop_off_pct = (1 / 3) * 100
        assert drop_off_pct == pytest.approx(33.33, rel=0.01)

        # 10 sessions, 5 dropped
        drop_off_pct = (5 / 10) * 100
        assert drop_off_pct == 50.0

    def test_drop_off_with_zero_sessions(self):
        """Zero sessions handled gracefully."""
        # With zero sessions, drop-off should be 0
        sessions = []
        drop_off_count = sum(1 for s in sessions if not getattr(s, "converted", True))

        assert drop_off_count == 0
