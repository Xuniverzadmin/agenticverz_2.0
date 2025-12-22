#!/usr/bin/env python3
"""
Synthetic Alert Injector for AOS

M8 Deliverable: Tool to inject synthetic alerts into Alertmanager for
testing alerting pipeline end-to-end (Alertmanager -> Slack).

Usage:
    python inject_synthetic_alert.py --type cost_overrun
    python inject_synthetic_alert.py --type rate_limit_breach --severity critical
    python inject_synthetic_alert.py --type replay_mismatch --tenant acme
    python inject_synthetic_alert.py --resolve --fingerprint abc123

Alert Types:
- cost_overrun: Skill budget exceeded
- rate_limit_breach: Tenant rate limit exceeded
- replay_mismatch: Replay parity failure
- worker_unhealthy: Worker health check failed
- custom: Custom alert with --name and --description
"""
import os
import sys
import json
import argparse
import requests
from datetime import datetime, timezone
from typing import Optional

# Configuration
ALERTMANAGER_URL = os.environ.get("ALERTMANAGER_URL", "http://localhost:9093")


def generate_alert(
    alert_type: str,
    severity: str = "warning",
    tenant_id: str = "default",
    custom_name: Optional[str] = None,
    custom_description: Optional[str] = None,
) -> dict:
    """Generate alert payload based on type."""

    base_labels = {
        "alertname": "",
        "severity": severity,
        "tenant_id": tenant_id,
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "injected": "true",
    }

    base_annotations = {
        "summary": "",
        "description": "",
        "runbook_url": "https://docs.agenticverz.com/runbooks/",
    }

    now = datetime.now(timezone.utc).isoformat()

    if alert_type == "cost_overrun":
        base_labels["alertname"] = "AOSCostOverrun"
        base_labels["skill"] = "llm_invoke"
        base_annotations["summary"] = f"Cost overrun detected for tenant {tenant_id}"
        base_annotations["description"] = (
            f"Tenant {tenant_id} has exceeded 80% of allocated budget. "
            f"Current usage: $8.50 / $10.00 limit."
        )
        base_annotations["runbook_url"] += "cost-overrun"

    elif alert_type == "rate_limit_breach":
        base_labels["alertname"] = "AOSRateLimitBreach"
        base_labels["tier"] = "free"
        base_annotations["summary"] = f"Rate limit breach for tenant {tenant_id}"
        base_annotations["description"] = (
            f"Tenant {tenant_id} (tier: free) has exceeded rate limit. "
            f"Current: 75 requests, Limit: 60/min."
        )
        base_annotations["runbook_url"] += "rate-limit-breach"

    elif alert_type == "replay_mismatch":
        base_labels["alertname"] = "AOSReplayMismatch"
        base_labels["trace_id"] = "trace_12345"
        base_annotations["summary"] = f"Replay parity failure for tenant {tenant_id}"
        base_annotations["description"] = (
            "Replay of trace_12345 diverged at step 3. "
            "Expected hash: abc123, Actual: def456. "
            "Review required."
        )
        base_annotations["runbook_url"] += "replay-mismatch"

    elif alert_type == "worker_unhealthy":
        base_labels["alertname"] = "AOSWorkerUnhealthy"
        base_labels["worker_id"] = "worker-1"
        base_annotations["summary"] = "AOS worker health check failed"
        base_annotations["description"] = (
            f"Worker worker-1 has failed health check for 5 minutes. "
            f"Last seen: {now}. Investigate immediately."
        )
        base_annotations["runbook_url"] += "worker-unhealthy"

    elif alert_type == "custom":
        base_labels["alertname"] = custom_name or "AOSCustomAlert"
        base_annotations["summary"] = custom_name or "Custom synthetic alert"
        base_annotations["description"] = (
            custom_description or "Synthetic alert for testing"
        )
        base_annotations["runbook_url"] += "custom"

    else:
        raise ValueError(f"Unknown alert type: {alert_type}")

    return {
        "labels": base_labels,
        "annotations": base_annotations,
        "startsAt": now,
        "generatorURL": "http://localhost:8000/api/v1/runtime/simulate",
    }


