#!/usr/bin/env python3
"""
M10 Observability Validation Suite

Comprehensive validation with integrations:
- Prometheus: Metrics for Grafana dashboards
- Alertmanager: Alert on failures
- PostHog: Analytics tracking
- Resend: Email alerts for critical failures
- Trigger.dev: Job scheduling (optional)

Test Scenarios with Cause → Effect → Expected vs Actual validation.

Usage:
    python -m scripts.ops.m10_observability_validation --full
    python -m scripts.ops.m10_observability_validation --scenarios
    python -m scripts.ops.m10_observability_validation --daemon --interval 300
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("m10.observability")

# ============================================================================
# Configuration
# ============================================================================


@dataclass
class Config:
    """Configuration from environment."""

    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", ""))

    # Prometheus
    prometheus_pushgateway: str = field(
        default_factory=lambda: os.getenv(
            "PROMETHEUS_PUSHGATEWAY", "http://localhost:9091"
        )
    )

    # Alertmanager
    alertmanager_url: str = field(
        default_factory=lambda: os.getenv("ALERTMANAGER_URL", "http://localhost:9093")
    )

    # PostHog
    posthog_api_key: str = field(
        default_factory=lambda: os.getenv("POSTHOG_API_KEY", "")
    )
    posthog_host: str = field(
        default_factory=lambda: os.getenv("POSTHOG_HOST", "https://us.posthog.com")
    )

    # Resend
    resend_api_key: str = field(default_factory=lambda: os.getenv("RESEND_API_KEY", ""))
    alert_email_to: str = field(
        default_factory=lambda: os.getenv("ALERT_EMAIL_TO", "admin1@agenticverz.com")
    )
    alert_email_from: str = field(
        default_factory=lambda: os.getenv("ALERT_EMAIL_FROM", "alerts@agenticverz.com")
    )

    # Trigger.dev
    trigger_api_key: str = field(
        default_factory=lambda: os.getenv("TRIGGER_API_KEY", "")
    )

    # Vault for secrets
    vault_addr: str = field(
        default_factory=lambda: os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    )
    vault_token: str = field(default_factory=lambda: os.getenv("VAULT_TOKEN", ""))


# ============================================================================
# Test Scenario Framework
# ============================================================================


class TestResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class ValidationScenario:
    """A test scenario with cause, effect, and expected vs actual."""

    name: str
    cause: str  # What action triggers the test
    expected_effect: str  # What should happen
    actual_effect: str = ""  # What actually happened
    expected_result: Any = None
    actual_result: Any = None
    result: TestResult = TestResult.SKIP
    latency_ms: float = 0.0
    error: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ValidationReport:
    """Full validation report."""

    run_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    scenarios: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    overall_result: TestResult = TestResult.SKIP

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "scenarios": [asdict(s) for s in self.scenarios],
            "metrics": self.metrics,
            "overall_result": self.overall_result.value,
            "summary": {
                "total": len(self.scenarios),
                "passed": sum(1 for s in self.scenarios if s.result == TestResult.PASS),
                "failed": sum(1 for s in self.scenarios if s.result == TestResult.FAIL),
                "errors": sum(
                    1 for s in self.scenarios if s.result == TestResult.ERROR
                ),
            },
        }


# ============================================================================
# Prometheus Integration
# ============================================================================


class PrometheusMetrics:
    """Push metrics to Prometheus Pushgateway."""

    def __init__(self, pushgateway_url: str):
        self.pushgateway_url = pushgateway_url
        self.metrics = []

    def gauge(self, name: str, value: float, labels: dict = None):
        """Add a gauge metric."""
        label_str = ""
        if labels:
            label_str = "{" + ",".join(f'{k}="{v}"' for k, v in labels.items()) + "}"
        self.metrics.append(f"{name}{label_str} {value}")

    def counter(self, name: str, value: float, labels: dict = None):
        """Add a counter metric."""
        self.gauge(name, value, labels)  # Same format for pushgateway

    async def push(self, job: str = "m10_validation") -> bool:
        """Push all metrics to Pushgateway."""
        if not self.metrics:
            return True

        try:
            import aiohttp

            body = "\n".join(self.metrics) + "\n"
            url = f"{self.pushgateway_url}/metrics/job/{job}"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=body) as resp:
                    if resp.status in (200, 202):
                        logger.info(f"Pushed {len(self.metrics)} metrics to Prometheus")
                        return True
                    else:
                        logger.warning(f"Prometheus push failed: {resp.status}")
                        return False
        except Exception as e:
            logger.warning(f"Prometheus push error: {e}")
            return False


# ============================================================================
# Alertmanager Integration
# ============================================================================


class AlertmanagerClient:
    """Send alerts to Alertmanager."""

    def __init__(self, alertmanager_url: str):
        self.alertmanager_url = alertmanager_url

    async def fire_alert(
        self,
        alertname: str,
        severity: str,
        summary: str,
        description: str,
        labels: dict = None,
    ) -> bool:
        """Fire an alert to Alertmanager."""
        try:
            import aiohttp

            alert = {
                "labels": {
                    "alertname": alertname,
                    "severity": severity,
                    "service": "m10_validation",
                    **(labels or {}),
                },
                "annotations": {"summary": summary, "description": description},
                "generatorURL": "http://localhost:8000/admin/validation",
            }

            url = f"{self.alertmanager_url}/api/v2/alerts"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=[alert]) as resp:
                    if resp.status in (200, 202):
                        logger.info(f"Alert fired: {alertname} ({severity})")
                        return True
                    else:
                        logger.warning(f"Alert failed: {resp.status}")
                        return False
        except Exception as e:
            logger.warning(f"Alertmanager error: {e}")
            return False


# ============================================================================
# PostHog Integration
# ============================================================================


class PostHogTracker:
    """Track events to PostHog."""

    def __init__(self, api_key: str, host: str):
        self.api_key = api_key
        self.host = host

    async def capture(
        self,
        event: str,
        properties: dict = None,
        distinct_id: str = "m10_validation_system",
    ) -> bool:
        """Capture an event."""
        if not self.api_key:
            logger.debug("PostHog API key not configured, skipping")
            return False

        try:
            import aiohttp

            payload = {
                "api_key": self.api_key,
                "event": event,
                "properties": {
                    "$lib": "m10_observability",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **(properties or {}),
                },
                "distinct_id": distinct_id,
            }

            url = f"{self.host}/capture/"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status in (200, 202):
                        logger.info(f"PostHog event captured: {event}")
                        return True
                    else:
                        logger.warning(f"PostHog capture failed: {resp.status}")
                        return False
        except Exception as e:
            logger.warning(f"PostHog error: {e}")
            return False


# ============================================================================
# Resend Email Integration
# ============================================================================


class ResendEmailer:
    """Send email alerts via Resend."""

    def __init__(self, api_key: str, from_email: str, to_email: str):
        self.api_key = api_key
        self.from_email = from_email
        self.to_email = to_email

    async def send_alert(self, subject: str, html_body: str) -> bool:
        """Send an email alert."""
        if not self.api_key:
            logger.debug("Resend API key not configured, skipping")
            return False

        try:
            import aiohttp

            payload = {
                "from": self.from_email,
                "to": [self.to_email],
                "subject": subject,
                "html": html_body,
            }

            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status in (200, 201):
                        logger.info(f"Email sent: {subject}")
                        return True
                    else:
                        body = await resp.text()
                        logger.warning(f"Resend failed: {resp.status} - {body}")
                        return False
        except Exception as e:
            logger.warning(f"Resend error: {e}")
            return False


# ============================================================================
# Trigger.dev Integration
# ============================================================================


class TriggerDevClient:
    """Interact with Trigger.dev for job scheduling."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def trigger_job(self, job_id: str, payload: dict = None) -> bool:
        """Trigger a job on Trigger.dev."""
        if not self.api_key:
            logger.debug("Trigger.dev API key not configured, skipping")
            return False

        try:
            import aiohttp

            url = f"https://api.trigger.dev/api/v1/jobs/{job_id}/invoke"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload or {}, headers=headers
                ) as resp:
                    if resp.status in (200, 201, 202):
                        logger.info(f"Trigger.dev job invoked: {job_id}")
                        return True
                    else:
                        logger.warning(f"Trigger.dev failed: {resp.status}")
                        return False
        except Exception as e:
            logger.warning(f"Trigger.dev error: {e}")
            return False


