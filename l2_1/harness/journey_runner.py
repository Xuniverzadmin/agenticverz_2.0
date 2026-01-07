#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: L2.1 Journey Runner - Execute canonical journeys against L2 backend
# Callers: CLI, CI/CD
# Allowed Imports: L8 (stdlib only)
# Forbidden Imports: L1-L7 (must be self-contained)
# Reference: PIN-322 (L2-L2.1 Progressive Activation)
#
# GOVERNANCE NOTE:
# This harness executes journeys defined in canonical_journeys.yaml
# and captures evidence for discovery classification.

"""
L2.1 Journey Runner

Executes canonical journeys against the L2 backend and captures evidence.

Evidence Format:
- Response status code
- Response headers
- Response body (truncated if large)
- Timing information
- Any errors encountered

Usage:
  python l2_1/harness/journey_runner.py                    # Run all journeys
  python l2_1/harness/journey_runner.py --journey JRN-001  # Run specific journey
  python l2_1/harness/journey_runner.py --capability CAP-001  # Run journeys for capability
  python l2_1/harness/journey_runner.py --dry-run          # Show what would run
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_BASE_URL = "http://localhost:8000"
EVIDENCE_DIR = Path(__file__).parent.parent / "evidence"
JOURNEYS_FILE = Path(__file__).parent.parent / "journeys" / "canonical_journeys.yaml"

# Maximum response body size to capture (bytes)
MAX_RESPONSE_BODY = 10000


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Journey:
    """Represents a canonical journey to execute."""
    journey_id: str
    capability_id: str
    name: str
    route: str
    method: str
    expected_status: int
    domain: str
    orders: List[str]
    audience: str
    description: str
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None


@dataclass
class JourneyResult:
    """Represents the result of executing a journey."""
    journey_id: str
    capability_id: str
    executed_at: str
    base_url: str
    route: str
    method: str

    # Response details
    status_code: Optional[int]
    response_headers: Dict[str, str]
    response_body: Optional[str]
    response_time_ms: float

    # Expected vs actual
    expected_status: int
    status_match: bool

    # Error handling
    error: Optional[str]
    error_type: Optional[str]

    # Classification hints
    suggested_failure_type: Optional[str]


# =============================================================================
# JOURNEY LOADING (simplified YAML parser)
# =============================================================================

def load_journeys_simple(file_path: Path) -> List[Journey]:
    """Load journeys from a simplified YAML file.

    Note: This is a simple parser for the canonical journeys format.
    For production, use PyYAML.
    """
    journeys = []

    if not file_path.exists():
        print(f"Warning: Journeys file not found: {file_path}")
        return journeys

    content = file_path.read_text()

    # Simple state machine parser for our specific YAML format
    current_journey = {}
    in_journey = False
    current_key = None

    for line in content.split('\n'):
        stripped = line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith('#'):
            continue

        # Detect journey start (e.g., "- journey_id: JRN-001")
        if stripped.startswith('- journey_id:'):
            if current_journey:
                journeys.append(parse_journey_dict(current_journey))
            current_journey = {'journey_id': stripped.split(':', 1)[1].strip().strip('"')}
            in_journey = True
            continue

        if in_journey:
            # Parse key-value pairs
            if ':' in stripped and not stripped.startswith('-'):
                key, value = stripped.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                # Handle list values (orders)
                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(',')]

                current_journey[key] = value

    # Don't forget the last journey
    if current_journey:
        journeys.append(parse_journey_dict(current_journey))

    return journeys


def parse_journey_dict(d: Dict) -> Journey:
    """Parse a dictionary into a Journey object."""
    orders = d.get('orders', [])
    if isinstance(orders, str):
        orders = [orders]

    return Journey(
        journey_id=d.get('journey_id', 'UNKNOWN'),
        capability_id=d.get('capability_id', 'UNKNOWN'),
        name=d.get('name', 'Unnamed Journey'),
        route=d.get('route', '/'),
        method=d.get('method', 'GET').upper(),
        expected_status=int(d.get('expected_status', 200)),
        domain=d.get('domain', 'Unknown'),
        orders=orders,
        audience=d.get('audience', 'unknown'),
        description=d.get('description', ''),
    )


# =============================================================================
# JOURNEY EXECUTION
# =============================================================================

def execute_journey(journey: Journey, base_url: str, api_key: Optional[str] = None) -> JourneyResult:
    """Execute a single journey and capture evidence."""
    executed_at = datetime.utcnow().isoformat() + "Z"
    url = f"{base_url}{journey.route}"

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if api_key:
        headers["X-AOS-Key"] = api_key
    if journey.headers:
        headers.update(journey.headers)

    # Prepare request
    data = None
    if journey.body:
        data = json.dumps(journey.body).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=journey.method,
    )

    # Execute and capture
    start_time = time.time()
    status_code = None
    response_headers = {}
    response_body = None
    error = None
    error_type = None

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = response.status
            response_headers = dict(response.headers)
            body = response.read()
            if len(body) > MAX_RESPONSE_BODY:
                response_body = body[:MAX_RESPONSE_BODY].decode('utf-8', errors='replace') + "... [TRUNCATED]"
            else:
                response_body = body.decode('utf-8', errors='replace')

    except urllib.error.HTTPError as e:
        status_code = e.code
        response_headers = dict(e.headers)
        try:
            body = e.read()
            if len(body) > MAX_RESPONSE_BODY:
                response_body = body[:MAX_RESPONSE_BODY].decode('utf-8', errors='replace') + "... [TRUNCATED]"
            else:
                response_body = body.decode('utf-8', errors='replace')
        except:
            response_body = None
        error = str(e)
        error_type = "HTTPError"

    except urllib.error.URLError as e:
        error = str(e.reason)
        error_type = "URLError"

    except Exception as e:
        error = str(e)
        error_type = type(e).__name__

    end_time = time.time()
    response_time_ms = (end_time - start_time) * 1000

    # Determine status match
    status_match = status_code == journey.expected_status if status_code else False

    # Suggest failure type
    suggested_failure_type = None
    if error_type == "URLError":
        suggested_failure_type = "ROUTE_MISMATCH"
    elif status_code == 404:
        suggested_failure_type = "ROUTE_MISMATCH"
    elif status_code in (401, 403):
        suggested_failure_type = "AUTH_MISMATCH"
    elif not status_match and status_code:
        suggested_failure_type = "SCHEMA_MISMATCH"

    return JourneyResult(
        journey_id=journey.journey_id,
        capability_id=journey.capability_id,
        executed_at=executed_at,
        base_url=base_url,
        route=journey.route,
        method=journey.method,
        status_code=status_code,
        response_headers=response_headers,
        response_body=response_body,
        response_time_ms=round(response_time_ms, 2),
        expected_status=journey.expected_status,
        status_match=status_match,
        error=error,
        error_type=error_type,
        suggested_failure_type=suggested_failure_type,
    )


def save_evidence(result: JourneyResult, evidence_dir: Path) -> Path:
    """Save journey result as evidence file."""
    evidence_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{result.journey_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = evidence_dir / filename

    evidence = asdict(result)
    filepath.write_text(json.dumps(evidence, indent=2))

    return filepath


# =============================================================================
# MAIN RUNNER
# =============================================================================

def run_journeys(
    journeys: List[Journey],
    base_url: str,
    api_key: Optional[str] = None,
    evidence_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> List[JourneyResult]:
    """Run a list of journeys and capture evidence."""
    results = []

    print("=" * 70)
    print("L2.1 JOURNEY RUNNER")
    print("=" * 70)
    print()
    print(f"Base URL: {base_url}")
    print(f"Journeys to execute: {len(journeys)}")
    print(f"Evidence directory: {evidence_dir or 'None (not saving)'}")
    print(f"Dry run: {dry_run}")
    print()

    if dry_run:
        print("DRY RUN - Would execute:")
        for j in journeys:
            print(f"  {j.journey_id}: {j.method} {j.route} ({j.capability_id})")
        return results

    print("Executing journeys...")
    print()

    for journey in journeys:
        print(f"  {journey.journey_id}: {journey.method} {journey.route}...", end=" ", flush=True)

        result = execute_journey(journey, base_url, api_key)
        results.append(result)

        if result.status_match:
            print(f"✓ {result.status_code} ({result.response_time_ms}ms)")
        elif result.error:
            print(f"✗ ERROR: {result.error_type}")
        else:
            print(f"⚠ {result.status_code} (expected {result.expected_status})")

        if evidence_dir:
            evidence_path = save_evidence(result, evidence_dir)
            print(f"       Evidence: {evidence_path.name}")

    print()

    # Summary
    passed = sum(1 for r in results if r.status_match)
    failed = len(results) - passed

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total:  {len(results)}")
    print()

    if failed > 0:
        print("FAILURES:")
        for r in results:
            if not r.status_match:
                print(f"  {r.journey_id}: {r.error or f'Status {r.status_code}'} [{r.suggested_failure_type}]")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="L2.1 Journey Runner - Execute canonical journeys against L2 backend"
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("L2_BASE_URL", DEFAULT_BASE_URL),
        help=f"Base URL for L2 backend (default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("AOS_API_KEY"),
        help="API key for authentication (default: from AOS_API_KEY env var)"
    )
    parser.add_argument(
        "--journey",
        help="Run specific journey by ID"
    )
    parser.add_argument(
        "--capability",
        help="Run journeys for specific capability ID"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would run without executing"
    )
    parser.add_argument(
        "--no-evidence",
        action="store_true",
        help="Don't save evidence files"
    )
    parser.add_argument(
        "--journeys-file",
        type=Path,
        default=JOURNEYS_FILE,
        help="Path to journeys YAML file"
    )
    args = parser.parse_args()

    # Load journeys
    journeys = load_journeys_simple(args.journeys_file)

    if not journeys:
        print("No journeys found. Create canonical_journeys.yaml first.")
        sys.exit(1)

    # Filter journeys
    if args.journey:
        journeys = [j for j in journeys if j.journey_id == args.journey]
    elif args.capability:
        journeys = [j for j in journeys if j.capability_id == args.capability]

    if not journeys:
        print("No matching journeys found.")
        sys.exit(1)

    # Determine evidence directory
    evidence_dir = None if args.no_evidence else EVIDENCE_DIR

    # Run
    results = run_journeys(
        journeys=journeys,
        base_url=args.base_url,
        api_key=args.api_key,
        evidence_dir=evidence_dir,
        dry_run=args.dry_run,
    )

    # Exit code based on failures
    failures = sum(1 for r in results if not r.status_match)
    sys.exit(1 if failures > 0 else 0)


if __name__ == "__main__":
    main()
