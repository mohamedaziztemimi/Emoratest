"""Consolidate 8 emotions to 4 scientifically-grounded emotions

Revision ID: 020_consolidate_emotions
Revises: 019_create_waitlist_table
Create Date: 2024-05-02

This migration consolidates the 8-emotion system to a 4-emotion system:
- OLD: confusion, frustration, delight, boredom, anxiety, focus, hesitation, satisfaction
- NEW: frustrated, confused, engaged, disengaged

Mapping:
- frustration, anxiety → frustrated
- confusion → confused
- focus, satisfaction, delight → engaged
- boredom, hesitation → disengaged

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '020_consolidate_emotions'
down_revision = '019_create_waitlist_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Consolidate 8 emotions to 4 emotions."""

    # Update primary_emotion column
    op.execute("""
        UPDATE sessions
        SET primary_emotion = 'frustrated'
        WHERE primary_emotion IN ('frustration', 'anxiety')
    """)

    op.execute("""
        UPDATE sessions
        SET primary_emotion = 'confused'
        WHERE primary_emotion = 'confusion'
    """)

    op.execute("""
        UPDATE sessions
        SET primary_emotion = 'engaged'
        WHERE primary_emotion IN ('focus', 'satisfaction', 'delight')
    """)

    op.execute("""
        UPDATE sessions
        SET primary_emotion = 'disengaged'
        WHERE primary_emotion IN ('boredom', 'hesitation')
    """)

    # Update emotion_scores JSONB column
    # This consolidates the probabilities from old emotions to new ones
    op.execute("""
        UPDATE sessions
        SET emotion_scores = (
            SELECT jsonb_build_object(
                'frustrated',
                COALESCE((emotion_scores->>'frustration')::float, 0) + COALESCE((emotion_scores->>'anxiety')::float, 0),
                'confused',
                COALESCE((emotion_scores->>'confusion')::float, 0),
                'engaged',
                COALESCE((emotion_scores->>'focus')::float, 0) +
                    COALESCE((emotion_scores->>'satisfaction')::float, 0) +
                    COALESCE((emotion_scores->>'delight')::float, 0),
                'disengaged',
                COALESCE((emotion_scores->>'boredom')::float, 0) +
                    COALESCE((emotion_scores->>'hesitation')::float, 0)
            )
            FROM sessions s2
            WHERE s2.id = sessions.id
        )
        WHERE emotion_scores IS NOT NULL
    """)


def downgrade() -> None:
    """Revert to 8-emotion system (lossy - distributes probabilities evenly)."""

    # Revert primary_emotion (lossy conversion)
    op.execute("""
        UPDATE sessions
        SET primary_emotion = 'frustration'
        WHERE primary_emotion = 'frustrated'
    """)

    # For 'confused', we keep it as is (same in both systems)
    # For 'engaged', distribute to focus/satisfaction (lossy)
    op.execute("""
        UPDATE sessions
        SET primary_emotion = CASE
            WHEN random() < 0.33 THEN 'focus'
            WHEN random() < 0.66 THEN 'satisfaction'
            ELSE 'delight'
        END
        WHERE primary_emotion = 'engaged'
    """)

    # For 'disengaged', distribute to boredom/hesitation (lossy)
    op.execute("""
        UPDATE sessions
        SET primary_emotion = CASE
            WHEN random() < 0.5 THEN 'boredom'
            ELSE 'hesitation'
        END
        WHERE primary_emotion = 'disengaged'
    """)

    # Revert emotion_scores (create approximate distribution)
    op.execute("""
        UPDATE sessions
        SET emotion_scores = (
            SELECT jsonb_build_object(
                'frustration', GREATEST((emotion_scores->>'frustrated')::float * 0.6, 0.01),
                'anxiety', GREATEST((emotion_scores->>'frustrated')::float * 0.4, 0.01),
                'confusion', GREATEST((emotion_scores->>'confused')::float, 0.01),
                'focus', GREATEST((emotion_scores->>'engaged')::float * 0.33, 0.01),
                'satisfaction', GREATEST((emotion_scores->>'engaged')::float * 0.33, 0.01),
                'delight', GREATEST((emotion_scores->>'engaged')::float * 0.34, 0.01),
                'boredom', GREATEST((emotion_scores->>'disengaged')::float * 0.5, 0.01),
                'hesitation', GREATEST((emotion_scores->>'disengaged')::float * 0.5, 0.01)
            )
            FROM sessions s2
            WHERE s2.id = sessions.id
        )
        WHERE emotion_scores IS NOT NULL
    """)