# ============================================================================
# Validation Scenarios
# ============================================================================


class ValidationSuite:
    """Run validation scenarios and report results."""

    def __init__(self, config: Config):
        self.config = config
        self.report = ValidationReport()

        # Initialize integrations
        self.prometheus = PrometheusMetrics(config.prometheus_pushgateway)
        self.alertmanager = AlertmanagerClient(config.alertmanager_url)
        self.posthog = PostHogTracker(config.posthog_api_key, config.posthog_host)
        self.resend = ResendEmailer(
            config.resend_api_key, config.alert_email_from, config.alert_email_to
        )
        self.trigger = TriggerDevClient(config.trigger_api_key)

    async def scenario_neon_write_read(self) -> ValidationScenario:
        """Scenario: Write to Neon and read back."""
        scenario = ValidationScenario(
            name="neon_write_read",
            cause="Insert a test record into failure_matches table",
            expected_effect="Record is persisted and can be read back with matching values",
        )

        try:
            import asyncpg

            start = time.time()
            conn = await asyncpg.connect(self.config.database_url, ssl="require")

            # Write
            test_id = f"obs_test_{uuid.uuid4().hex[:8]}"
            row_id = await conn.fetchval(
                """
                INSERT INTO failure_matches (
                    run_id, error_code, match_type, confidence_score, created_at
                ) VALUES ($1, 'OBS_TEST', 'observability', 0.99, NOW())
                RETURNING id
            """,
                test_id,
            )

            # Read back
            row = await conn.fetchrow(
                """
                SELECT run_id, error_code, confidence_score FROM failure_matches WHERE id = $1
            """,
                row_id,
            )

            # Cleanup
            await conn.execute("DELETE FROM failure_matches WHERE id = $1", row_id)
            await conn.close()

            scenario.latency_ms = (time.time() - start) * 1000
            scenario.expected_result = {
                "run_id": test_id,
                "error_code": "OBS_TEST",
                "confidence": 0.99,
            }
            scenario.actual_result = {
                "run_id": row["run_id"],
                "error_code": row["error_code"],
                "confidence": float(row["confidence_score"]),
            }

            if (
                row["run_id"] == test_id
                and row["error_code"] == "OBS_TEST"
                and abs(row["confidence_score"] - 0.99) < 0.01
            ):
                scenario.result = TestResult.PASS
                scenario.actual_effect = f"Record persisted and retrieved successfully in {scenario.latency_ms:.0f}ms"
            else:
                scenario.result = TestResult.FAIL
                scenario.actual_effect = "Data mismatch between written and read values"

        except Exception as e:
            scenario.result = TestResult.ERROR
            scenario.error = str(e)
            scenario.actual_effect = f"Exception: {e}"

        return scenario

    async def scenario_neon_referential_integrity(self) -> ValidationScenario:
        """Scenario: Test foreign key constraints work."""
        scenario = ValidationScenario(
            name="neon_referential_integrity",
            cause="Insert failure_match, then recovery_candidate referencing it",
            expected_effect="Both records created with valid FK relationship",
        )

        try:
            import asyncpg

            start = time.time()
            conn = await asyncpg.connect(self.config.database_url, ssl="require")

            # Create parent record
            test_id = f"fk_test_{uuid.uuid4().hex[:8]}"
            fm_id = await conn.fetchval(
                """
                INSERT INTO failure_matches (
                    run_id, error_code, match_type, confidence_score
                ) VALUES ($1, 'FK_TEST', 'fk_test', 0.5)
                RETURNING id
            """,
                test_id,
            )

            # Create child record with FK
            rc_id = await conn.fetchval(
                """
                INSERT INTO recovery_candidates (
                    failure_match_id, suggestion, confidence, decision, source
                ) VALUES ($1, 'FK test suggestion', 0.8, 'pending', 'fk_test')
                RETURNING id
            """,
                fm_id,
            )

            # Verify JOIN works
            join_result = await conn.fetchval(
                """
                SELECT COUNT(*) FROM recovery_candidates rc
                JOIN failure_matches fm ON rc.failure_match_id = fm.id
                WHERE fm.id = $1
            """,
                fm_id,
            )

            # Cleanup (child first due to FK)
            await conn.execute("DELETE FROM recovery_candidates WHERE id = $1", rc_id)
            await conn.execute("DELETE FROM failure_matches WHERE id = $1", fm_id)
            await conn.close()

            scenario.latency_ms = (time.time() - start) * 1000
            scenario.expected_result = {"join_count": 1}
            scenario.actual_result = {"join_count": join_result}

            if join_result == 1:
                scenario.result = TestResult.PASS
                scenario.actual_effect = "FK relationship maintained, JOIN successful"
            else:
                scenario.result = TestResult.FAIL
                scenario.actual_effect = f"Expected 1 joined record, got {join_result}"

        except Exception as e:
            scenario.result = TestResult.ERROR
            scenario.error = str(e)
            scenario.actual_effect = f"Exception: {e}"

        return scenario

    async def scenario_neon_latency_threshold(self) -> ValidationScenario:
        """Scenario: Verify write latency is under threshold."""
        scenario = ValidationScenario(
            name="neon_latency_threshold",
            cause="Measure round-trip write latency to Neon",
            expected_effect="Latency under 3000ms (serverless acceptable)",
        )

        LATENCY_THRESHOLD_MS = 3000

        try:
            import asyncpg

            conn = await asyncpg.connect(self.config.database_url, ssl="require")

            # Measure latency over 3 writes
            latencies = []
            for i in range(3):
                start = time.time()
                test_id = f"lat_test_{uuid.uuid4().hex[:8]}"
                row_id = await conn.fetchval(
                    """
                    INSERT INTO failure_matches (
                        run_id, error_code, match_type, confidence_score
                    ) VALUES ($1, 'LATENCY_TEST', 'latency', 0.0)
                    RETURNING id
                """,
                    test_id,
                )
                await conn.execute("DELETE FROM failure_matches WHERE id = $1", row_id)
                latencies.append((time.time() - start) * 1000)

            await conn.close()

            avg_latency = sum(latencies) / len(latencies)
            scenario.latency_ms = avg_latency
            scenario.expected_result = {
                "threshold_ms": LATENCY_THRESHOLD_MS,
                "condition": "under",
            }
            scenario.actual_result = {
                "avg_latency_ms": round(avg_latency, 2),
                "samples": [round(l, 2) for l in latencies],
            }

            if avg_latency < LATENCY_THRESHOLD_MS:
                scenario.result = TestResult.PASS
                scenario.actual_effect = f"Average latency {avg_latency:.0f}ms is under {LATENCY_THRESHOLD_MS}ms threshold"
            else:
                scenario.result = TestResult.FAIL
                scenario.actual_effect = f"Average latency {avg_latency:.0f}ms exceeds {LATENCY_THRESHOLD_MS}ms threshold"

        except Exception as e:
            scenario.result = TestResult.ERROR
            scenario.error = str(e)
            scenario.actual_effect = f"Exception: {e}"

        return scenario

    async def scenario_redis_stream_operations(self) -> ValidationScenario:
        """Scenario: Test Redis stream write/read."""
        scenario = ValidationScenario(
            name="redis_stream_operations",
            cause="Write message to Redis stream, read it back",
            expected_effect="Message persisted in stream and retrievable",
        )

        try:
            import redis.asyncio as redis

            start = time.time()
            client = redis.from_url(self.config.redis_url)

            stream_key = "obs_test:stream"
            test_data = {
                "test_id": uuid.uuid4().hex[:8],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Write to stream
            msg_id = await client.xadd(stream_key, test_data)

            # Read back
            messages = await client.xrange(stream_key, min=msg_id, max=msg_id)

            # Cleanup
            await client.xdel(stream_key, msg_id)
            await client.aclose()

            scenario.latency_ms = (time.time() - start) * 1000
            scenario.expected_result = {"message_count": 1, "data_matches": True}

            if messages and len(messages) == 1:
                retrieved_data = {
                    k.decode(): v.decode() for k, v in messages[0][1].items()
                }
                data_matches = retrieved_data.get("test_id") == test_data["test_id"]
                scenario.actual_result = {
                    "message_count": 1,
                    "data_matches": data_matches,
                }

                if data_matches:
                    scenario.result = TestResult.PASS
                    scenario.actual_effect = (
                        "Stream message written and read back successfully"
                    )
                else:
                    scenario.result = TestResult.FAIL
                    scenario.actual_effect = "Data mismatch in stream message"
            else:
                scenario.actual_result = {
                    "message_count": len(messages) if messages else 0
                }
                scenario.result = TestResult.FAIL
                scenario.actual_effect = (
                    f"Expected 1 message, got {len(messages) if messages else 0}"
                )

        except Exception as e:
            scenario.result = TestResult.ERROR
            scenario.error = str(e)
            scenario.actual_effect = f"Exception: {e}"

        return scenario

    async def scenario_redis_hash_operations(self) -> ValidationScenario:
        """Scenario: Test Redis hash CRUD operations."""
        scenario = ValidationScenario(
            name="redis_hash_operations",
            cause="Create, read, update, delete hash fields",
            expected_effect="All CRUD operations succeed",
        )

        try:
            import redis.asyncio as redis

            start = time.time()
            client = redis.from_url(self.config.redis_url)

            hash_key = f"obs_test:hash:{uuid.uuid4().hex[:8]}"

            # Create
            await client.hset(hash_key, mapping={"field1": "value1", "counter": "0"})

            # Read
            val1 = await client.hget(hash_key, "field1")

            # Update (increment)
            new_counter = await client.hincrby(hash_key, "counter", 5)

            # Read all
            all_fields = await client.hgetall(hash_key)

            # Delete
            await client.delete(hash_key)

            # Verify deleted
            exists = await client.exists(hash_key)

            await client.aclose()

            scenario.latency_ms = (time.time() - start) * 1000
            scenario.expected_result = {
                "create": "success",
                "read_field1": "value1",
                "increment_result": 5,
                "deleted": True,
            }
            scenario.actual_result = {
                "read_field1": val1.decode() if val1 else None,
                "increment_result": new_counter,
                "field_count": len(all_fields),
                "deleted": exists == 0,
            }

            if val1 and val1.decode() == "value1" and new_counter == 5 and exists == 0:
                scenario.result = TestResult.PASS
                scenario.actual_effect = "All hash CRUD operations successful"
            else:
                scenario.result = TestResult.FAIL
                scenario.actual_effect = "One or more hash operations failed"

        except Exception as e:
            scenario.result = TestResult.ERROR
            scenario.error = str(e)
            scenario.actual_effect = f"Exception: {e}"

        return scenario

    async def scenario_redis_latency(self) -> ValidationScenario:
        """Scenario: Verify Redis latency is acceptable."""
        scenario = ValidationScenario(
            name="redis_latency",
            cause="Measure Redis ping latency",
            expected_effect="Latency under 500ms",
        )

        LATENCY_THRESHOLD_MS = 500

        try:
            import redis.asyncio as redis

            client = redis.from_url(self.config.redis_url)

            # Measure latency over 5 pings
            latencies = []
            for _ in range(5):
                start = time.time()
                await client.ping()
                latencies.append((time.time() - start) * 1000)

            await client.aclose()

            avg_latency = sum(latencies) / len(latencies)
            scenario.latency_ms = avg_latency
            scenario.expected_result = {"threshold_ms": LATENCY_THRESHOLD_MS}
            scenario.actual_result = {
                "avg_latency_ms": round(avg_latency, 2),
                "samples": [round(l, 2) for l in latencies],
            }

            if avg_latency < LATENCY_THRESHOLD_MS:
                scenario.result = TestResult.PASS
                scenario.actual_effect = f"Average latency {avg_latency:.0f}ms under {LATENCY_THRESHOLD_MS}ms"
            else:
                scenario.result = TestResult.FAIL
                scenario.actual_effect = (
                    f"Average latency {avg_latency:.0f}ms exceeds threshold"
                )

        except Exception as e:
            scenario.result = TestResult.ERROR
            scenario.error = str(e)
            scenario.actual_effect = f"Exception: {e}"

        return scenario

    async def scenario_api_health(self) -> ValidationScenario:
        """Scenario: Verify API health endpoint."""
        scenario = ValidationScenario(
            name="api_health",
            cause="Call /health endpoint",
            expected_effect="Returns 200 with status=healthy",
        )

        try:
            import aiohttp

            start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/health") as resp:
                    status_code = resp.status
                    body = await resp.json()

            scenario.latency_ms = (time.time() - start) * 1000
            scenario.expected_result = {"status_code": 200, "body_status": "healthy"}
            scenario.actual_result = {
                "status_code": status_code,
                "body_status": body.get("status"),
            }

            if status_code == 200 and body.get("status") == "healthy":
                scenario.result = TestResult.PASS
                scenario.actual_effect = "API health check passed"
            else:
                scenario.result = TestResult.FAIL
                scenario.actual_effect = f"Health check failed: {status_code}, {body}"

        except Exception as e:
            scenario.result = TestResult.ERROR
            scenario.error = str(e)
            scenario.actual_effect = f"Exception: {e}"

        return scenario

    async def scenario_api_capabilities(self) -> ValidationScenario:
        """Scenario: Verify API returns capabilities."""
        scenario = ValidationScenario(
            name="api_capabilities",
            cause="Call /api/v1/runtime/capabilities",
            expected_effect="Returns skills list with at least 5 skills",
        )

        try:
            import aiohttp

            start = time.time()
            api_key = os.getenv("AOS_API_KEY", "")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/api/v1/runtime/capabilities",
                    headers={"X-AOS-Key": api_key},  # Fixed: was X-API-Key
                ) as resp:
                    status_code = resp.status
                    body = await resp.json()

            scenario.latency_ms = (time.time() - start) * 1000
            skills = body.get("skills", {})
            skill_count = len(skills)

            scenario.expected_result = {"min_skills": 5}
            scenario.actual_result = {
                "skill_count": skill_count,
                "skills": list(skills.keys()),
            }

            if status_code == 200 and skill_count >= 5:
                scenario.result = TestResult.PASS
                scenario.actual_effect = f"API returned {skill_count} skills"
            else:
                scenario.result = TestResult.FAIL
                scenario.actual_effect = f"Expected >=5 skills, got {skill_count}"

        except Exception as e:
            scenario.result = TestResult.ERROR
            scenario.error = str(e)
            scenario.actual_effect = f"Exception: {e}"

        return scenario

    async def run_all_scenarios(self) -> ValidationReport:
        """Run all validation scenarios."""
        scenarios = [
            self.scenario_neon_write_read,
            self.scenario_neon_referential_integrity,
            self.scenario_neon_latency_threshold,
            self.scenario_redis_stream_operations,
            self.scenario_redis_hash_operations,
            self.scenario_redis_latency,
            self.scenario_api_health,
            self.scenario_api_capabilities,
        ]

        for scenario_fn in scenarios:
            try:
                result = await scenario_fn()
                self.report.scenarios.append(result)
                logger.info(f"Scenario {result.name}: {result.result.value}")
            except Exception as e:
                logger.error(f"Scenario {scenario_fn.__name__} crashed: {e}")
                self.report.scenarios.append(
                    ValidationScenario(
                        name=scenario_fn.__name__,
                        cause="Run scenario",
                        expected_effect="Complete without crash",
                        actual_effect=f"Crashed: {e}",
                        result=TestResult.ERROR,
                        error=str(e),
                    )
                )

        # Determine overall result
        if any(
            s.result in (TestResult.FAIL, TestResult.ERROR)
            for s in self.report.scenarios
        ):
            self.report.overall_result = TestResult.FAIL
        elif all(s.result == TestResult.PASS for s in self.report.scenarios):
            self.report.overall_result = TestResult.PASS
        else:
            self.report.overall_result = TestResult.SKIP

        # Collect metrics
        self.report.metrics = {
            "neon_write_latency_ms": next(
                (
                    s.latency_ms
                    for s in self.report.scenarios
                    if s.name == "neon_latency_threshold"
                ),
                0,
            ),
            "redis_ping_latency_ms": next(
                (
                    s.latency_ms
                    for s in self.report.scenarios
                    if s.name == "redis_latency"
                ),
                0,
            ),
            "api_health_latency_ms": next(
                (s.latency_ms for s in self.report.scenarios if s.name == "api_health"),
                0,
            ),
        }

        return self.report

    async def push_metrics(self):
        """Push metrics to Prometheus."""
        summary = self.report.to_dict()["summary"]

        self.prometheus.gauge("m10_validation_scenarios_total", summary["total"])
        self.prometheus.gauge("m10_validation_scenarios_passed", summary["passed"])
        self.prometheus.gauge("m10_validation_scenarios_failed", summary["failed"])
        self.prometheus.gauge("m10_validation_scenarios_errors", summary["errors"])

        self.prometheus.gauge(
            "m10_validation_overall_success",
            1 if self.report.overall_result == TestResult.PASS else 0,
        )

        for name, value in self.report.metrics.items():
            self.prometheus.gauge(f"m10_{name}", value)

        await self.prometheus.push()

    async def fire_alerts_if_needed(self):
        """Fire alerts if validation failed."""
        if self.report.overall_result in (TestResult.FAIL, TestResult.ERROR):
            failed_scenarios = [
                s
                for s in self.report.scenarios
                if s.result in (TestResult.FAIL, TestResult.ERROR)
            ]

            # Alertmanager
            await self.alertmanager.fire_alert(
                alertname="M10ValidationFailed",
                severity="critical",
                summary=f"M10 validation failed: {len(failed_scenarios)} scenarios failed",
                description="\n".join(
                    f"- {s.name}: {s.actual_effect}" for s in failed_scenarios
                ),
            )

            # Resend email
            html_body = f"""
            <h2>M10 Validation Failed</h2>
            <p><strong>Run ID:</strong> {self.report.run_id}</p>
            <p><strong>Timestamp:</strong> {self.report.timestamp}</p>
            <h3>Failed Scenarios:</h3>
            <ul>
            {"".join(f"<li><strong>{s.name}</strong>: {s.actual_effect}</li>" for s in failed_scenarios)}
            </ul>
            <h3>Expected vs Actual:</h3>
            {"".join(f"<p><strong>{s.name}</strong><br>Expected: {s.expected_result}<br>Actual: {s.actual_result}</p>" for s in failed_scenarios)}
            """

            await self.resend.send_alert(
                subject=f"[CRITICAL] M10 Validation Failed - {len(failed_scenarios)} scenarios",
                html_body=html_body,
            )

    async def track_analytics(self):
        """Track validation event in PostHog."""
        summary = self.report.to_dict()["summary"]

        await self.posthog.capture(
            event="m10_validation_completed",
            properties={
                "run_id": self.report.run_id,
                "overall_result": self.report.overall_result.value,
                "scenarios_total": summary["total"],
                "scenarios_passed": summary["passed"],
                "scenarios_failed": summary["failed"],
                "neon_latency_ms": self.report.metrics.get("neon_write_latency_ms", 0),
                "redis_latency_ms": self.report.metrics.get("redis_ping_latency_ms", 0),
            },
        )


