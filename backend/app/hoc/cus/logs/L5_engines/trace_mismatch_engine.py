# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L4 handler)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: aos_trace_mismatches, aos_traces (via L6 driver)
#   Writes: aos_trace_mismatches (via L6 driver)
# Role: Business logic for trace mismatch operations (notifications, validation)
# Callers: L4 traces_handler.py (via registry dispatch)
# Allowed Imports: L5_schemas, L6_drivers
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy
# Reference: PIN-470, M8 Trace System, L2 first-principles purity migration
# artifact_class: CODE

"""
Trace Mismatch Engine (L5)

Business logic for trace mismatch operations.

This engine:
- Validates inputs and enforces tenant isolation
- Delegates DB operations to L6 driver
- Handles notifications (GitHub issues, Slack)
- Returns structured results for L4 handler

Usage:
    from app.hoc.cus.logs.L5_engines.trace_mismatch_engine import get_trace_mismatch_engine

    engine = get_trace_mismatch_engine(session)
    result = await engine.list_all_mismatches(window="24h", status="open", limit=100)
"""

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.hoc.cus.logs.L6_drivers.trace_mismatch_driver import (
    TraceMismatchDriver,
)

logger = logging.getLogger("nova.hoc.logs.trace_mismatch_engine")


@dataclass
class MismatchReportInput:
    """Input for reporting a mismatch."""
    trace_id: str
    step_index: int
    reason: str
    expected_hash: Optional[str] = None
    actual_hash: Optional[str] = None
    details: dict = field(default_factory=dict)


@dataclass
class NotificationResult:
    """Result of notification attempt."""
    channel: str  # "github", "slack", "none"
    issue_url: Optional[str] = None
    success: bool = False


