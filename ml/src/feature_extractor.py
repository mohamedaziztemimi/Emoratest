"""Behavioral feature extractor for emotion classification.

Extracts 28 features from raw event streams including mouse movement,
click patterns, scroll behavior, dwell time, and session engagement.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from sklearn.preprocessing import StandardScaler

if TYPE_CHECKING:
    pass


@dataclass
class Event:
    """Raw event from behavioral tracking."""

    type: str
    x: float | None = None
    y: float | None = None
    timestamp: float = 0.0
    target_selector: str | None = None
    value: str | None = None
    metadata: dict | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Event:
        """Create Event from dictionary."""
        return cls(
            type=data.get("type", ""),
            x=data.get("x"),
            y=data.get("y"),
            timestamp=data.get("ts", data.get("timestamp", 0.0)),
            target_selector=data.get("element_id", data.get("target_selector")),
            value=data.get("value"),
            metadata=data.get("metadata"),
        )


class BehavioralFeatureExtractor:
    """Extract behavioral features from raw event streams.

    Extracts 28 features across 4 categories:
    - Mouse features (velocity, direction changes, idle, backtrack)
    - Click features (rage clicks, dead clicks, heatmap entropy, double-clicks)
    - Scroll features (depth, reversals, speed variance, reading pauses)
    - Dwell features (duration, engagement ratio, tab switches, form abandonment)
    """

    # Feature names for 28-dimensional output
    FEATURE_NAMES = [
        # Mouse features (8)
        "mouse_velocity_mean",
        "mouse_velocity_std",
        "mouse_velocity_max",
        "mouse_direction_changes_per_sec",
        "mouse_hover_duration_on_cta",
        "mouse_cursor_idle_ratio",
        "mouse_backtrack_ratio",
        "mouse_movement_total_distance",
        # Click features (4)
        "click_rage_click_count",
        "click_dead_click_count",
        "click_heatmap_entropy",
        "click_double_click_rate",
        # Scroll features (4)
        "scroll_depth_max",
        "scroll_reversal_count",
        "scroll_speed_variance",
        "scroll_reading_pause_count",
        # Dwell features (4)
        "dwell_total_session_duration",
        "dwell_active_engagement_ratio",
        "dwell_tab_switch_count",
        "dwell_form_abandon_count",
        # Combined features (8)
        "session_total_events",
        "session_events_per_second",
        "session_mouse_click_ratio",
        "session_scroll_click_ratio",
        "session_idle_periods",
        "session_burst_activity_count",
        "session_form_interaction_duration",
        "session_cta_click_count",
    ]

    def __init__(self, window_seconds: float = 5.0):
        """Initialize feature extractor.

        Args:
            window_seconds: Time window for time-based features (default 5s).
        """
        self.window_seconds = window_seconds
        self.scaler = StandardScaler()
        self.scaler_fitted = False

    def fit_scaler(self, data: list[np.ndarray] | np.ndarray) -> None:
        """Fit the StandardScaler on feature data.

        Args:
            data: List or array of feature vectors.
        """
        if isinstance(data, list):
            data = np.array(data)
        self.scaler.fit(data)
        self.scaler_fitted = True

    def transform(self, events: list[dict | Event]) -> np.ndarray:
        """Extract features from event stream.

        Args:
            events: List of event dictionaries or Event objects.

        Returns:
            Numpy array of shape (28,) with extracted features.
        """
        # Convert to Event objects if needed
        parsed_events = []
        for e in events:
            if isinstance(e, Event):
                parsed_events.append(e)
            else:
                parsed_events.append(Event.from_dict(e))

        if not parsed_events:
            return np.zeros(28)

        # Extract feature groups
        mouse_features = self._extract_mouse_features(parsed_events)
        click_features = self._extract_click_features(parsed_events)
        scroll_features = self._extract_scroll_features(parsed_events)
        dwell_features = self._extract_dwell_features(parsed_events)
        combined_features = self._extract_combined_features(parsed_events)

        # Concatenate all features
        features = np.concatenate([
            mouse_features,
            click_features,
            scroll_features,
            dwell_features,
            combined_features,
        ])

        # Scale if fitted
        if self.scaler_fitted:
            features = self.scaler.transform([features])[0]

        return features

    def fit_transform(self, data: list[list[dict | Event]]) -> np.ndarray:
        """Fit scaler and transform event streams.

        Args:
            data: List of event streams.

        Returns:
            Numpy array of shape (n_samples, 28).
        """
        # Extract all features first
        all_features = np.array([self.transform(events) for events in data])
        # Fit scaler
        self.fit_scaler(all_features)
        # Transform
        return self.scaler.transform(all_features)

    def _extract_mouse_features(self, events: list[Event]) -> np.ndarray:
        """Extract mouse movement features (8 features)."""
        mouse_events = [e for e in events if e.type == "mouse_move"]

        if not mouse_events:
            return np.zeros(8)

        # Calculate velocities between consecutive points
        velocities = []
        prev_event = None

        for event in mouse_events:
            if prev_event and prev_event.x is not None and event.x is not None:
                dt = event.timestamp - prev_event.timestamp
                if dt > 0:
                    dx = event.x - prev_event.x
                    dy = event.y - prev_event.y
                    distance = math.sqrt(dx**2 + dy**2)
                    velocity = distance / dt
                    velocities.append(velocity)
            prev_event = event
            prev_event = event

        if not velocities:
            return np.zeros(8)

        velocities = np.array(velocities)
        velocity_mean = np.mean(velocities)
        velocity_std = np.std(velocities)
        velocity_max = np.max(velocities)

        # Direction changes per second
        direction_changes = self._count_direction_changes(mouse_events)
        duration = mouse_events[-1].timestamp - mouse_events[0].timestamp
        direction_changes_per_sec = direction_changes / max(duration, 1)

        # Hover duration on CTA elements
        cta_selectors = ["button", "cta", "checkout", "buy", "submit"]
        hover_duration_on_cta = self._calculate_hover_duration(
            mouse_events, cta_selectors
        )

        # Cursor idle ratio
        idle_ratio = self._calculate_idle_ratio(mouse_events)

        # Backtrack ratio (leftward/upward movement)
        backtrack_ratio = self._calculate_backtrack_ratio(mouse_events)

        # Total distance moved
        total_distance = np.sum(np.sqrt(np.diff([e.x or 0 for e in mouse_events])**2 +
                                        np.diff([e.y or 0 for e in mouse_events])**2))

        return np.array([
            velocity_mean,
            velocity_std,
            velocity_max,
            direction_changes_per_sec,
            hover_duration_on_cta,
            idle_ratio,
            backtrack_ratio,
            total_distance,
        ])

    def _extract_click_features(self, events: list[Event]) -> np.ndarray:
        """Extract click behavior features (4 features)."""
        click_events = [e for e in events if e.type == "click"]

        if not click_events:
            return np.zeros(4)

        # Rage clicks: 3+ clicks on same element within 2 seconds
        rage_click_count = self._count_rage_clicks(click_events)

        # Dead clicks: clicks with no subsequent page event/response
        dead_click_count = self._count_dead_clicks(click_events, events)

        # Click heatmap entropy: measure of spread vs concentration
        heatmap_entropy = self._calculate_click_heatmap_entropy(click_events)

        # Double click rate
        double_click_rate = self._calculate_double_click_rate(click_events)

        return np.array([
            rage_click_count,
            dead_click_count,
            heatmap_entropy,
            double_click_rate,
        ])

    def _extract_scroll_features(self, events: list[Event]) -> np.ndarray:
        """Extract scroll behavior features (4 features)."""
        scroll_events = [e for e in events if e.type == "scroll"]

        if not scroll_events:
            return np.zeros(4)

        # Max scroll depth (% of page)
        scroll_depth_max = self._calculate_scroll_depth(scroll_events)

        # Scroll reversal count
        scroll_reversal_count = self._count_scroll_reversals(scroll_events)

        # Scroll speed variance
        scroll_speed_variance = self._calculate_scroll_speed_variance(scroll_events)

        # Reading pause count: scroll stops > 1.5s
        reading_pause_count = self._count_reading_pauses(scroll_events)

        return np.array([
            scroll_depth_max,
            scroll_reversal_count,
            scroll_speed_variance,
            reading_pause_count,
        ])

    def _extract_dwell_features(self, events: list[Event]) -> np.ndarray:
        """Extract session dwell features (4 features)."""
        if not events:
            return np.zeros(4)

        # Total session duration
        total_duration = events[-1].timestamp - events[0].timestamp

        # Active engagement ratio (events > threshold)
        active_events = [e for e in events if e.type not in ("exit_intent", "idle")]
        active_engagement_ratio = len(active_events) / max(len(events), 1)

        # Tab switch count
        tab_switch_count = sum(1 for e in events if e.type == "exit_intent")

        # Form abandonment count
        form_abandon_count = self._count_form_abandonments(events)

        return np.array([
            total_duration,
            active_engagement_ratio,
            tab_switch_count,
            form_abandon_count,
        ])

    def _extract_combined_features(self, events: list[Event]) -> np.ndarray:
        """Extract combined behavioral features (8 features)."""
        if not events:
            return np.zeros(8)

        total_duration = events[-1].timestamp - events[0].timestamp

        # Total events and rate
        total_events = len(events)
        events_per_second = total_events / max(total_duration, 1)

        # Mouse-click ratio
        mouse_events = sum(1 for e in events if e.type == "mouse_move")
        click_events = sum(1 for e in events if e.type == "click")
        mouse_click_ratio = click_events / max(mouse_events, 1)

        # Scroll-click ratio
        scroll_events = sum(1 for e in events if e.type == "scroll")
        scroll_click_ratio = click_events / max(scroll_events, 1)

        # Idle periods
        idle_periods = self._count_idle_periods(events)

        # Burst activity count (high-frequency event clusters)
        burst_activity_count = self._count_burst_activities(events)

        # Form interaction duration
        form_interaction_duration = self._calculate_form_interaction_duration(events)

        # CTA click count
        cta_count = sum(
            1 for e in events
            if e.type == "click" and self._is_cta_selector(e.target_selector)
        )

        return np.array([
            total_events,
            events_per_second,
            mouse_click_ratio,
            scroll_click_ratio,
            idle_periods,
            burst_activity_count,
            form_interaction_duration,
            cta_count,
        ])

    # ── Helper Methods ────────────────────────────────────────────────

    def _count_direction_changes(self, mouse_events: list[Event]) -> int:
        """Count direction changes in mouse movement."""
        count = 0
        for i in range(2, len(mouse_events)):
            prev2 = mouse_events[i - 2]
            prev1 = mouse_events[i - 1]
            curr = mouse_events[i]

            if None in (prev2.x, prev1.x, curr.x):
                continue

            # Calculate directions
            dir1 = math.atan2(prev1.y - prev2.y, prev1.x - prev2.x)
            dir2 = math.atan2(curr.y - prev1.y, curr.x - prev1.x)

            # Check if direction changed significantly (>45 degrees)
            angle_diff = abs(dir2 - dir1)
            if angle_diff > math.pi / 4:
                count += 1

        return count

    def _calculate_hover_duration(
        self, mouse_events: list[Event], cta_selectors: list[str]
    ) -> float:
        """Calculate total hover duration on CTA elements."""
        total_hover_time = 0
        cta_patterns = [re.compile(selector, re.IGNORECASE) for selector in cta_selectors]

        for event in mouse_events:
            if event.target_selector:
                is_cta = any(pattern.search(event.target_selector) for pattern in cta_patterns)
                if is_cta:
                    # Approximate hover time by time to next mouse event
                    total_hover_time += self.window_seconds

        return total_hover_time * 1000  # Convert to ms

    def _calculate_idle_ratio(self, mouse_events: list[Event]) -> float:
        """Calculate ratio of time cursor is idle."""
        if len(mouse_events) < 2:
            return 0.0

        idle_time = 0
        total_time = 0

        for i in range(1, len(mouse_events)):
            dt = mouse_events[i].timestamp - mouse_events[i - 1].timestamp
            total_time += dt
            # Consider idle if gap > 2 seconds
            if dt > 2.0:
                idle_time += dt

        return idle_time / max(total_time, 1)

    def _calculate_backtrack_ratio(self, mouse_events: list[Event]) -> float:
        """Calculate ratio of leftward/upward movement (backtracking)."""
        backtrack_steps = 0
        total_steps = 0

        for i in range(1, len(mouse_events)):
            prev = mouse_events[i - 1]
            curr = mouse_events[i]

            if None in (prev.x, prev.y, curr.x, curr.y):
                continue

            dx = curr.x - prev.x
            dy = curr.y - prev.y

            # Leftward or upward movement
            if dx < 0 or dy < 0:
                backtrack_steps += 1
            total_steps += 1

        return backtrack_steps / max(total_steps, 1)

    def _count_rage_clicks(self, click_events: list[Event]) -> int:
        """Count rage clicks (3+ clicks on same element within 2s)."""
        rage_count = 0
        element_clicks = defaultdict(list)

        for event in click_events:
            selector = event.target_selector or "unknown"
            element_clicks[selector].append(event.timestamp)

        for selector, timestamps in element_clicks.items():
            if len(timestamps) >= 3:
                # Check if they occurred within 2 seconds
                if timestamps[-1] - timestamps[0] < 2.0:
                    rage_count += 1

        return rage_count

    def _count_dead_clicks(self, click_events: list[Event], all_events: list[Event]) -> int:
        """Count dead clicks (clicks with no subsequent page event)."""
        dead_count = 0

        # Find page navigation events
        page_events = set(e.timestamp for e in all_events if e.type in ("page_view", "navigate"))

        for event in click_events:
            # If no page event occurred within 5 seconds, consider dead
            has_page_event = any(
                page_time > event.timestamp and page_time - event.timestamp < 5
                for page_time in page_events
            )
            if not has_page_event:
                dead_count += 1

        return dead_count

    def _calculate_click_heatmap_entropy(self, click_events: list[Event]) -> float:
        """Calculate entropy of click distribution (spread vs concentration)."""
        if not click_events:
            return 0.0

        # Create spatial grid (10x10)
        grid_size = 10
        grid = np.zeros((grid_size, grid_size))

        for event in click_events:
            if event.x is not None and event.y is not None:
                # Normalize to grid
                gx = int((event.x / 100.0) * grid_size) % grid_size
                gy = int((event.y / 100.0) * grid_size) % grid_size
                grid[gy, gx] += 1

        # Normalize to probabilities
        total = np.sum(grid)
        if total == 0:
            return 0.0

        probs = grid / total
        probs = probs[probs > 0]  # Filter zeros for log

        # Calculate entropy
        entropy = -np.sum(probs * np.log2(probs + 1e-10))

        # Normalize to 0-1 range
        max_entropy = np.log2(min(100, np.count_nonzero(grid)))
        return entropy / max(max_entropy, 1)

    def _calculate_double_click_rate(self, click_events: list[Event]) -> float:
        """Calculate rate of double clicks."""
        double_clicks = 0
        total_clicks = len(click_events)

        for i in range(1, len(click_events)):
            prev = click_events[i - 1]
            curr = click_events[i]

            if (curr.timestamp - prev.timestamp) < 0.5 and prev.target_selector == curr.target_selector:
                double_clicks += 1

        return double_clicks / max(total_clicks, 1)

    def _calculate_scroll_depth(self, scroll_events: list[Event]) -> float:
        """Calculate maximum scroll depth as percentage."""
        if not scroll_events:
            return 0.0

        max_scroll = 0
        for event in scroll_events:
            metadata = event.metadata or {}
            scroll_pct = metadata.get("viewport_pct", 0)
            if isinstance(scroll_pct, (int, float)):
                max_scroll = max(max_scroll, scroll_pct / 100.0)

        return min(max_scroll, 1.0)

    def _count_scroll_reversals(self, scroll_events: list[Event]) -> int:
        """Count scroll direction reversals."""
        reversals = 0
        prev_direction = None

        for event in scroll_events:
            metadata = event.metadata or {}
            direction = metadata.get("direction")

            if prev_direction and direction and direction != prev_direction:
                reversals += 1
            prev_direction = direction

        return reversals

    def _calculate_scroll_speed_variance(self, scroll_events: list[Event]) -> int:
        """Calculate variance in scroll speed."""
        if len(scroll_events) < 2:
            return 0.0

        speeds = []
        for i in range(1, len(scroll_events)):
            dt = scroll_events[i].timestamp - scroll_events[i - 1].timestamp
            if dt > 0:
                metadata = scroll_events[i].metadata or {}
                delta = abs(metadata.get("delta", 0))
                speeds.append(delta / dt)

        if not speeds:
            return 0.0

        return np.var(speeds)

    def _count_reading_pauses(self, scroll_events: list[Event]) -> int:
        """Count reading pauses (scroll stops > 1.5s)."""
        pauses = 0
        prev_time = None

        for event in scroll_events:
            if prev_time and (event.timestamp - prev_time) > 1.5:
                pauses += 1
            prev_time = event.timestamp

        return pauses

    def _count_form_abandonments(self, events: list[Event]) -> int:
        """Count form abandonments."""
        abandonments = 0
        in_form = False
        form_element = None

        for event in events:
            if event.type == "focus":
                if self._is_form_element(event.target_selector):
                    in_form = True
                    form_element = event.target_selector
            elif event.type == "blur":
                if in_form and event.target_selector == form_element:
                    in_form = False
            elif event.type == "exit_intent":
                if in_form:
                    abandonments += 1
                    in_form = False

        return abandonments

    def _count_idle_periods(self, events: list[Event]) -> int:
        """Count idle periods (>3s gaps)."""
        idle_count = 0

        for i in range(1, len(events)):
            gap = events[i].timestamp - events[i - 1].timestamp
            if gap > 3.0:
                idle_count += 1

        return idle_count

    def _count_burst_activities(self, events: list[Event]) -> int:
        """Count burst activity clusters (5+ events in 1s)."""
        bursts = 0
        i = 0

        while i < len(events) - 4:
            # Check if 5 events occur within 1 second
            if events[i + 4].timestamp - events[i].timestamp < 1.0:
                bursts += 1
                i += 5  # Skip past this burst
            else:
                i += 1

        return bursts

    def _calculate_form_interaction_duration(self, events: list[Event]) -> float:
        """Calculate total time spent interacting with forms."""
        total_duration = 0
        in_form = False
        form_enter_time = 0

        for event in events:
            if event.type == "focus":
                if self._is_form_element(event.target_selector):
                    in_form = True
                    form_enter_time = event.timestamp
            elif event.type == "blur":
                if in_form and self._is_form_element(event.target_selector):
                    in_form = False
                    total_duration += event.timestamp - form_enter_time

        return total_duration

    def _is_cta_selector(self, selector: str | None) -> bool:
        """Check if selector matches CTA elements."""
        if not selector:
            return False
        cta_keywords = ["button", "cta", "checkout", "buy", "submit", "add-to-cart"]
        selector_lower = selector.lower()
        return any(keyword in selector_lower for keyword in cta_keywords)

    def _is_form_element(self, selector: str | None) -> bool:
        """Check if selector matches form elements."""
        if not selector:
            return False
        form_keywords = ["input", "textarea", "select", "form"]
        selector_lower = selector.lower()
        return any(keyword in selector_lower for keyword in form_keywords)