# ============================================================================
# Main
# ============================================================================


async def run_validation(
    config: Config,
    push_metrics: bool = True,
    fire_alerts: bool = True,
    track_analytics: bool = True,
) -> ValidationReport:
    """Run full validation suite with all integrations."""
    suite = ValidationSuite(config)

    # Run scenarios
    report = await suite.run_all_scenarios()

    # Push to integrations
    if push_metrics:
        await suite.push_metrics()

    if fire_alerts:
        await suite.fire_alerts_if_needed()

    if track_analytics:
        await suite.track_analytics()

    return report


async def run_daemon(config: Config, interval: int = 300):
    """Run validation in daemon mode."""
    logger.info(f"Starting observability validation daemon (interval={interval}s)")

    while True:
        try:
            report = await run_validation(config)
            logger.info(
                f"Validation cycle {report.run_id}: {report.overall_result.value}"
            )
        except Exception as e:
            logger.error(f"Daemon cycle error: {e}")

        await asyncio.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="M10 Observability Validation Suite")
    parser.add_argument(
        "--full", action="store_true", help="Run full validation with all integrations"
    )
    parser.add_argument(
        "--scenarios", action="store_true", help="Run scenarios only (no integrations)"
    )
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument(
        "--interval", type=int, default=300, help="Daemon interval (seconds)"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    config = Config()

    if not config.database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)

    async def run():
        if args.daemon:
            await run_daemon(config, args.interval)
        else:
            push = not args.scenarios
            report = await run_validation(
                config, push_metrics=push, fire_alerts=push, track_analytics=push
            )

            if args.json:
                print(json.dumps(report.to_dict(), indent=2, default=str))
            else:
                summary = report.to_dict()["summary"]
                print(f"\n{'=' * 60}")
                print("M10 Observability Validation Report")
                print(f"{'=' * 60}")
                print(f"Run ID: {report.run_id}")
                print(f"Timestamp: {report.timestamp}")
                print(f"Overall: {report.overall_result.value.upper()}")
                print(f"\nScenarios: {summary['passed']}/{summary['total']} passed")
                print(f"  - Passed: {summary['passed']}")
                print(f"  - Failed: {summary['failed']}")
                print(f"  - Errors: {summary['errors']}")

                print("\nScenario Details:")
                for s in report.scenarios:
                    status_icon = {
                        "pass": "[OK]",
                        "fail": "[FAIL]",
                        "error": "[ERR]",
                        "skip": "[SKIP]",
                    }[s.result.value]
                    print(f"  {status_icon} {s.name}")
                    print(f"       Cause: {s.cause}")
                    print(f"       Expected: {s.expected_effect}")
                    print(f"       Actual: {s.actual_effect}")
                    if s.latency_ms > 0:
                        print(f"       Latency: {s.latency_ms:.0f}ms")

                print("\nMetrics:")
                for name, value in report.metrics.items():
                    print(f"  {name}: {value:.2f}")

            sys.exit(0 if report.overall_result == TestResult.PASS else 1)

    asyncio.run(run())


if __name__ == "__main__":
    main()
