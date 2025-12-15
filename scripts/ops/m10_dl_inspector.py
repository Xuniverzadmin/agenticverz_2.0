#!/usr/bin/env python3
"""
M10 Dead Letter Inspector CLI

Inspects dead_letter_archive and provides safe replay commands with idempotency checks.

Usage:
    # Show top 10 dead letters
    aos-dl top

    # Show details for a specific dead letter
    aos-dl show <id>

    # Safe replay with idempotency check (dry-run)
    aos-dl replay --dry-run

    # Actually replay (with confirmation)
    aos-dl replay --confirm

    # JSON output
    aos-dl top --json

Commands:
    top     - Show top 10 dead letters by failure reason
    show    - Show details for a specific dead letter ID
    replay  - Replay dead letters with idempotency checks
    stats   - Show dead letter statistics

Environment Variables:
    DATABASE_URL: PostgreSQL connection URL (required)
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

logger = logging.getLogger("m10.dl_inspector")

DATABASE_URL = os.getenv("DATABASE_URL")


def get_engine():
    """Get database engine."""
    from sqlmodel import create_engine
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not configured")
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def cmd_top(limit: int = 10, as_json: bool = False) -> dict:
    """Show top dead letters by failure reason."""
    from sqlalchemy import text
    from sqlmodel import Session

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dead_letters": [],
        "summary": {},
        "error": None,
    }

    try:
        engine = get_engine()
        with Session(engine) as session:
            # Get top dead letters
            rows = session.execute(text("""
                SELECT
                    id,
                    original_msg_id,
                    candidate_id,
                    reason,
                    reclaim_count,
                    dead_lettered_at,
                    EXTRACT(EPOCH FROM NOW() - dead_lettered_at) / 3600 as hours_ago
                FROM m10_recovery.dead_letter_archive
                ORDER BY dead_lettered_at DESC
                LIMIT :limit
            """), {"limit": limit}).fetchall()

            for row in rows:
                result["dead_letters"].append({
                    "id": row[0],
                    "original_msg_id": row[1],
                    "candidate_id": row[2],
                    "failure_reason": row[3],
                    "reclaim_count": row[4],
                    "failed_at": row[5].isoformat() if row[5] else None,
                    "hours_ago": round(float(row[6]), 1) if row[6] else 0,
                })

            # Get summary by failure reason
            summary_rows = session.execute(text("""
                SELECT reason, COUNT(*) as count
                FROM m10_recovery.dead_letter_archive
                GROUP BY reason
                ORDER BY count DESC
                LIMIT 10
            """)).fetchall()

            for row in summary_rows:
                result["summary"][row[0] or "unknown"] = row[1]

    except Exception as e:
        result["error"] = str(e)

    if as_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if result["error"]:
            print(f"ERROR: {result['error']}")
            return result

        print("\n=== M10 Dead Letter Inspector ===\n")
        print(f"Top {limit} Dead Letters:\n")
        print(f"{'ID':<8} {'Candidate':<12} {'Reason':<30} {'Hours Ago':<10} {'Reclaims':<8}")
        print("-" * 78)

        for dl in result["dead_letters"]:
            reason = (dl["failure_reason"] or "unknown")[:30]
            print(f"{dl['id']:<8} {dl['candidate_id'] or 'N/A':<12} {reason:<30} {dl['hours_ago']:<10} {dl['reclaim_count']:<8}")

        print(f"\n\nSummary by Failure Reason:")
        print("-" * 40)
        for reason, count in result["summary"].items():
            print(f"  {reason[:35]:<35} {count:>4}")

        print(f"\n\nSafe Replay Command:")
        print(f"  aos-dl replay --dry-run   # Preview what will be replayed")
        print(f"  aos-dl replay --confirm   # Actually replay with idempotency check")

    return result


def cmd_show(dl_id: int, as_json: bool = False) -> dict:
    """Show details for a specific dead letter."""
    from sqlalchemy import text
    from sqlmodel import Session

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dead_letter": None,
        "already_replayed": False,
        "error": None,
    }

    try:
        engine = get_engine()
        with Session(engine) as session:
            # Get dead letter details
            row = session.execute(text("""
                SELECT
                    id, dl_msg_id, original_msg_id, candidate_id,
                    failure_match_id, payload, reason,
                    reclaim_count, dead_lettered_at, archived_by
                FROM m10_recovery.dead_letter_archive
                WHERE id = :id
            """), {"id": dl_id}).fetchone()

            if not row:
                result["error"] = f"Dead letter {dl_id} not found"
                return result

            result["dead_letter"] = {
                "id": row[0],
                "dl_msg_id": row[1],
                "original_msg_id": row[2],
                "candidate_id": row[3],
                "failure_match_id": str(row[4]) if row[4] else None,
                "payload": row[5],
                "failure_reason": row[6],
                "reclaim_count": row[7],
                "failed_at": row[8].isoformat() if row[8] else None,
                "archived_by": row[9],
            }

            # Check if already replayed
            if row[2]:  # original_msg_id
                replay_check = session.execute(text("""
                    SELECT id, replayed_at FROM m10_recovery.replay_log
                    WHERE original_msg_id = :msg_id
                """), {"msg_id": row[2]}).fetchone()

                if replay_check:
                    result["already_replayed"] = True
                    result["replay_info"] = {
                        "replay_id": replay_check[0],
                        "replayed_at": replay_check[1].isoformat() if replay_check[1] else None,
                    }

    except Exception as e:
        result["error"] = str(e)

    if as_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if result["error"]:
            print(f"ERROR: {result['error']}")
            return result

        dl = result["dead_letter"]
        print(f"\n=== Dead Letter #{dl['id']} ===\n")
        print(f"Original Msg ID:   {dl['original_msg_id']}")
        print(f"DL Msg ID:         {dl['dl_msg_id']}")
        print(f"Candidate ID:      {dl['candidate_id']}")
        print(f"Failure Match ID:  {dl['failure_match_id']}")
        print(f"Failure Reason:    {dl['failure_reason']}")
        print(f"Reclaim Count:     {dl['reclaim_count']}")
        print(f"Failed At:         {dl['failed_at']}")
        print(f"Archived By:       {dl['archived_by']}")
        print(f"\nPayload:")
        print(json.dumps(dl['payload'], indent=2) if dl['payload'] else "  (empty)")

        if result["already_replayed"]:
            print(f"\n⚠️  ALREADY REPLAYED:")
            print(f"   Replay ID: {result['replay_info']['replay_id']}")
            print(f"   Replayed At: {result['replay_info']['replayed_at']}")
        else:
            print(f"\n✓ Not yet replayed - safe to replay")

    return result


def cmd_replay(dry_run: bool = True, confirm: bool = False, limit: int = 10, as_json: bool = False) -> dict:
    """Replay dead letters with idempotency checks."""
    from sqlalchemy import text
    from sqlmodel import Session

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "candidates": [],
        "replayed": [],
        "skipped_already_replayed": [],
        "error": None,
    }

    if not dry_run and not confirm:
        result["error"] = "Must use --confirm to actually replay"
        if not as_json:
            print("ERROR: Must use --confirm to actually replay dead letters")
            print("       Use --dry-run first to preview what will be replayed")
        return result

    try:
        engine = get_engine()
        with Session(engine) as session:
            # Get dead letters that haven't been replayed yet
            rows = session.execute(text("""
                SELECT
                    dla.id,
                    dla.original_msg_id,
                    dla.candidate_id,
                    dla.reason,
                    dla.payload,
                    rl.id as replay_id
                FROM m10_recovery.dead_letter_archive dla
                LEFT JOIN m10_recovery.replay_log rl
                    ON dla.original_msg_id = rl.original_msg_id
                ORDER BY dla.dead_lettered_at DESC
                LIMIT :limit
            """), {"limit": limit}).fetchall()

            for row in rows:
                dl_info = {
                    "id": row[0],
                    "original_msg_id": row[1],
                    "candidate_id": row[2],
                    "failure_reason": row[3],
                }

                if row[5]:  # Already has replay entry
                    result["skipped_already_replayed"].append(dl_info)
                else:
                    result["candidates"].append(dl_info)

                    if not dry_run and confirm:
                        # Record replay (idempotent - will fail if already exists)
                        try:
                            session.execute(text("""
                                SELECT m10_recovery.record_replay(
                                    :original_msg_id,
                                    :dl_msg_id,
                                    :candidate_id,
                                    gen_random_uuid(),
                                    :new_msg_id,
                                    'dl_inspector_cli'
                                )
                            """), {
                                "original_msg_id": row[1],
                                "dl_msg_id": None,
                                "candidate_id": row[2],
                                "new_msg_id": f"replay-{row[0]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                            })
                            result["replayed"].append(dl_info)
                        except Exception as e:
                            dl_info["replay_error"] = str(e)

            if not dry_run and confirm:
                session.commit()

    except Exception as e:
        result["error"] = str(e)

    if as_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if result["error"]:
            print(f"ERROR: {result['error']}")
            return result

        print(f"\n=== M10 Dead Letter Replay {'(DRY RUN)' if dry_run else ''} ===\n")

        print(f"Candidates for replay: {len(result['candidates'])}")
        for dl in result["candidates"][:5]:
            print(f"  - #{dl['id']}: candidate={dl['candidate_id']}, reason={dl['failure_reason'][:40]}")
        if len(result["candidates"]) > 5:
            print(f"  ... and {len(result['candidates']) - 5} more")

        print(f"\nSkipped (already replayed): {len(result['skipped_already_replayed'])}")

        if not dry_run:
            print(f"\nActually replayed: {len(result['replayed'])}")
        else:
            print(f"\nTo actually replay, run:")
            print(f"  aos-dl replay --confirm")

    return result


def cmd_stats(as_json: bool = False) -> dict:
    """Show dead letter statistics."""
    from sqlalchemy import text
    from sqlmodel import Session

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_dead_letters": 0,
        "total_replayed": 0,
        "pending_replay": 0,
        "by_reason": {},
        "by_day": [],
        "error": None,
    }

    try:
        engine = get_engine()
        with Session(engine) as session:
            # Total counts
            row = session.execute(text("""
                SELECT
                    (SELECT COUNT(*) FROM m10_recovery.dead_letter_archive) as total_dl,
                    (SELECT COUNT(*) FROM m10_recovery.replay_log) as total_replayed
            """)).fetchone()

            result["total_dead_letters"] = row[0] if row else 0
            result["total_replayed"] = row[1] if row else 0
            result["pending_replay"] = result["total_dead_letters"] - result["total_replayed"]

            # By reason
            rows = session.execute(text("""
                SELECT reason, COUNT(*)
                FROM m10_recovery.dead_letter_archive
                GROUP BY reason
                ORDER BY count DESC
            """)).fetchall()

            for row in rows:
                result["by_reason"][row[0] or "unknown"] = row[1]

            # By day (last 7 days)
            rows = session.execute(text("""
                SELECT
                    DATE(dead_lettered_at) as day,
                    COUNT(*) as count
                FROM m10_recovery.dead_letter_archive
                WHERE dead_lettered_at > NOW() - INTERVAL '7 days'
                GROUP BY DATE(dead_lettered_at)
                ORDER BY day DESC
            """)).fetchall()

            for row in rows:
                result["by_day"].append({
                    "date": row[0].isoformat() if row[0] else None,
                    "count": row[1],
                })

    except Exception as e:
        result["error"] = str(e)

    if as_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if result["error"]:
            print(f"ERROR: {result['error']}")
            return result

        print(f"\n=== M10 Dead Letter Statistics ===\n")
        print(f"Total Dead Letters:    {result['total_dead_letters']}")
        print(f"Total Replayed:        {result['total_replayed']}")
        print(f"Pending Replay:        {result['pending_replay']}")

        print(f"\nBy Failure Reason:")
        for reason, count in list(result["by_reason"].items())[:10]:
            print(f"  {reason[:40]:<40} {count:>4}")

        print(f"\nLast 7 Days:")
        for day in result["by_day"]:
            print(f"  {day['date']}: {day['count']} dead letters")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="M10 Dead Letter Inspector CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aos-dl top              # Show top 10 dead letters
  aos-dl top --limit 20   # Show top 20
  aos-dl show 123         # Show details for DL #123
  aos-dl replay --dry-run # Preview replay candidates
  aos-dl replay --confirm # Actually replay
  aos-dl stats            # Show statistics
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # top command
    top_parser = subparsers.add_parser("top", help="Show top dead letters")
    top_parser.add_argument("--limit", type=int, default=10, help="Number of entries to show")
    top_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # show command
    show_parser = subparsers.add_parser("show", help="Show details for a dead letter")
    show_parser.add_argument("id", type=int, help="Dead letter ID")
    show_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # replay command
    replay_parser = subparsers.add_parser("replay", help="Replay dead letters")
    replay_parser.add_argument("--dry-run", action="store_true", help="Preview only")
    replay_parser.add_argument("--confirm", action="store_true", help="Actually replay")
    replay_parser.add_argument("--limit", type=int, default=10, help="Max entries to replay")
    replay_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "top":
            cmd_top(limit=args.limit, as_json=args.json)
        elif args.command == "show":
            cmd_show(dl_id=args.id, as_json=args.json)
        elif args.command == "replay":
            cmd_replay(dry_run=args.dry_run, confirm=args.confirm, limit=args.limit, as_json=args.json)
        elif args.command == "stats":
            cmd_stats(as_json=args.json)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
