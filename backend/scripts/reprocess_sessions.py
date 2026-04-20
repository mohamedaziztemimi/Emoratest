#!/usr/bin/env python3
"""Reprocess existing sessions to add emotion predictions.

This script finds all sessions that ended but don't have emotion data,
then runs the feature worker to compute emotions for each.

Usage:
    docker-compose exec backend python /app/scripts/reprocess_sessions.py
"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import async_session
from app.models.session import Session
from app.services.feature_worker import process_session


async def reprocess_sessions() -> None:
    """Reprocess all sessions without emotion data."""

    async with async_session() as db:
        # Find sessions that ended but have no emotion
        result = await db.execute(
            select(Session).where(
                Session.primary_emotion.is_(None),
                Session.ended_at.isnot(None),
            )
        )
        sessions = result.scalars().all()

        if not sessions:
            print("No sessions to reprocess.")
            return

        print(f"Found {len(sessions)} sessions to reprocess...")
        print("=" * 60)

        success = 0
        failed = 0

        for i, session in enumerate(sessions, 1):
            session_id = str(session.id)
            try:
                # Process the session
                result = await process_session(session_id)

                if result.get("status") == "ok":
                    # Get the updated session to see what emotion was assigned
                    await db.refresh(session)
                    emotion = session.primary_emotion or "none"
                    confidence = session.emotion_confidence or 0
                    print(f"[{i}/{len(sessions)}] {session_id[:8]}... → {emotion} ({confidence:.2%})")
                    success += 1
                else:
                    print(f"[{i}/{len(sessions)}] {session_id[:8]}... → Skipped: {result.get('detail', 'unknown')}")
                    failed += 1

            except Exception as e:
                print(f"[{i}/{len(sessions)}] {session_id[:8]}... → ERROR: {e}")
                failed += 1

        print("=" * 60)
        print(f"Complete! {success} succeeded, {failed} failed")


async def reprocess_single(session_id: str) -> None:
    """Reprocess a single session by ID."""

    async with async_session() as db:
        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            print(f"Session {session_id} not found")
            return

        print(f"Processing session {session_id}...")
        result = await process_session(session_id)

        await db.refresh(session)
        print(f"  Outcome: {session.outcome}")
        print(f"  Primary emotion: {session.primary_emotion}")
        print(f"  Emotion confidence: {session.emotion_confidence}")
        print(f"  Abandonment risk: {session.abandonment_risk}")
        print(f"  Friction score: {session.friction_score}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reprocess sessions for emotion data")
    parser.add_argument("--session", help="Reprocess a single session ID")
    args = parser.parse_args()

    if args.session:
        asyncio.run(reprocess_single(args.session))
    else:
        asyncio.run(reprocess_sessions())