class TraceMismatchEngine:
    """
    L5 engine for trace mismatch business logic.

    Handles:
    - Input validation
    - Tenant isolation enforcement
    - Notification dispatch (GitHub, Slack)
    - Result structuring
    """

    def __init__(self, driver: TraceMismatchDriver):
        self._driver = driver

    # =========================================================================
    # Mismatch Listing
    # =========================================================================

    async def list_all_mismatches(
        self,
        window: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        List all mismatches with optional filters.

        Args:
            window: Time window (e.g., "24h", "7d")
            status: Filter by status ("open" or "resolved")
            limit: Max results

        Returns:
            Dict with mismatches, summary counts, window info
        """
        # Parse window to datetime
        window_since = None
        if window:
            if window.endswith("h"):
                hours = int(window.rstrip("h"))
                window_since = datetime.now(timezone.utc) - timedelta(hours=hours)
            elif window.endswith("d"):
                days = int(window.rstrip("d"))
                window_since = datetime.now(timezone.utc) - timedelta(days=days)
            else:
                window_since = datetime.now(timezone.utc) - timedelta(hours=24)

        # Parse status filter
        resolved_filter = None
        if status == "resolved":
            resolved_filter = True
        elif status == "open":
            resolved_filter = False

        result = await self._driver.fetch_all_mismatches(
            window_since=window_since,
            resolved_filter=resolved_filter,
            limit=limit,
        )

        return {
            "mismatches": [
                {
                    "id": r["id"],
                    "trace_id": r["trace_id"],
                    "step_index": r["step_index"],
                    "reason": r["reason"],
                    "expected_hash": r["expected_hash"],
                    "actual_hash": r["actual_hash"],
                    "details": r["details"],
                    "status": "resolved" if r["resolved"] else "open",
                    "resolved_at": r["resolved_at"],
                    "detected_at": r["created_at"],
                }
                for r in result["rows"]
            ],
            "summary": {
                "open": result["open_count"],
                "resolved": result["resolved_count"],
            },
            "window": window,
            "total": len(result["rows"]),
        }

    async def list_trace_mismatches(
        self,
        trace_id: str,
        tenant_id: str,
        is_admin: bool = False,
    ) -> dict[str, Any]:
        """
        List all mismatches for a specific trace.

        Args:
            trace_id: Trace ID
            tenant_id: Caller's tenant ID
            is_admin: Whether caller has admin role

        Returns:
            Dict with trace_id, mismatches, total

        Raises:
            ValueError: If trace not found
            PermissionError: If tenant isolation violated
        """
        # Verify trace exists and check tenant access
        trace_tenant = await self._driver.fetch_trace_tenant(trace_id)
        if trace_tenant is None:
            raise ValueError(f"Trace {trace_id} not found")

        if trace_tenant != tenant_id and not is_admin:
            raise PermissionError("Access denied")

        mismatches = await self._driver.fetch_mismatches_for_trace(trace_id)

        return {
            "trace_id": trace_id,
            "mismatches": mismatches,
            "total": len(mismatches),
        }

    # =========================================================================
    # Report Mismatch
    # =========================================================================

    async def report_mismatch(
        self,
        input_data: MismatchReportInput,
        tenant_id: str,
        user_id: str,
        is_admin: bool = False,
    ) -> dict[str, Any]:
        """
        Report a replay mismatch.

        Args:
            input_data: Mismatch details
            tenant_id: Caller's tenant ID
            user_id: Reporting user ID
            is_admin: Whether caller has admin role

        Returns:
            Dict with mismatch_id, trace_id, status, notified, issue_url

        Raises:
            ValueError: If trace not found
            PermissionError: If tenant isolation violated
        """
        trace_id = input_data.trace_id

        # Verify trace exists and check tenant access
        trace_tenant = await self._driver.fetch_trace_tenant(trace_id)
        if trace_tenant is None:
            raise ValueError(f"Trace {trace_id} not found")

        if trace_tenant != tenant_id and not is_admin:
            raise PermissionError("Cannot report mismatch for other tenant's trace")

        # Generate mismatch ID
        mismatch_id = str(uuid.uuid4())

        # Insert mismatch record
        await self._driver.insert_mismatch(
            mismatch_id=mismatch_id,
            trace_id=trace_id,
            tenant_id=tenant_id,
            reported_by=user_id,
            step_index=input_data.step_index,
            reason=input_data.reason,
            expected_hash=input_data.expected_hash,
            actual_hash=input_data.actual_hash,
            details=input_data.details,
        )

        # Attempt notifications
        notification = await self._send_notification(
            trace_id=trace_id,
            step_index=input_data.step_index,
            reason=input_data.reason,
            user_id=user_id,
            tenant_id=tenant_id,
            expected_hash=input_data.expected_hash,
            actual_hash=input_data.actual_hash,
            details=input_data.details,
        )

        # Update mismatch with notification result
        if notification.issue_url:
            await self._driver.update_mismatch_issue_url(mismatch_id, notification.issue_url)
        elif notification.channel == "slack":
            await self._driver.update_mismatch_notification(mismatch_id)

        logger.info(
            f"Mismatch reported: trace={trace_id}, step={input_data.step_index}, "
            f"notified={notification.channel}"
        )

        return {
            "mismatch_id": mismatch_id,
            "trace_id": trace_id,
            "status": "recorded",
            "notified": notification.channel,
            "issue_url": notification.issue_url,
        }

    # =========================================================================
    # Resolve Mismatch
    # =========================================================================

    async def resolve_mismatch(
        self,
        trace_id: str,
        mismatch_id: str,
        user_id: str,
        resolution_note: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Mark a mismatch as resolved.

        Args:
            trace_id: Trace ID
            mismatch_id: Mismatch ID
            user_id: User resolving the mismatch
            resolution_note: Optional resolution note

        Returns:
            Dict with status, mismatch_id, resolved_by

        Raises:
            ValueError: If mismatch not found
        """
        row = await self._driver.resolve_mismatch(
            mismatch_id=mismatch_id,
            trace_id=trace_id,
            resolved_by=user_id,
        )

        if not row:
            raise ValueError("Mismatch not found")

        # If there's an associated GitHub issue, comment on it
        issue_url = row.get("issue_url")
        if issue_url and resolution_note:
            await self._comment_on_github_issue(issue_url, user_id, resolution_note)

        return {
            "status": "resolved",
            "mismatch_id": mismatch_id,
            "resolved_by": user_id,
        }

    # =========================================================================
    # Bulk Report
    # =========================================================================

    async def bulk_report_mismatches(
        self,
        mismatch_ids: list[str],
        user_id: str,
        github_issue: bool = True,
    ) -> dict[str, Any]:
        """
        Create a single GitHub issue for multiple mismatches.

        Args:
            mismatch_ids: List of mismatch IDs to link
            user_id: User creating the bulk report
            github_issue: Whether to create a GitHub issue

        Returns:
            Dict with linked_count, traces_affected, issue_url, mismatch_ids

        Raises:
            ValueError: If no mismatches found
        """
        # Fetch all mismatches
        rows = await self._driver.fetch_mismatches_by_ids(mismatch_ids)

        if not rows:
            raise ValueError("No mismatches found")

        # Group by trace_id
        by_trace: dict[str, list[dict]] = {}
        for r in rows:
            trace_id = r["trace_id"]
            if trace_id not in by_trace:
                by_trace[trace_id] = []
            by_trace[trace_id].append({
                "mismatch_id": r["id"],
                "step_index": r["step_index"],
                "reason": r["reason"],
                "expected_hash": r["expected_hash"],
                "actual_hash": r["actual_hash"],
            })

        issue_url = None

        if github_issue:
            issue_url = await self._create_bulk_github_issue(
                by_trace=by_trace,
                total_count=len(rows),
                user_id=user_id,
            )

            if issue_url:
                await self._driver.bulk_update_issue_url(mismatch_ids, issue_url)

        return {
            "linked_count": len(rows),
            "traces_affected": len(by_trace),
            "issue_url": issue_url,
            "mismatch_ids": [r["id"] for r in rows],
        }

    # =========================================================================
    # Notification Helpers
    # =========================================================================

    async def _send_notification(
        self,
        trace_id: str,
        step_index: int,
        reason: str,
        user_id: str,
        tenant_id: str,
        expected_hash: Optional[str],
        actual_hash: Optional[str],
        details: dict,
    ) -> NotificationResult:
        """
        Send notification to GitHub or Slack.

        Tries GitHub first, then Slack if GitHub not configured.
        """
        import httpx

        # Try GitHub issue creation
        github_token = os.getenv("GITHUB_TOKEN")
        github_repo = os.getenv("GITHUB_REPO")

        if github_token and github_repo:
            try:
                title = f"[Replay Mismatch] trace:{trace_id} step:{step_index}"
                body = f"""## Replay Mismatch Detected

**Trace ID:** `{trace_id}`
**Step Index:** {step_index}
**Reason:** {reason}
**Reported By:** {user_id}
**Tenant:** {tenant_id}

### Details
- Expected Hash: `{expected_hash or "N/A"}`
- Actual Hash: `{actual_hash or "N/A"}`

### Additional Details
```json
{details}
```

### Investigation
Run the following to inspect the trace:
```bash
curl -H "Authorization: Bearer $TOKEN" https://api.agenticverz.com/api/v1/traces/{trace_id}
```
"""
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"https://api.github.com/repos/{github_repo}/issues",
                        headers={
                            "Authorization": f"token {github_token}",
                            "Accept": "application/vnd.github.v3+json",
                        },
                        json={
                            "title": title,
                            "body": body,
                            "labels": ["replay-mismatch", "aos", "automated"],
                        },
                        timeout=10.0,
                    )
                    if resp.status_code in (200, 201):
                        issue_data = resp.json()
                        return NotificationResult(
                            channel="github",
                            issue_url=issue_data.get("html_url"),
                            success=True,
                        )
            except Exception as e:
                logger.warning(f"Failed to create GitHub issue: {e}")

        # Try Slack notification
        slack_webhook = os.getenv("SLACK_MISMATCH_WEBHOOK")
        if slack_webhook:
            try:
                message = {
                    "text": f"[Replay Mismatch] trace:{trace_id} step:{step_index}",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": "*Replay Mismatch Detected* :warning:"},
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Trace ID*\n`{trace_id}`"},
                                {"type": "mrkdwn", "text": f"*Step Index*\n{step_index}"},
                                {"type": "mrkdwn", "text": f"*Reason*\n{reason}"},
                                {"type": "mrkdwn", "text": f"*Reported By*\n{user_id}"},
                            ],
                        },
                    ],
                }
                async with httpx.AsyncClient() as client:
                    resp = await client.post(slack_webhook, json=message, timeout=10.0)
                    if resp.status_code == 200:
                        return NotificationResult(channel="slack", success=True)
            except Exception as e:
                logger.warning(f"Failed to send Slack notification: {e}")

        return NotificationResult(channel="none", success=False)

    async def _create_bulk_github_issue(
        self,
        by_trace: dict[str, list[dict]],
        total_count: int,
        user_id: str,
    ) -> Optional[str]:
        """Create a bulk GitHub issue for multiple mismatches."""
        import httpx

        github_token = os.getenv("GITHUB_TOKEN")
        github_repo = os.getenv("GITHUB_REPO")

        if not github_token or not github_repo:
            return None

        try:
            title = f"[Replay Mismatches] {total_count} mismatches across {len(by_trace)} trace(s)"

            body_parts = ["## Bulk Mismatch Report\n"]
            body_parts.append(f"**Total Mismatches:** {total_count}")
            body_parts.append(f"**Traces Affected:** {len(by_trace)}")
            body_parts.append(f"**Reported By:** {user_id}\n")

            for trace_id, mismatches in by_trace.items():
                body_parts.append(f"### Trace `{trace_id}`")
                body_parts.append("| Step | Reason | Expected | Actual |")
                body_parts.append("|------|--------|----------|--------|")
                for m in mismatches:
                    exp = m["expected_hash"][:8] if m["expected_hash"] else "N/A"
                    act = m["actual_hash"][:8] if m["actual_hash"] else "N/A"
                    body_parts.append(f"| {m['step_index']} | {m['reason']} | `{exp}` | `{act}` |")
                body_parts.append("")

            body = "\n".join(body_parts)

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://api.github.com/repos/{github_repo}/issues",
                    headers={
                        "Authorization": f"token {github_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    json={
                        "title": title,
                        "body": body,
                        "labels": ["replay-mismatch", "aos", "bulk-report", "automated"],
                    },
                    timeout=15.0,
                )
                if resp.status_code in (200, 201):
                    issue_data = resp.json()
                    return issue_data.get("html_url")
        except Exception as e:
            logger.warning(f"Failed to create bulk GitHub issue: {e}")

        return None

    async def _comment_on_github_issue(
        self,
        issue_url: str,
        user_id: str,
        resolution_note: str,
    ) -> None:
        """Comment on a GitHub issue when a mismatch is resolved."""
        import httpx

        github_token = os.getenv("GITHUB_TOKEN")
        github_repo = os.getenv("GITHUB_REPO")

        if not github_token or not github_repo:
            return

        try:
            # Extract issue number from URL
            issue_number = issue_url.rstrip("/").split("/")[-1]

            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.github.com/repos/{github_repo}/issues/{issue_number}/comments",
                    headers={
                        "Authorization": f"token {github_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    json={"body": f"Resolved by {user_id}\n\n{resolution_note}"},
                    timeout=10.0,
                )
        except Exception as e:
            logger.warning(f"Failed to comment on GitHub issue: {e}")


def get_trace_mismatch_engine(driver: TraceMismatchDriver) -> TraceMismatchEngine:
    """Get trace mismatch engine instance for the given (session-bound) driver."""
    return TraceMismatchEngine(driver)
