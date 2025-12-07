#!/usr/bin/env python3
"""
Prometheus Alert Fuzzer - M7 Implementation

Generate randomized Alertmanager webhook payloads to validate:
- Webhook receiver routing
- Rate limiting behavior
- Alert ingestion
- Metric recording

Usage:
    # Basic fuzzing (50 alerts)
    python3 alert_fuzzer.py --url http://localhost:8011/webhook/alertmanager

    # Stress test (1000 alerts, 50 concurrent)
    python3 alert_fuzzer.py --url http://localhost:8011/webhook/alertmanager \
        --count 1000 --concurrency 50

    # With authentication
    WEBHOOK_TOKEN=xxx python3 alert_fuzzer.py --url http://localhost:8011/webhook/alertmanager

    # Specific alert patterns
    python3 alert_fuzzer.py --url http://localhost:8011/webhook/alertmanager \
        --alert-name MemoryPinError --severity critical
"""

import argparse
import asyncio
import json
import logging
import os
import random
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("alert_fuzzer")

# Default alert configurations
SEVERITIES = ["critical", "warning", "info"]
ALERT_NAMES = [
    "WebhookLatencyHigh",
    "RateLimitExceeded",
    "RedisLatencyHigh",
    "DBConnExhaustion",
    "MemoryPinError",
    "RBACDenied",
    "CostSimDrift",
    "WorkflowStalled",
    "BudgetExceeded",
    "SkillTimeout",
]
INSTANCES = [f"svc-{i}" for i in range(1, 11)]
NAMESPACES = ["aos-staging", "aos-prod", "default"]


@dataclass
class FuzzResult:
    """Result of a single fuzz request."""
    success: bool
    status_code: int
    response_time_ms: float
    alert_name: str
    error: Optional[str] = None


def generate_alert(
    name: Optional[str] = None,
    severity: Optional[str] = None,
    instance: Optional[str] = None,
    namespace: Optional[str] = None,
    status: str = "firing",
) -> Dict[str, Any]:
    """
    Generate a single Alertmanager alert payload.

    Args:
        name: Alert name (random if not specified)
        severity: Alert severity (random if not specified)
        instance: Instance label (random if not specified)
        namespace: Namespace label (random if not specified)
        status: Alert status (firing or resolved)

    Returns:
        Alertmanager webhook payload
    """
    alert_name = name or random.choice(ALERT_NAMES)
    alert_severity = severity or random.choice(SEVERITIES)
    alert_instance = instance or random.choice(INSTANCES)
    alert_namespace = namespace or random.choice(NAMESPACES)

    now = datetime.now(timezone.utc)
    starts_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    ends_at = (now.replace(minute=now.minute + 5)).strftime("%Y-%m-%dT%H:%M:%SZ") if status == "firing" else starts_at

    # Generate unique fingerprint
    fingerprint = uuid.uuid4().hex[:16]

    return {
        "version": "4",
        "groupKey": f"{alert_namespace}/{alert_name}",
        "truncatedAlerts": 0,
        "status": status,
        "receiver": "webhook",
        "groupLabels": {
            "alertname": alert_name,
            "namespace": alert_namespace,
        },
        "commonLabels": {
            "alertname": alert_name,
            "severity": alert_severity,
            "instance": alert_instance,
            "namespace": alert_namespace,
            "job": "aos",
        },
        "commonAnnotations": {
            "summary": f"[FUZZ] {alert_name} triggered",
            "description": f"Fuzzer-generated alert for testing. Instance: {alert_instance}",
            "runbook_url": f"https://docs.example.com/runbooks/{alert_name.lower()}",
        },
        "externalURL": "http://alertmanager:9093",
        "alerts": [
            {
                "status": status,
                "labels": {
                    "alertname": alert_name,
                    "severity": alert_severity,
                    "instance": alert_instance,
                    "namespace": alert_namespace,
                    "job": "aos",
                    "fuzz_id": fingerprint,
                },
                "annotations": {
                    "summary": f"[FUZZ] {alert_name} triggered",
                    "description": f"Fuzzer-generated alert. Fingerprint: {fingerprint}",
                },
                "startsAt": starts_at,
                "endsAt": ends_at,
                "generatorURL": f"http://prometheus:9090/graph?g0.expr={alert_name}",
                "fingerprint": fingerprint,
            }
        ],
    }


def send_alert(
    url: str,
    payload: Dict[str, Any],
    token: Optional[str] = None,
    timeout: float = 5.0,
) -> FuzzResult:
    """
    Send an alert payload to the webhook receiver.

    Args:
        url: Webhook URL
        payload: Alert payload
        token: Optional authentication token
        timeout: Request timeout

    Returns:
        FuzzResult with success status and timing
    """
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    alert_name = payload.get("commonLabels", {}).get("alertname", "unknown")
    start_time = time.time()

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout,
        )
        elapsed_ms = (time.time() - start_time) * 1000

        return FuzzResult(
            success=response.status_code in (200, 201, 202),
            status_code=response.status_code,
            response_time_ms=elapsed_ms,
            alert_name=alert_name,
        )

    except requests.exceptions.Timeout:
        return FuzzResult(
            success=False,
            status_code=0,
            response_time_ms=(time.time() - start_time) * 1000,
            alert_name=alert_name,
            error="timeout",
        )
    except requests.exceptions.ConnectionError as e:
        return FuzzResult(
            success=False,
            status_code=0,
            response_time_ms=(time.time() - start_time) * 1000,
            alert_name=alert_name,
            error=f"connection_error: {str(e)[:50]}",
        )
    except Exception as e:
        return FuzzResult(
            success=False,
            status_code=0,
            response_time_ms=(time.time() - start_time) * 1000,
            alert_name=alert_name,
            error=f"error: {str(e)[:50]}",
        )


