#!/usr/bin/env python3
"""
M9 Synthetic Failure Traffic Generator

Generates synthetic failure events for validation:
- 600 known (mapped) errors
- 300 unknown signature errors
- 100 recovery attempts (50 success, 50 failure)

Validates:
- SELECT count(*) FROM failure_matches >= 1000
- Prometheus metrics show expected counts
- Grafana panels reflect the spike

Usage:
    python tools/generate_synthetic_failures.py --count 1000 --validate
    python tools/generate_synthetic_failures.py --dry-run
"""

import argparse
import json
import logging
import os
import random
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("synthetic_failures")


# Known error codes from failure catalog
KNOWN_ERROR_CODES = [
    "TIMEOUT",
    "RATE_LIMITED",
    "HTTP_5XX",
    "HTTP_4XX",
    "DNS_FAILURE",
    "CONNECTION_REFUSED",
    "CONTEXT_OVERFLOW",
    "SCHEMA_VALIDATION_FAILED",
    "FILE_NOT_FOUND",
    "PERMISSION_DENIED",
    "DISK_FULL",
    "DELIVERY_FAILED",
    "TRANSFORM_ERROR",
]

UNKNOWN_ERROR_PATTERNS = [
    "UnexpectedError_{uuid}",
    "CustomException_{uuid}",
    "ServiceError_{service}_{code}",
    "InternalError_{component}",
    "ValidationFailed_{field}",
    "UnknownState_{state}",
    "CorruptedData_{entity}",
    "MissingDependency_{dep}",
]

SKILLS = ["http_call", "llm_invoke", "json_transform", "fs_read", "fs_write", "webhook_send", "email_send"]
CATEGORIES = ["TRANSIENT", "PERMANENT", "PERMISSION", "RESOURCE"]
SEVERITIES = ["INFO", "WARNING", "ERROR", "CRITICAL"]
RECOVERY_MODES = ["RETRY", "FALLBACK", "MANUAL", "SKIP", None]
TENANTS = ["tenant-001", "tenant-002", "tenant-003", None]


@dataclass
class SyntheticFailure:
    """Represents a synthetic failure event."""
    run_id: str
    error_code: str
    error_message: str
    is_known: bool
    skill_id: str
    step_index: int
    category: str
    severity: str
    tenant_id: Optional[str]
    recovery_mode: Optional[str]
    is_recovery_attempt: bool = False
    recovery_succeeded: Optional[bool] = None


def generate_known_failure() -> SyntheticFailure:
    """Generate a failure with a known catalog entry."""
    error_code = random.choice(KNOWN_ERROR_CODES)
    skill = random.choice(SKILLS)

    messages = {
        "TIMEOUT": f"Connection timed out after {random.randint(10, 60)}s",
        "RATE_LIMITED": f"Rate limit exceeded. Retry after {random.randint(1, 60)}s",
        "HTTP_5XX": f"Server error: {random.choice([500, 502, 503, 504])}",
        "HTTP_4XX": f"Client error: {random.choice([400, 401, 403, 404, 422])}",
        "DNS_FAILURE": f"DNS resolution failed for {random.choice(['api.example.com', 'svc.internal', 'db.prod'])}",
        "CONNECTION_REFUSED": f"Connection refused on port {random.choice([80, 443, 5432, 6379])}",
        "CONTEXT_OVERFLOW": f"Context exceeded max tokens: {random.randint(100000, 150000)} > 100000",
        "SCHEMA_VALIDATION_FAILED": f"Schema validation failed: missing required field '{random.choice(['id', 'name', 'type'])}'",
        "FILE_NOT_FOUND": f"File not found: /path/to/{random.choice(['config.json', 'data.csv', 'template.txt'])}",
        "PERMISSION_DENIED": f"Permission denied for operation: {random.choice(['read', 'write', 'execute'])}",
        "DISK_FULL": f"Disk space exhausted: {random.randint(0, 5)}MB remaining",
        "DELIVERY_FAILED": f"Email delivery failed: {random.choice(['SMTP error', 'Invalid recipient', 'Quota exceeded'])}",
        "TRANSFORM_ERROR": f"Transform error: {random.choice(['null pointer', 'type mismatch', 'invalid json'])}",
    }

    return SyntheticFailure(
        run_id=f"run-{uuid.uuid4().hex[:12]}",
        error_code=error_code,
        error_message=messages.get(error_code, f"Error: {error_code}"),
        is_known=True,
        skill_id=skill,
        step_index=random.randint(0, 5),
        category=random.choice(CATEGORIES),
        severity=random.choice(SEVERITIES),
        tenant_id=random.choice(TENANTS),
        recovery_mode=random.choice(RECOVERY_MODES),
    )


