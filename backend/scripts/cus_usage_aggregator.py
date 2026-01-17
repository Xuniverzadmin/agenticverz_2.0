#!/usr/bin/env python3
# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: scheduler (cron)
#   Execution: batch
# Role: Aggregate cus_llm_usage into cus_usage_daily for reporting
# Callers: cron, manual operators
# Allowed Imports: L6 (models, db)
# Forbidden Imports: L1, L2, L3, L4
# Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md

"""Customer Usage Aggregation Script

PURPOSE:
    Roll up individual LLM usage records (cus_llm_usage) into daily
    aggregates (cus_usage_daily) for efficient reporting and dashboards.

IMPORTANT:
    This script produces DERIVED DATA for REPORTING ONLY.
    cus_usage_daily is NEVER used for enforcement decisions.
    Enforcement always queries cus_llm_usage directly.

SCHEDULE:
    Run hourly via cron to keep aggregates fresh.
    Can also be run manually for backfill.

USAGE:
    # Aggregate yesterday's data
    python cus_usage_aggregator.py

    # Aggregate specific date
    python cus_usage_aggregator.py --date 2026-01-15

    # Aggregate date range (backfill)
    python cus_usage_aggregator.py --from 2026-01-01 --to 2026-01-15

    # Dry run (show what would be aggregated)
    python cus_usage_aggregator.py --dry-run

CRON EXAMPLE:
    # Run every hour at minute 5
    5 * * * * cd /app/backend && python scripts/cus_usage_aggregator.py >> /var/log/cus_aggregator.log 2>&1
"""

import argparse
import json
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

# Setup path for imports
sys.path.insert(0, "/root/agenticverz2.0/backend")

from sqlmodel import Session, func, select

from app.db import get_engine
from app.models.cus_models import CusLLMUsage, CusUsageDaily

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder for datetime objects."""

    def default(self, o: Any) -> Any:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


def aggregate_day(
    session: Session,
    target_date: date,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Aggregate usage for a single day.

    Args:
        session: Database session
        target_date: Date to aggregate
        dry_run: If True, don't write to database

    Returns:
        Summary of aggregation
    """
    logger.info(f"Aggregating usage for {target_date}")

    # Query aggregated data grouped by tenant and integration
    query = (
        select(
            CusLLMUsage.tenant_id,
            CusLLMUsage.integration_id,
            func.count().label("total_calls"),
            func.sum(CusLLMUsage.tokens_in).label("total_tokens_in"),
            func.sum(CusLLMUsage.tokens_out).label("total_tokens_out"),
            func.sum(CusLLMUsage.cost_cents).label("total_cost_cents"),
            func.avg(CusLLMUsage.latency_ms).label("avg_latency_ms"),
            func.sum(
                func.case((CusLLMUsage.error_code.isnot(None), 1), else_=0)
            ).label("error_count"),
            func.sum(
                func.case((CusLLMUsage.policy_result == "blocked", 1), else_=0)
            ).label("blocked_count"),
        )
        .where(func.date(CusLLMUsage.created_at) == target_date)
        .group_by(CusLLMUsage.tenant_id, CusLLMUsage.integration_id)
    )

    results = session.exec(query).all()

    aggregates_created = 0
    aggregates_updated = 0

    for row in results:
        tenant_id = row.tenant_id
        integration_id = row.integration_id

        aggregate_data = {
            "total_calls": row.total_calls or 0,
            "total_tokens_in": int(row.total_tokens_in or 0),
            "total_tokens_out": int(row.total_tokens_out or 0),
            "total_cost_cents": int(row.total_cost_cents or 0),
            "avg_latency_ms": int(row.avg_latency_ms) if row.avg_latency_ms else None,
            "error_count": int(row.error_count or 0),
            "blocked_count": int(row.blocked_count or 0),
        }

        if dry_run:
            logger.info(
                f"  [DRY RUN] Would aggregate {tenant_id}/{integration_id}: "
                f"{aggregate_data['total_calls']} calls, "
                f"{aggregate_data['total_cost_cents']}¢"
            )
            aggregates_created += 1
            continue

        # Check if aggregate exists
        existing = session.exec(
            select(CusUsageDaily).where(
                CusUsageDaily.tenant_id == tenant_id,
                CusUsageDaily.integration_id == integration_id,
                CusUsageDaily.date == target_date,
            )
        ).first()

        if existing:
            # Update existing
            existing.total_calls = aggregate_data["total_calls"]
            existing.total_tokens_in = aggregate_data["total_tokens_in"]
            existing.total_tokens_out = aggregate_data["total_tokens_out"]
            existing.total_cost_cents = aggregate_data["total_cost_cents"]
            existing.avg_latency_ms = aggregate_data["avg_latency_ms"]
            existing.error_count = aggregate_data["error_count"]
            existing.blocked_count = aggregate_data["blocked_count"]
            existing.updated_at = datetime.now(timezone.utc)
            session.add(existing)
            aggregates_updated += 1
        else:
            # Create new
            aggregate = CusUsageDaily(
                tenant_id=tenant_id,
                integration_id=integration_id,
                date=target_date,
                **aggregate_data,
            )
            session.add(aggregate)
            aggregates_created += 1

    if not dry_run:
        session.commit()

    summary = {
        "date": target_date,
        "records_processed": len(results),
        "aggregates_created": aggregates_created,
        "aggregates_updated": aggregates_updated,
    }

    logger.info(
        f"Completed {target_date}: "
        f"{summary['records_processed']} groups, "
        f"{aggregates_created} created, {aggregates_updated} updated"
    )

    return summary