def run_sequential(
    url: str,
    count: int,
    token: Optional[str],
    pause: float,
    alert_name: Optional[str],
    severity: Optional[str],
) -> List[FuzzResult]:
    """Run fuzzer sequentially with optional pause between requests."""
    results = []

    for i in range(count):
        payload = generate_alert(name=alert_name, severity=severity)
        result = send_alert(url, payload, token)
        results.append(result)

        status_icon = "✓" if result.success else "✗"
        logger.info(
            f"[{i+1}/{count}] {status_icon} {result.alert_name} - "
            f"{result.status_code} ({result.response_time_ms:.1f}ms)"
        )

        if pause > 0 and i < count - 1:
            time.sleep(pause)

    return results


def run_concurrent(
    url: str,
    count: int,
    concurrency: int,
    token: Optional[str],
    alert_name: Optional[str],
    severity: Optional[str],
) -> List[FuzzResult]:
    """Run fuzzer with concurrent requests."""
    results = []

    def send_one(i: int) -> FuzzResult:
        payload = generate_alert(name=alert_name, severity=severity)
        return send_alert(url, payload, token)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(send_one, i) for i in range(count)]
        for i, future in enumerate(futures):
            result = future.result()
            results.append(result)
            status_icon = "✓" if result.success else "✗"
            logger.info(
                f"[{i+1}/{count}] {status_icon} {result.alert_name} - "
                f"{result.status_code} ({result.response_time_ms:.1f}ms)"
            )

    return results


def print_summary(results: List[FuzzResult], duration_seconds: float):
    """Print summary statistics."""
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful

    response_times = [r.response_time_ms for r in results]
    avg_time = sum(response_times) / len(response_times) if response_times else 0
    min_time = min(response_times) if response_times else 0
    max_time = max(response_times) if response_times else 0

    # Count by status code
    status_codes: Dict[int, int] = {}
    for r in results:
        status_codes[r.status_code] = status_codes.get(r.status_code, 0) + 1

    # Count by alert name
    alert_counts: Dict[str, int] = {}
    for r in results:
        alert_counts[r.alert_name] = alert_counts.get(r.alert_name, 0) + 1

    print("\n" + "=" * 60)
    print("FUZZ SUMMARY")
    print("=" * 60)
    print(f"Total requests:    {total}")
    print(f"Successful:        {successful} ({100*successful/total:.1f}%)")
    print(f"Failed:            {failed} ({100*failed/total:.1f}%)")
    print(f"Duration:          {duration_seconds:.2f}s")
    print(f"Requests/sec:      {total/duration_seconds:.1f}")
    print()
    print("Response Times:")
    print(f"  Min:   {min_time:.1f}ms")
    print(f"  Avg:   {avg_time:.1f}ms")
    print(f"  Max:   {max_time:.1f}ms")
    print()
    print("Status Codes:")
    for code, count in sorted(status_codes.items()):
        print(f"  {code}: {count}")
    print()
    print("Alerts by Name:")
    for name, count in sorted(alert_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {name}: {count}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Prometheus Alert Fuzzer for webhook testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic test
    python3 alert_fuzzer.py --url http://localhost:8011/webhook/alertmanager

    # Stress test
    python3 alert_fuzzer.py --url http://localhost:8011/webhook/alertmanager \\
        --count 1000 --concurrency 50

    # Specific alert pattern
    python3 alert_fuzzer.py --url http://localhost:8011/webhook/alertmanager \\
        --alert-name MemoryPinError --severity critical
        """
    )

    parser.add_argument(
        "--url",
        required=True,
        help="Webhook receiver URL"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of alerts to send (default: 50)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of concurrent requests (default: 1 = sequential)"
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0.1,
        help="Pause between sequential requests in seconds (default: 0.1)"
    )
    parser.add_argument(
        "--token",
        default=os.getenv("WEBHOOK_TOKEN"),
        help="Authentication token (or set WEBHOOK_TOKEN env)"
    )
    parser.add_argument(
        "--alert-name",
        help="Use specific alert name (random if not set)"
    )
    parser.add_argument(
        "--severity",
        choices=["critical", "warning", "info"],
        help="Use specific severity (random if not set)"
    )
    parser.add_argument(
        "--output",
        help="Write results to JSON file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Starting alert fuzzer: {args.count} alerts to {args.url}")
    if args.concurrency > 1:
        logger.info(f"Concurrent mode: {args.concurrency} workers")
    else:
        logger.info(f"Sequential mode: {args.pause}s pause between requests")

    start_time = time.time()

    if args.concurrency > 1:
        results = run_concurrent(
            url=args.url,
            count=args.count,
            concurrency=args.concurrency,
            token=args.token,
            alert_name=args.alert_name,
            severity=args.severity,
        )
    else:
        results = run_sequential(
            url=args.url,
            count=args.count,
            token=args.token,
            pause=args.pause,
            alert_name=args.alert_name,
            severity=args.severity,
        )

    duration = time.time() - start_time
    print_summary(results, duration)

    # Write results to file if requested
    if args.output:
        output_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "url": args.url,
            "count": args.count,
            "concurrency": args.concurrency,
            "duration_seconds": duration,
            "results": [
                {
                    "success": r.success,
                    "status_code": r.status_code,
                    "response_time_ms": r.response_time_ms,
                    "alert_name": r.alert_name,
                    "error": r.error,
                }
                for r in results
            ],
        }
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Results written to {args.output}")

    # Exit with error if too many failures
    failure_rate = (len(results) - sum(1 for r in results if r.success)) / len(results)
    if failure_rate > 0.1:
        logger.error(f"High failure rate: {failure_rate*100:.1f}%")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
