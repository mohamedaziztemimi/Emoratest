"""Load testing with Locust (CONV-44, CONV-46).

Simulates 500 concurrent users across all API surfaces:
- SDK event ingestion (high volume)
- Dashboard analytics (medium volume)
- Experiment management (low volume)
- Intervention recommendations (medium volume)

Performance targets:
    /events/batch          p95 < 200ms
    /dashboard/sessions    p95 < 500ms
    /interventions/recommend  p95 < 300ms
    /experiments           p95 < 400ms

Run:
    pip install locust
    cd backend
    locust -f tests/locustfile.py --host=http://localhost:8000

Then open http://localhost:8089 to configure and start the test.
"""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime

from locust import HttpUser, between, task


class SDKUser(HttpUser):
    """Simulates SDK traffic — high volume event ingestion."""

    wait_time = between(0.1, 0.5)
    weight = 8  # 80% of simulated users are SDK clients

    def on_start(self):
        self.sdk_key = f"test-key-{uuid.uuid4().hex[:8]}"
        self.session_id = str(uuid.uuid4())
        self.headers = {
            "X-SDK-Key": self.sdk_key,
            "Content-Type": "application/json",
        }

        # Create a session
        self.client.post(
            "/api/v1/sessions",
            json={
                "merchant_id": str(uuid.uuid4()),
                "page_url": f"https://shop-{random.randint(1, 100)}.com/product",
                "started_at": datetime.now(UTC).isoformat(),
                "device_type": random.choice(["desktop", "mobile", "tablet"]),
            },
            headers=self.headers,
            name="/api/v1/sessions [create]",
        )

    @task(10)
    def send_events(self):
        """Send a batch of behavioral events."""
        event_types = ["mouse_move", "click", "scroll", "exit_intent", "visibility"]
        events = []
        batch_size = random.randint(5, 50)

        for _ in range(batch_size):
            etype = random.choice(event_types)
            event = {
                "type": etype,
                "ts": datetime.now(UTC).isoformat(),
            }
            if etype in ("mouse_move", "click"):
                event["x"] = random.uniform(0, 1920)
                event["y"] = random.uniform(0, 1080)
            if etype == "mouse_move":
                event["velocity"] = random.uniform(0, 2000)
            events.append(event)

        self.client.post(
            "/api/v1/events/batch",
            json={"session_id": self.session_id, "events": events},
            headers=self.headers,
            name="/api/v1/events/batch",
        )

    @task(1)
    def end_session(self):
        """End the current session and start a new one."""
        self.client.put(
            f"/api/v1/sessions/{self.session_id}/end",
            headers=self.headers,
            name="/api/v1/sessions/{id}/end",
        )
        self.session_id = str(uuid.uuid4())


class DashboardUser(HttpUser):
    """Simulates dashboard traffic — lower volume analytics queries."""

    wait_time = between(1, 3)
    weight = 2  # 20% of simulated users are dashboard users

    def on_start(self):
        self.sdk_key = f"dash-key-{uuid.uuid4().hex[:8]}"
        self.headers = {
            "X-SDK-Key": self.sdk_key,
            "Content-Type": "application/json",
        }

    @task(5)
    def list_sessions(self):
        """Query paginated session list."""
        page = random.randint(1, 10)
        self.client.get(
            f"/api/v1/dashboard/sessions?page={page}&page_size=20",
            headers=self.headers,
            name="/api/v1/dashboard/sessions",
        )

    @task(3)
    def get_session_detail(self):
        """Fetch session detail."""
        session_id = str(uuid.uuid4())
        self.client.get(
            f"/api/v1/dashboard/sessions/{session_id}",
            headers=self.headers,
            name="/api/v1/dashboard/sessions/{id}",
        )

    @task(2)
    def friction_map(self):
        """Query friction map analytics."""
        self.client.get(
            "/api/v1/dashboard/analytics/friction-map?limit=50",
            headers=self.headers,
            name="/api/v1/dashboard/analytics/friction-map",
        )

    @task(1)
    def funnel(self):
        """Query conversion funnel."""
        self.client.get(
            "/api/v1/dashboard/analytics/funnel",
            headers=self.headers,
            name="/api/v1/dashboard/analytics/funnel",
        )

    @task(2)
    def cohort_analysis(self):
        """Query cohort analytics (CONV-40)."""
        dimension = random.choice(["device_type", "country_code", "outcome", "intent_label"])
        self.client.get(
            f"/api/v1/analytics/cohorts?dimension={dimension}",
            headers=self.headers,
            name="/api/v1/analytics/cohorts",
        )

    @task(1)
    def risk_distribution(self):
        """Query risk distribution (CONV-40)."""
        self.client.get(
            "/api/v1/analytics/risk-distribution?buckets=10",
            headers=self.headers,
            name="/api/v1/analytics/risk-distribution",
        )

    @task(3)
    def intervention_recommend(self):
        """Request intervention recommendations (CONV-39)."""
        session_id = str(uuid.uuid4())
        self.client.get(
            f"/api/v1/interventions/recommend/{session_id}",
            headers=self.headers,
            name="/api/v1/interventions/recommend/{id}",
        )

    @task(1)
    def intervention_stats(self):
        """Query intervention stats (CONV-39)."""
        self.client.get(
            "/api/v1/interventions/stats",
            headers=self.headers,
            name="/api/v1/interventions/stats",
        )

    @task(2)
    def list_experiments(self):
        """List experiments (CONV-38)."""
        self.client.get(
            "/api/v1/experiments?page=1&page_size=20",
            headers=self.headers,
            name="/api/v1/experiments",
        )

    @task(1)
    def merchant_usage(self):
        """Check merchant usage (CONV-43)."""
        self.client.get(
            "/api/v1/merchants/usage",
            headers=self.headers,
            name="/api/v1/merchants/usage",
        )
