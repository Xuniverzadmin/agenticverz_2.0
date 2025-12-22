#!/usr/bin/env python3
"""
M10 Synthetic Traffic Generator

Generates synthetic traffic to exercise outbox/queue every 30 minutes in staging.
Ensures the M10 recovery pipeline stays warm and detects issues early.

Usage:
    # Run once (generate 10 synthetic events)
    python -m scripts.ops.m10_synthetic_traffic

    # Custom count
    python -m scripts.ops.m10_synthetic_traffic --count 20

    # Dry run (show what would be created)
    python -m scripts.ops.m10_synthetic_traffic --dry-run

    # JSON output for monitoring
    python -m scripts.ops.m10_synthetic_traffic --json

Systemd Timer (staging):
    Create /etc/systemd/system/m10-synthetic-traffic.timer:

    [Unit]
    Description=M10 Synthetic Traffic Generator

    [Timer]
    OnCalendar=*:0/30
    Persistent=true

    [Install]
    WantedBy=timers.target

Environment Variables:
    DATABASE_URL: PostgreSQL connection URL (required)
    M10_SYNTHETIC_COUNT: Number of events to generate (default: 10)
"""

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

logger = logging.getLogger("m10.synthetic_traffic")

DATABASE_URL = os.getenv("DATABASE_URL")
DEFAULT_COUNT = int(os.getenv("M10_SYNTHETIC_COUNT", "10"))


def generate_synthetic_events(count: int, dry_run: bool = False) -> dict:
    """Generate synthetic outbox events for testing."""
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count_requested": count,
        "count_created": 0,
        "dry_run": dry_run,
        "events": [],
        "error": None,
    }

    if not DATABASE_URL:
        result["error"] = "DATABASE_URL not configured"
        return result

    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)

        with Session(engine) as session:
            for i in range(count):
                event_id = str(uuid.uuid4())
                aggregate_id = f"synthetic-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{i}"

                payload = {
                    "synthetic": True,
                    "generator": "m10_synthetic_traffic",
                    "sequence": i,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "url": "http://127.0.0.1:9999/synthetic-sink",  # Non-routable sink
                    "method": "POST",
                    "body": {"test": True, "event_id": event_id},
                }

                if dry_run:
                    result["events"].append(
                        {
                            "aggregate_id": aggregate_id,
                            "event_type": "http:synthetic_test",
                            "payload_preview": str(payload)[:100],
                        }
                    )
                else:
                    # Insert into outbox using publish_outbox function
                    session.execute(
                        text(
                            """
                            SELECT m10_recovery.publish_outbox(
                                :aggregate_type,
                                :aggregate_id,
                                :event_type,
                                :payload::jsonb
                            )
                        """
                        ),
                        {
                            "aggregate_type": "synthetic_test",
                            "aggregate_id": aggregate_id,
                            "event_type": "http:synthetic_test",
                            "payload": json.dumps(payload),
                        },
                    )
                    result["events"].append(
                        {
                            "aggregate_id": aggregate_id,
                            "event_type": "http:synthetic_test",
                        }
                    )

                result["count_created"] += 1

            if not dry_run:
                session.commit()

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Failed to generate synthetic events: {e}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic traffic for M10 outbox/queue"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help=f"Number of events to generate (default: {DEFAULT_COUNT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without actually creating",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    logger.info(f"Generating {args.count} synthetic events (dry_run={args.dry_run})")

    result = generate_synthetic_events(args.count, args.dry_run)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["error"]:
            print(f"ERROR: {result['error']}")
            sys.exit(1)
        else:
            print(f"Generated {result['count_created']} synthetic events")
            if args.dry_run:
                print("(dry-run mode - no events actually created)")
            for event in result["events"][:5]:
                print(f"  - {event['aggregate_id']}: {event['event_type']}")
            if len(result["events"]) > 5:
                print(f"  ... and {len(result['events']) - 5} more")

    sys.exit(0 if not result["error"] else 1)


if __name__ == "__main__":
    main()