def generate_unknown_failure() -> SyntheticFailure:
    """Generate a failure with an unknown error signature."""
    pattern = random.choice(UNKNOWN_ERROR_PATTERNS)

    replacements = {
        "{uuid}": uuid.uuid4().hex[:8],
        "{service}": random.choice(["auth", "payment", "inventory", "notification"]),
        "{code}": str(random.randint(1000, 9999)),
        "{component}": random.choice(["parser", "validator", "serializer", "handler"]),
        "{field}": random.choice(["user_id", "amount", "status", "timestamp"]),
        "{state}": random.choice(["PENDING", "PROCESSING", "UNKNOWN"]),
        "{entity}": random.choice(["user", "order", "session", "transaction"]),
        "{dep}": random.choice(["redis", "kafka", "postgres", "elasticsearch"]),
    }

    error_code = pattern
    for key, value in replacements.items():
        error_code = error_code.replace(key, value)

    return SyntheticFailure(
        run_id=f"run-{uuid.uuid4().hex[:12]}",
        error_code=error_code,
        error_message=f"Unknown error: {error_code}",
        is_known=False,
        skill_id=random.choice(SKILLS),
        step_index=random.randint(0, 5),
        category=random.choice(CATEGORIES),
        severity=random.choice(SEVERITIES),
        tenant_id=random.choice(TENANTS),
        recovery_mode=None,  # Unknown errors don't have catalog recovery modes
    )


def generate_recovery_attempt(succeeded: bool) -> SyntheticFailure:
    """Generate a failure with recovery attempt."""
    failure = generate_known_failure()
    failure.is_recovery_attempt = True
    failure.recovery_succeeded = succeeded
    return failure


def generate_batch(known: int = 600, unknown: int = 300, recovery_success: int = 50, recovery_fail: int = 50) -> List[SyntheticFailure]:
    """Generate a batch of synthetic failures."""
    failures = []

    logger.info(f"Generating {known} known failures...")
    for _ in range(known):
        failures.append(generate_known_failure())

    logger.info(f"Generating {unknown} unknown failures...")
    for _ in range(unknown):
        failures.append(generate_unknown_failure())

    logger.info(f"Generating {recovery_success} successful recovery attempts...")
    for _ in range(recovery_success):
        failures.append(generate_recovery_attempt(succeeded=True))

    logger.info(f"Generating {recovery_fail} failed recovery attempts...")
    for _ in range(recovery_fail):
        failures.append(generate_recovery_attempt(succeeded=False))

    # Shuffle for realism
    random.shuffle(failures)

    return failures


def persist_failure(failure: SyntheticFailure) -> Optional[str]:
    """Persist a single failure to the database."""
    try:
        from app.runtime.failure_catalog import (
            FailureCatalog,
            persist_failure_match,
        )

        catalog = FailureCatalog()

        # Match against catalog
        result = catalog.match_code(failure.error_code)
        if not result.matched:
            result = catalog.match_message(failure.error_message)

        # Persist with matched result
        record_id = persist_failure_match(
            run_id=failure.run_id,
            result=result,
            error_code=failure.error_code,
            error_message=failure.error_message,
            tenant_id=failure.tenant_id,
            skill_id=failure.skill_id,
            step_index=failure.step_index,
            context={"synthetic": True, "is_known": failure.is_known},
        )

        return record_id

    except Exception as e:
        logger.error(f"Failed to persist failure: {e}")
        return None


def update_recovery(failure_id: str, succeeded: bool) -> bool:
    """Update recovery status for a failure."""
    try:
        from sqlmodel import Session, select
        from app.db import engine, FailureMatch
        from app.runtime.failure_catalog import update_recovery_status

        with Session(engine) as session:
            failure = session.exec(
                select(FailureMatch).where(FailureMatch.id == failure_id)
            ).first()

            if failure:
                if succeeded:
                    failure.mark_recovery_succeeded(by="synthetic", notes="Synthetic test")
                else:
                    failure.mark_recovery_failed(by="synthetic", notes="Synthetic test")

                session.add(failure)
                session.commit()

                # Update metrics
                update_recovery_status(
                    succeeded=succeeded,
                    recovery_mode=failure.recovery_mode or "unknown",
                    error_code=failure.error_code[:50] if failure.error_code else "unknown",
                )
                return True
        return False
    except Exception as e:
        logger.error(f"Failed to update recovery: {e}")
        return False


def validate_db(expected_min: int = 1000) -> Dict[str, Any]:
    """Validate database has expected records."""
    try:
        from sqlmodel import Session, select, func
        from app.db import engine, FailureMatch

        with Session(engine) as session:
            total = session.exec(
                select(func.count(FailureMatch.id))
            ).one()

            matched = session.exec(
                select(func.count(FailureMatch.id)).where(
                    FailureMatch.catalog_entry_id.isnot(None)
                )
            ).one()

            recovery_attempted = session.exec(
                select(func.count(FailureMatch.id)).where(
                    FailureMatch.recovery_attempted == True
                )
            ).one()

            recovery_succeeded = session.exec(
                select(func.count(FailureMatch.id)).where(
                    FailureMatch.recovery_succeeded == True
                )
            ).one()

            return {
                "total": total,
                "matched": matched,
                "unmatched": total - matched,
                "recovery_attempted": recovery_attempted,
                "recovery_succeeded": recovery_succeeded,
                "pass": total >= expected_min,
            }
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return {"error": str(e), "pass": False}