def aggregate_range(
    start_date: date,
    end_date: date,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    """Aggregate usage for a date range.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        dry_run: If True, don't write to database

    Returns:
        List of summaries for each day
    """
    engine = get_engine()
    summaries: List[Dict[str, Any]] = []

    current = start_date
    while current <= end_date:
        with Session(engine) as session:
            summary = aggregate_day(session, current, dry_run)
            summaries.append(summary)
        current += timedelta(days=1)

    return summaries


def get_missing_dates(
    lookback_days: int = 30,
) -> List[date]:
    """Find dates that have usage but no aggregates.

    Args:
        lookback_days: How many days to look back

    Returns:
        List of dates needing aggregation
    """
    engine = get_engine()
    missing: List[date] = []

    with Session(engine) as session:
        # Get dates with usage
        cutoff = date.today() - timedelta(days=lookback_days)

        usage_dates_query = (
            select(func.date(CusLLMUsage.created_at).label("usage_date"))
            .where(func.date(CusLLMUsage.created_at) >= cutoff)
            .distinct()
        )
        usage_dates = {row.usage_date for row in session.exec(usage_dates_query).all()}

        # Get dates with aggregates
        aggregate_dates_query = (
            select(CusUsageDaily.date).where(CusUsageDaily.date >= cutoff).distinct()
        )
        aggregate_dates = {row for row in session.exec(aggregate_dates_query).all()}

        # Find missing
        missing = sorted(usage_dates - aggregate_dates)

    return missing


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(
        description="Aggregate customer LLM usage into daily summaries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Date selection
    parser.add_argument(
        "--date",
        "-d",
        type=str,
        help="Specific date to aggregate (YYYY-MM-DD). Default: yesterday",
    )
    parser.add_argument(
        "--from",
        dest="from_date",
        type=str,
        help="Start date for range aggregation (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--to",
        dest="to_date",
        type=str,
        help="End date for range aggregation (YYYY-MM-DD)",
    )

    # Options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be aggregated without writing",
    )
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Find and aggregate all missing dates",
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=30,
        help="Days to look back for backfill (default: 30)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        if args.backfill:
            # Find and aggregate missing dates
            missing = get_missing_dates(args.lookback)

            if not missing:
                logger.info("No missing dates found")
                if args.json:
                    print(json.dumps({"status": "ok", "missing_dates": []}))
                return 0

            logger.info(f"Found {len(missing)} missing dates: {missing}")

            summaries = []
            for target_date in missing:
                engine = get_engine()
                with Session(engine) as session:
                    summary = aggregate_day(session, target_date, args.dry_run)
                    summaries.append(summary)

            if args.json:
                print(
                    json.dumps(
                        {"status": "ok", "summaries": summaries},
                        cls=DateTimeEncoder,
                        indent=2,
                    )
                )

        elif args.from_date and args.to_date:
            # Range aggregation
            start = date.fromisoformat(args.from_date)
            end = date.fromisoformat(args.to_date)

            if start > end:
                logger.error("Start date must be before end date")
                return 1

            summaries = aggregate_range(start, end, args.dry_run)

            if args.json:
                print(
                    json.dumps(
                        {"status": "ok", "summaries": summaries},
                        cls=DateTimeEncoder,
                        indent=2,
                    )
                )

        else:
            # Single date aggregation
            if args.date:
                target_date = date.fromisoformat(args.date)
            else:
                # Default to yesterday
                target_date = date.today() - timedelta(days=1)

            engine = get_engine()
            with Session(engine) as session:
                summary = aggregate_day(session, target_date, args.dry_run)

            if args.json:
                print(
                    json.dumps(
                        {"status": "ok", "summary": summary},
                        cls=DateTimeEncoder,
                        indent=2,
                    )
                )

        return 0

    except Exception as e:
        logger.exception(f"Aggregation failed: {e}")
        if args.json:
            print(json.dumps({"status": "error", "error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
