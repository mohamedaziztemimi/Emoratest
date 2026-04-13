"""Emotion service for real-time ingestion, classification, and why-analysis.

Provides:
- Event ingestion with feature extraction and classification
- Why-analysis linking emotions to behaviors and outcomes
- Churn risk prediction
- Predictive experiment prioritization
- Frustration spike alerts
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    pass

# Add parent directory to path for ml module import
backend_dir = Path(__file__).parent.parent.parent
parent_dir = backend_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import ML components
from ml.src import (
    BehavioralFeatureExtractor,
    EmotionClassifier,
    EmotionResult,
    generate_synthetic_training_data,
)

# ── Result Classes ────────────────────────────────────────────────────────


@dataclass
class EmotionResult:
    """Result of emotion classification for an event batch."""

    primary_emotion: str
    confidence: float
    all_scores: dict[str, float]
    valence: float
    arousal: float
    rule_adjustments: dict[str, float] | None = None


@dataclass
class EmotionEventSummary:
    """Summary of classified events for a session."""

    session_id: str
    user_id: str | None = None
    events_processed: int = 0
    emotions_detected: list[str] = field(default_factory=list)
    high_frustration_count: int = 0


@dataclass
class EmotionDropOff:
    """Represents a drop-off associated with an emotion."""

    emotion: str
    drop_off_count: int
    drop_off_percentage: float
    avg_time_to_drop_off: float | None = None


@dataclass
class WhyAnalysis:
    """Why-analysis report linking emotions to behaviors and revenue."""

    top_emotion_drop_offs: list[EmotionDropOff]
    emotion_to_conversion_correlation: dict[str, float]
    frustration_funnel_map: dict[str, float]
    revenue_by_emotion: dict[str, float]
    total_sessions: int
    total_converted: int
    total_revenue: float


@dataclass
class ExperimentROI:
    """ROI score for experiment prioritization."""

    experiment_id: str
    roi_score: float
    estimated_lift: float
    avg_frustration_reduction_potential: float
    current_avg_frustration: float
    primary_emotion_opportunity: str | None = None


# ── Emotion Service ────────────────────────────────────────────────────────


class EmotionService:
    """Service for emotion ingestion, classification, and analysis.

    Key capabilities:
    - Real-time event ingestion with classification
    - Why-analysis linking emotions to drop-offs and revenue
    - Churn risk prediction
    - Predictive experiment prioritization
    - Frustration spike detection and alerting
    """

    def __init__(self):
        """Initialize emotion service."""
        self.extractor = BehavioralFeatureExtractor()
        # Load or initialize classifier
        self.classifier = self._load_or_init_classifier()
        self.alert_threshold = 0.7  # Frustration score alert threshold

    def _load_or_init_classifier(self) -> EmotionClassifier:
        """Load trained classifier or initialize with synthetic data.

        In production, this would load from persistent storage.
        For bootstrapping, trains on synthetic data.
        """
        # Try to load from file
        # classifier = EmotionClassifier()
        # classifier.load_model("path/to/model.json")
        # return classifier

        # Fall back: train on synthetic data
        classifier = EmotionClassifier(n_estimators=100)
        X, y = generate_synthetic_training_data(n=2000)
        classifier.train(X, y, BehavioralFeatureExtractor.FEATURE_NAMES)

        return classifier

    # ── INGESTION ───────────────────────────────────────────────────────

    async def ingest_events(
        self,
        session_id: str,
        raw_events: list[dict],
        experiment_id: str | None = None,
        variant_id: str | None = None,
        db: AsyncSession | None = None,
        user_id: str | None = None,
        page_url: str = "",
    ) -> EmotionResult:
        """Ingest raw behavioral events and classify emotions.

        Args:
            session_id: Session identifier.
            raw_events: List of raw event dictionaries.
            experiment_id: Associated experiment ID.
            variant_id: Associated variant ID.
            db: Database session for persistence.
            user_id: User identifier.
            page_url: Current page URL.

        Returns:
            EmotionResult from classification.
        """
        # Extract features
        features = self.extractor.transform(raw_events)

        # Classify
        result = self.classifier.predict(features)

        # Create EmotionEvent records for storage
        emotion_events = []
        emotion_timeline = []

        for i, event in enumerate(raw_events):
            emotion_events.append({
                "session_id": session_id,
                "user_id": user_id,
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "primary_emotion": result.primary_emotion,
                "confidence": result.confidence,
                "valence": result.valence,
                "arousal": result.arousal,
                "trigger_features": {
                    "feature_values": features.tolist(),
                    "event_index": i,
                },
                "page_url": page_url,
                "timestamp": datetime.fromtimestamp(event.get("ts", event.get("timestamp", 0)), tz=UTC),
                "source": "behavioral",
            })

            # Build timeline for session aggregation
            emotion_timeline.append({
                "timestamp": event.get("ts", event.get("timestamp", 0)),
                "emotion": result.primary_emotion,
                "confidence": result.confidence,
            })

        # Persist events if DB provided
        if db:
            await self._persist_emotion_events(
                db,
                emotion_events,
                session_id,
                user_id,
            )

        # Update session summary
        if db:
            await self._update_emotion_session(
                db,
                session_id,
                user_id,
                experiment_id,
                variant_id,
                result,
                emotion_timeline,
            )

        # Check for alerts
        if result.primary_emotion == "frustration" and result.confidence > self.alert_threshold:
            await self._trigger_frustration_alert(session_id, result)

        return result

    async def _persist_emotion_events(
        self,
        db: AsyncSession,
        events: list[dict],
        session_id: str,
        user_id: str | None,
    ) -> None:
        """Persist EmotionEvent records to database."""
        from app.models.emotion_event import EmotionEvent

        for event_data in events:
            event = EmotionEvent(
                session_id=event_data["session_id"],
                user_id=event_data["user_id"],
                primary_emotion=event_data["primary_emotion"],
                confidence=event_data["confidence"],
                valence=event_data["valence"],
                arousal=event_data["arousal"],
                trigger_features=event_data["trigger_features"],
                page_url=event_data["page_url"],
                timestamp=event_data["timestamp"],
                source=event_data["source"],
            )
            db.add(event)

        await db.commit()

    async def _update_emotion_session(
        self,
        db: AsyncSession,
        session_id: str,
        user_id: str | None,
        experiment_id: str | None,
        variant_id: str | None,
        result: EmotionResult,
        emotion_timeline: list[dict],
    ) -> None:
        """Update or create EmotionSession with aggregated data."""
        from app.models.emotion_event import EmotionSession
        from app.models.session import Session as UserSession

        # Try to load existing session
        session_result = await db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        user_session = session_result.scalar_one_or_none()

        # Load existing emotion session
        emotion_session_result = await db.execute(
            select(EmotionSession).where(EmotionSession.session_id == session_id)
        )
        emotion_session = emotion_session_result.scalar_one_or_none()

        # Calculate scores
        emotion_scores = result.all_scores
        frustration_score = emotion_scores.get("frustration", 0.0)
        confusion_score = emotion_scores.get("confusion", 0.0)
        delight_score = emotion_scores.get("delight", 0.0)

        # Get outcome info if available
        converted = user_session.outcome == "purchase" if user_session else None
        # Revenue would need to be joined with order data
        # For now, set to None
        revenue = None

        if emotion_session:
            # Update existing
            emotion_session.update_emotion_scores(emotion_scores)
            emotion_session.emotion_timeline = emotion_timeline
            emotion_session.updated_at = datetime.now(UTC)
        else:
            # Create new
            emotion_session = EmotionSession(
                session_id=session_id,
                user_id=user_id,
                experiment_id=experiment_id,
                variant_id=variant_id,
                dominant_emotion=result.primary_emotion,
                emotion_timeline=emotion_timeline,
                frustration_score=frustration_score,
                confusion_score=confusion_score,
                delight_score=delight_score,
                converted=converted,
                revenue=revenue,
            )
            db.add(emotion_session)

        await db.commit()

    async def _trigger_frustration_alert(self, session_id: str, result: EmotionResult) -> None:
        """Trigger alert for high frustration.

        Args:
            session_id: Session identifier.
            result: Classification result.
        """
        # In production, this would:
        # 1. Call AlertService to create alert record
        # 2. Emit WebSocket message to connected dashboards
        # 3. Send webhook to Slack/Email if configured

        # For now, log the alert
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"High frustration detected - session: {session_id}, "
            f"emotion: {result.primary_emotion}, "
            f"confidence: {result.confidence}"
        )

    # ── WHY ANALYSIS ─────────────────────────────────────────────────────

    async def get_why_analysis(
        self,
        experiment_id: str,
        variant_id: str | None = None,
        days: int = 30,
        db: AsyncSession | None = None,
    ) -> WhyAnalysis:
        """Generate why-analysis linking emotions to behaviors and revenue.

        Args:
            experiment_id: Experiment to analyze.
            variant_id: Optional variant for comparison.
            days: Number of days to analyze.
            db: Database session.

        Returns:
            WhyAnalysis with emotion drop-offs, correlations, and revenue breakdown.
        """
        if not db:
            return WhyAnalysis(
                top_emotion_drop_offs=[],
                emotion_to_conversion_correlation={},
                frustration_funnel_map={},
                revenue_by_emotion={},
                total_sessions=0,
                total_converted=0,
                total_revenue=0.0,
            )

        from app.models.emotion_event import EmotionSession

        # Calculate date cutoff
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Query sessions
        query = select(EmotionSession).where(
            and_(
                EmotionSession.experiment_id == experiment_id,
                EmotionSession.last_event_at >= cutoff,
            )
        )

        if variant_id:
            query = query.where(EmotionSession.variant_id == variant_id)

        result = await db.execute(query)
        sessions = result.scalars().all()

        if not sessions:
            return WhyAnalysis(
                top_emotion_drop_offs=[],
                emotion_to_conversion_correlation={},
                frustration_funnel_map={},
                revenue_by_emotion={},
                total_sessions=0,
                total_converted=0,
                total_revenue=0.0,
            )

        # Calculate drop-offs by emotion
        drop_offs_by_emotion = self._calculate_drop_offs(sessions)

        # Calculate emotion to conversion correlation
        emotion_to_conversion = self._calculate_conversion_correlation(sessions)

        # Calculate frustration funnel map
        frustration_funnel = self._calculate_frustration_funnel(sessions)

        # Calculate revenue by emotion
        revenue_by_emotion = self._calculate_revenue_by_emotion(sessions)

        # Calculate totals
        total_sessions = len(sessions)
        total_converted = sum(1 for s in sessions if s.converted)
        total_revenue = sum(s.revenue or 0 for s in sessions if s.revenue)

        return WhyAnalysis(
            top_emotion_drop_offs=sorted(
                drop_offs_by_emotion.values(), key=lambda x: x.drop_off_count, reverse=True
            )[:5],
            emotion_to_conversion_correlation=emotion_to_conversion,
            frustration_funnel_map=frustration_funnel,
            revenue_by_emotion=revenue_by_emotion,
            total_sessions=total_sessions,
            total_converted=total_converted,
            total_revenue=total_revenue,
        )

    def _calculate_drop_offs(self, sessions: list) -> dict[str, EmotionDropOff]:
        """Calculate drop-off analysis by emotion."""

        # Count sessions by dominant emotion
        emotion_counts = defaultdict(int)
        emotion_times = defaultdict(list)

        for session in sessions:
            emotion = session.dominant_emotion or "unknown"
            emotion_counts[emotion] += 1
            emotion_times[emotion].append(
                session.last_event_at - session.first_event_at
            )

        # Count drop-offs (sessions without conversion)
        drop_off_counts = defaultdict(int)
        for session in sessions:
            if not session.converted:
                emotion = session.dominant_emotion or "unknown"
                drop_off_counts[emotion] += 1

        # Build drop-off objects
        drop_offs = {}
        for emotion, count in emotion_counts.items():
            if count == 0:
                continue

            drop_off_count = drop_off_counts.get(emotion, 0)
            drop_off_pct = (drop_off_count / count) * 100

            avg_time = None
            if emotion in emotion_times and len(emotion_times[emotion]) > 0:
                avg_time = sum(
                    dt.total_seconds() for dt in emotion_times[emotion]
                ) / len(emotion_times[emotion])

            drop_offs[emotion] = EmotionDropOff(
                emotion=emotion,
                drop_off_count=drop_off_count,
                drop_off_percentage=drop_off_pct,
                avg_time_to_drop_off=avg_time,
            )

        return drop_offs

    def _calculate_conversion_correlation(self, sessions: list) -> dict[str, float]:
        """Calculate correlation between emotions and conversion.

        Returns correlation coefficient for each emotion.
        """

        emotion_metrics = defaultdict(lambda: {"converted": 0, "total": 0})

        for session in sessions:
            emotion = session.dominant_emotion or "unknown"
            emotion_metrics[emotion]["total"] += 1
            if session.converted:
                emotion_metrics[emotion]["converted"] += 1

        # Calculate conversion rate by emotion
        emotion_to_conversion = {}
        for emotion, metrics in emotion_metrics.items():
            if metrics["total"] > 0:
                conversion_rate = metrics["converted"] / metrics["total"]
                emotion_to_conversion[emotion] = round(conversion_rate, 4)
            else:
                emotion_to_conversion[emotion] = 0.0

        return emotion_to_conversion

    def _calculate_frustration_funnel(self, sessions: list) -> dict[str, float]:
        """Calculate frustration drop-off percentage by funnel stage.

        Args:
            sessions: List of emotion sessions.

        Returns:
            Dict mapping funnel stages to frustration drop-off %.
        """
        # This would require page/element tracking data
        # For now, return mock structure
        return {
            "landing": 15.0,
            "engaged": 25.0,
            "intent": 35.0,
            "checkout": 45.0,
        }

    def _calculate_revenue_by_emotion(self, sessions: list) -> dict[str, float]:
        """Calculate total revenue by dominant emotion."""

        revenue_by_emotion = defaultdict(float)
        emotion_sessions = defaultdict(int)

        for session in sessions:
            emotion = session.dominant_emotion or "unknown"
            if session.revenue:
                revenue_by_emotion[emotion] += session.revenue
            emotion_sessions[emotion] += 1

        # Calculate average revenue per session
        revenue_avg = {}
        for emotion in revenue_by_emotion:
            if emotion_sessions[emotion] > 0:
                revenue_avg[emotion] = revenue_by_emotion[emotion] / emotion_sessions[emotion]

        return revenue_avg

    # ── CHURN PREDICTION ───────────────────────────────────────────────

    async def predict_churn_risk(
        self,
        session_id: str,
        db: AsyncSession | None = None,
    ) -> float:
        """Predict churn risk for a session.

        Rule-based formula:
        churn_risk = frustration_score * 0.4 + confusion_score * 0.3 + (1 - delight_score) * 0.3

        Args:
            session_id: Session identifier.
            db: Database session.

        Returns:
            Float churn risk score (0-1).
        """
        if not db:
            return 0.0

        from app.models.emotion_event import EmotionSession

        # Load session
        result = await db.execute(
            select(EmotionSession).where(EmotionSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return 0.0

        # Calculate churn risk
        frustration = session.frustration_score
        confusion = session.confusion_score
        delight = session.delight_score

        churn_risk = (
            frustration * 0.4 +
            confusion * 0.3 +
            (1.0 - min(delight, 1.0)) * 0.3
        )

        # Update and save
        session.churn_risk = churn_risk
        await db.commit()

        return churn_risk

    # ── PREDICTIVE PRIORITIZATION ─────────────────────────────────────

    async def rank_experiments_by_emotional_roi(
        self,
        experiment_ids: list[str],
        db: AsyncSession | None = None,
    ) -> list[ExperimentROI]:
        """Rank experiments by emotional ROI for prioritization.

        Score formula:
        roi_score = avg_frustration_reduction_potential * estimated_conversion_lift

        Args:
            experiment_ids: List of experiment IDs to rank.
            db: Database session.

        Returns:
            List of ExperimentROI sorted by roi_score descending.
        """
        if not db:
            return []

        from app.models.emotion_event import EmotionSession

        # Calculate metrics for each experiment
        experiment_scores = []

        for exp_id in experiment_ids:
            # Query sessions for this experiment
            result = await db.execute(
                select(EmotionSession).where(
                    and_(
                        EmotionSession.experiment_id == exp_id,
                        EmotionSession.last_event_at >= datetime.now(UTC) - timedelta(days=30),
                    )
                )
            )
            sessions = result.scalars().all()

            if not sessions:
                continue

            # Calculate averages
            avg_frustration = sum(s.frustration_score for s in sessions) / len(sessions)
            avg_confusion = sum(s.confusion_score for s in sessions) / len(sessions)
            avg_delight = sum(s.delight_score for s in sessions) / len(sessions)
            conversion_rate = sum(1 for s in sessions if s.converted) / len(sessions)

            # Identify primary emotion opportunity
            emotion_opportunity = None
            if avg_frustration > 0.3:
                emotion_opportunity = "frustration"
            elif avg_confusion > 0.3:
                emotion_opportunity = "confusion"
            elif avg_delight > 0.5:
                emotion_opportunity = "delight"

            # Calculate scores
            frustration_reduction = 1.0 - min(avg_frustration, 1.0)
            estimated_lift = (conversion_rate - 0.04) * 100  # Assume 4% baseline

            # ROI score
            roi_score = frustration_reduction * max(estimated_lift, 0) * 100

            experiment_scores.append(ExperimentROI(
                experiment_id=exp_id,
                roi_score=roi_score,
                primary_emotion_opportunity=emotion_opportunity,
                estimated_lift=estimated_lift,
                avg_frustration_reduction_potential=frustration_reduction,
                current_avg_frustration=avg_frustration,
            ))

        # Sort by ROI score
        return sorted(experiment_scores, key=lambda x: x.roi_score, reverse=True)

    # ── ALERTS ────────────────────────────────────────────────────────────

    async def check_frustration_spike(
        self,
        experiment_id: str,
        window_minutes: int = 15,
        db: AsyncSession | None = None,
    ) -> bool:
        """Check if there's a frustration spike in the recent window.

        Args:
            experiment_id: Experiment to check.
            window_minutes: Time window in minutes.
            db: Database session.

        Returns:
            True if frustration events > 2 std devs above rolling mean.
        """
        if not db:
            return False

        from app.models.emotion_event import EmotionEvent

        # Calculate time window
        cutoff = datetime.now(UTC) - timedelta(minutes=window_minutes)

        # Query recent events
        result = await db.execute(
            select(EmotionEvent).where(
                and_(
                    EmotionEvent.experiment_id == experiment_id,
                    EmotionEvent.timestamp >= cutoff,
                    EmotionEvent.primary_emotion == "frustration",
                )
            )
        )
        events = result.scalars().all()

        if len(events) < 5:
            return False

        # Calculate moving stats
        confidences = [e.confidence for e in events]
        mean_conf = sum(confidences) / len(confidences)
        std_conf = math.sqrt(sum((c - mean_conf) ** 2 for c in confidences) / len(confidences))

        # Check for spike (current mean > rolling mean + 2*std)
        if std_conf == 0:
            return False

        spike_threshold = mean_conf + (2 * std_conf)
        recent_mean = sum(confidences[-5:]) / min(len(confidences), 5)

        spike_detected = recent_mean > spike_threshold

        if spike_detected:
            # Log spike
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Frustration spike detected - experiment: {experiment_id}, "
                f"window: {window_minutes}m, "
                f"recent: {recent_mean:.3f}, threshold: {spike_threshold:.3f}"
            )

        return spike_detected