def inject_alert(alert: dict, alertmanager_url: str = None) -> dict:
    """Send alert to Alertmanager."""
    base_url = alertmanager_url or ALERTMANAGER_URL
    url = f"{base_url}/api/v2/alerts"

    try:
        response = requests.post(
            url,
            json=[alert],
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        return {"success": True, "status": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def resolve_alert(fingerprint: str, alertmanager_url: str = None) -> dict:
    """Resolve an alert by fingerprint."""
    base_url = alertmanager_url or ALERTMANAGER_URL
    url = f"{base_url}/api/v2/alerts"

    now = datetime.now(timezone.utc).isoformat()

    # To resolve, we send the same alert with endsAt set
    payload = [
        {
            "labels": {"fingerprint": fingerprint},
            "endsAt": now,
        }
    ]

    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        return {"success": True, "status": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def list_active_alerts(alertmanager_url: str = None) -> dict:
    """List currently active alerts."""
    base_url = alertmanager_url or ALERTMANAGER_URL
    url = f"{base_url}/api/v2/alerts"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return {"success": True, "alerts": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Inject synthetic alerts into Alertmanager for testing"
    )

    parser.add_argument(
        "--type",
        "-t",
        choices=[
            "cost_overrun",
            "rate_limit_breach",
            "replay_mismatch",
            "worker_unhealthy",
            "custom",
        ],
        default="cost_overrun",
        help="Type of alert to inject",
    )
    parser.add_argument(
        "--severity",
        "-s",
        choices=["info", "warning", "critical"],
        default="warning",
        help="Alert severity level",
    )
    parser.add_argument(
        "--tenant", default="synthetic-test", help="Tenant ID for the alert"
    )
    parser.add_argument("--name", help="Custom alert name (for --type custom)")
    parser.add_argument(
        "--description", help="Custom alert description (for --type custom)"
    )
    parser.add_argument(
        "--resolve", action="store_true", help="Resolve an alert instead of creating"
    )
    parser.add_argument(
        "--fingerprint", help="Alert fingerprint to resolve (with --resolve)"
    )
    parser.add_argument("--list", action="store_true", help="List active alerts")
    parser.add_argument(
        "--alertmanager-url", default=ALERTMANAGER_URL, help="Alertmanager URL"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print alert payload without sending"
    )
    parser.add_argument("--json", action="store_true", help="Output result as JSON")

    args = parser.parse_args()

    # Use provided Alertmanager URL or default
    alertmanager_url = args.alertmanager_url

    if args.list:
        result = list_active_alerts(alertmanager_url)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["success"]:
                # API v2 returns alerts directly as a list
                alerts = result.get("alerts", [])
                if isinstance(alerts, dict):
                    alerts = alerts.get("data", [])
                print(f"Active alerts: {len(alerts)}")
                for alert in alerts:
                    labels = alert.get("labels", {})
                    print(
                        f"  - {labels.get('alertname')} [{labels.get('severity')}] "
                        f"tenant={labels.get('tenant_id', 'N/A')}"
                    )
            else:
                print(f"Error: {result['error']}")
        sys.exit(0 if result["success"] else 1)

    if args.resolve:
        if not args.fingerprint:
            print("Error: --fingerprint required with --resolve")
            sys.exit(1)
        result = resolve_alert(args.fingerprint, alertmanager_url)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["success"]:
                print(f"Alert resolved: {args.fingerprint}")
            else:
                print(f"Error resolving alert: {result['error']}")
        sys.exit(0 if result["success"] else 1)

    # Generate alert
    try:
        alert = generate_alert(
            alert_type=args.type,
            severity=args.severity,
            tenant_id=args.tenant,
            custom_name=args.name,
            custom_description=args.description,
        )
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.dry_run:
        print(json.dumps(alert, indent=2))
        sys.exit(0)

    # Inject alert
    result = inject_alert(alert, alertmanager_url)

    if args.json:
        output = {**result, "alert": alert}
        print(json.dumps(output, indent=2))
    else:
        if result["success"]:
            print("Alert injected successfully!")
            print(f"  Type: {args.type}")
            print(f"  Severity: {args.severity}")
            print(f"  Alertname: {alert['labels']['alertname']}")
            print(f"  Tenant: {args.tenant}")
        else:
            print(f"Error injecting alert: {result['error']}")

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