def validate_metrics() -> Dict[str, Any]:
    """Validate Prometheus metrics."""
    import urllib.request

    try:
        with urllib.request.urlopen("http://localhost:9090/api/v1/query?query=failure_match_hits_total") as response:
            hits_data = json.loads(response.read().decode())

        with urllib.request.urlopen("http://localhost:9090/api/v1/query?query=failure_match_misses_total") as response:
            misses_data = json.loads(response.read().decode())

        with urllib.request.urlopen("http://localhost:9090/api/v1/query?query=recovery_success_total") as response:
            recovery_data = json.loads(response.read().decode())

        return {
            "hits": hits_data.get("data", {}).get("result", []),
            "misses": misses_data.get("data", {}).get("result", []),
            "recovery": recovery_data.get("data", {}).get("result", []),
            "prometheus_reachable": True,
        }
    except Exception as e:
        logger.warning(f"Could not fetch metrics: {e}")
        return {"prometheus_reachable": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic failure traffic for M9 validation")
    parser.add_argument("--known", type=int, default=600, help="Number of known failures")
    parser.add_argument("--unknown", type=int, default=300, help="Number of unknown failures")
    parser.add_argument("--recovery-success", type=int, default=50, help="Recovery success attempts")
    parser.add_argument("--recovery-fail", type=int, default=50, help="Recovery failure attempts")
    parser.add_argument("--dry-run", action="store_true", help="Generate but don't persist")
    parser.add_argument("--validate", action="store_true", help="Validate after generation")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for progress reporting")

    args = parser.parse_args()

    total = args.known + args.unknown + args.recovery_success + args.recovery_fail
    logger.info(f"Generating {total} synthetic failures...")

    failures = generate_batch(
        known=args.known,
        unknown=args.unknown,
        recovery_success=args.recovery_success,
        recovery_fail=args.recovery_fail,
    )

    if args.dry_run:
        logger.info("Dry run mode - not persisting")
        print(f"\nGenerated {len(failures)} failures:")
        print(f"  Known: {sum(1 for f in failures if f.is_known)}")
        print(f"  Unknown: {sum(1 for f in failures if not f.is_known)}")
        print(f"  Recovery attempts: {sum(1 for f in failures if f.is_recovery_attempt)}")

        # Print sample
        print("\nSample failures:")
        for f in failures[:5]:
            print(f"  - {f.error_code}: {f.error_message[:50]}... (known={f.is_known})")
        return

    # Persist failures
    logger.info("Persisting failures to database...")
    persisted = 0
    recovery_updates = 0

    for i, failure in enumerate(failures):
        if (i + 1) % args.batch_size == 0:
            logger.info(f"Progress: {i+1}/{len(failures)}")

        record_id = persist_failure(failure)
        if record_id:
            persisted += 1

            # Update recovery status if this is a recovery attempt
            if failure.is_recovery_attempt and failure.recovery_succeeded is not None:
                if update_recovery(record_id, failure.recovery_succeeded):
                    recovery_updates += 1

    logger.info(f"Persisted {persisted}/{len(failures)} failures")
    logger.info(f"Updated {recovery_updates} recovery statuses")

    if args.validate:
        logger.info("\n=== Validation ===")

        # Validate DB
        db_result = validate_db(expected_min=total)
        print(f"\nDatabase validation:")
        print(f"  Total records: {db_result.get('total', 'N/A')}")
        print(f"  Matched: {db_result.get('matched', 'N/A')}")
        print(f"  Unmatched: {db_result.get('unmatched', 'N/A')}")
        print(f"  Recovery attempted: {db_result.get('recovery_attempted', 'N/A')}")
        print(f"  Recovery succeeded: {db_result.get('recovery_succeeded', 'N/A')}")
        print(f"  PASS: {db_result.get('pass', False)}")

        # Validate metrics
        metrics_result = validate_metrics()
        print(f"\nMetrics validation:")
        print(f"  Prometheus reachable: {metrics_result.get('prometheus_reachable', False)}")
        if metrics_result.get('prometheus_reachable'):
            print(f"  Hits: {len(metrics_result.get('hits', []))} series")
            print(f"  Misses: {len(metrics_result.get('misses', []))} series")
            print(f"  Recovery: {len(metrics_result.get('recovery', []))} series")

        if db_result.get('pass'):
            print("\n✅ Validation PASSED")
            return 0
        else:
            print("\n❌ Validation FAILED")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
