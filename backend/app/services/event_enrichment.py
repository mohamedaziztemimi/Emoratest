"""Event enrichment service - generates human-readable event descriptions.

This service reads raw events and creates enriched records for UI display.
Raw events table remains unchanged for ML pipeline integrity.
"""
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventEnriched


def generate_readable_description(event: Event) -> str | None:
    """Generate a human-readable description from raw event data.

    Args:
        event: Raw event with type, label, element_type, section, metadata

    Returns:
        Human-readable description or None for non-enrichable events
    """
    metadata = event.metadata_ or {}

    match event.type:
        case "click":
            # Rage click detection
            if metadata.get("rage_click"):
                click_count = metadata.get("click_count", 3)
                return f"🔥 Rage click: {click_count}+ rapid clicks"

            # Use enriched label if available
            if event.label:
                section_str = f" in {event.section}" if event.section else ""
                return f"Clicked '{event.label}'{section_str}"

            # Fallback to element type
            if event.element_type:
                section_str = f" ({event.section})" if event.section else ""
                return f"Clicked {event.element_type}{section_str}"

            # Fallback to selector parsing
            if event.selector:
                desc = _describe_selector(event.selector)
                return f"Clicked {desc}" if desc else None

            return None

        case "scroll":
            direction = metadata.get("direction", "unknown")
            if direction == "down":
                return "Scrolled down"
            if direction == "up":
                is_retreat = metadata.get("is_retreat", False)
                return "Scrolled up (retreat)" if is_retreat else "Scrolled up"
            return "Scrolled"

        case "exit_intent":
            trigger = metadata.get("trigger", "unknown")
            match trigger:
                case "mouse_leave":
                    return "Mouse left viewport (exit intent)"
                case "back_button":
                    return "Browser back button pressed"
                case "tab_switch":
                    return "Tab hidden (switched away)"
                case _:
                    return f"Exit intent ({trigger})"

        case "visibility":
            state = metadata.get("state", "unknown")
            return f"Page visibility: {state}"

        case "mouse_move" | "mouse_summary":
            return None  # Don't show individual mouse moves in timeline

        case _:
            return f"{event.type.replace('_', ' ').title()}"


def _describe_selector(selector: str) -> str | None:
    """Generate a readable description from a CSS selector."""
    if not selector:
        return None

    # Handle ID selector
    if selector.startswith("#"):
        return f"element with ID '{selector[1:]}'"

    # Handle class selectors
    if "." in selector:
        parts = selector.split(".")
        tag = parts[0] if parts[0] else "element"
        classes = ".".join(parts[1:])
        # Extract meaningful class names
        meaningful_classes = _extract_meaningful_classes(classes)
        if meaningful_classes:
            return f"{tag} with class '{meaningful_classes}'"
        return f"{tag} element"

    # Handle tag-only selector
    if re.match(r"^[a-z]+$", selector):
        return f"{selector} element"

    # Handle attribute selectors
    if "[" in selector:
        match = re.search(r'\[name="([^"]+)"\]', selector)
        if match:
            return f"input named '{match.group(1)}'"

    return None


def _extract_meaningful_classes(class_str: str) -> str:
    """Filter out utility/class-prefix classes, keep semantic ones."""
    # Split on dots
    classes = class_str.split(".")

    # Filter out common utility patterns
    ignored_prefixes = (
        "css-", "cls-", "style-", "Mui", "chakra", "tw-", "jsx", "__",
    )

    meaningful = [
        c for c in classes
        if c and not c.startswith(ignored_prefixes) and len(c) > 2
    ][:3]  # Max 3 classes

    return " ".join(meaningful) if meaningful else ""


async def enrich_events(
    db: AsyncSession,
    session_id: str,
    events: list[Event] | None = None,
) -> list[EventEnriched]:
    """Create enriched event records for a session.

    This is a non-blocking operation that creates UI-friendly descriptions
    without affecting the raw events used by ML.

    Args:
        db: Database session
        session_id: Session UUID to enrich events for
        events: Optional pre-fetched events (avoids re-query)

    Returns:
        List of enriched event records
    """
    import uuid

    # Fetch events if not provided
    if events is None:
        result = await db.execute(
            select(Event).where(Event.session_id == session_id)
        )
        events = result.scalars().all()

    enriched_records = []

    for event in events:
        # Skip if already enriched
        existing = await db.execute(
            select(EventEnriched).where(EventEnriched.event_id == event.id)
        )
        if existing.scalar_one_or_none():
            continue

        readable_desc = generate_readable_description(event)

        enriched = EventEnriched(
            event_id=event.id,
            session_id=event.session_id,
            type=event.type,
            ts=event.ts,
            label=event.label,
            section=event.section,
            element_type=event.element_type,
            readable_description=readable_desc,
        )
        enriched_records.append(enriched)

    if enriched_records:
        db.add_all(enriched_records)
        await db.commit()

    return enriched_records


async def get_enriched_timeline(
    db: AsyncSession,
    session_id: str,
) -> list[dict[str, Any]]:
    """Get enriched timeline for UI display.

    Args:
        db: Database session
        session_id: Session UUID

    Returns:
        List of enriched event dictionaries for timeline rendering
    """
    result = await db.execute(
        select(EventEnriched)
        .where(EventEnriched.session_id == session_id)
        .order_by(EventEnriched.ts)
    )
    enriched = result.scalars().all()

    return [
        {
            "id": e.id,
            "event_id": e.event_id,
            "type": e.type,
            "ts": e.ts.isoformat(),
            "label": e.label,
            "section": e.section,
            "element_type": e.element_type,
            "readable_description": e.readable_description,
        }
        for e in enriched
        if e.readable_description  # Only show enriched events
    ]
