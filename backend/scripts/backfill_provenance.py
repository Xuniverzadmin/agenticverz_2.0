#!/usr/bin/env python3
"""
Provenance Backfill Script for CostSim V2 (M6)

This script backfills V1 baseline provenance records from:
1. File-based provenance logs (/var/lib/aos/provenance/*.jsonl)
2. Historical run data from the provenance table
3. Manual JSON input files

Usage:
    # Backfill from file-based provenance logs
    python3 scripts/backfill_provenance.py --dir /var/lib/aos/provenance

    # Backfill from a specific JSON file
    python3 scripts/backfill_provenance.py --file historical_runs.json

    # Dry-run mode (preview without writing)
    python3 scripts/backfill_provenance.py --dir /var/lib/aos/provenance --dry-run

    # Verify backfill results
    python3 scripts/backfill_provenance.py --verify

Requirements:
    - DATABASE_URL environment variable set
    - Migration 008 applied (costsim_provenance table exists)
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("backfill_provenance")


def compute_input_hash(payload: Dict[str, Any]) -> str:
    """Compute deterministic hash of input payload."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


def load_jsonl_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load records from a JSONL file."""
    records = []
    try:
        with open(file_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON at {file_path}:{line_num}: {e}")
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
    return records


def transform_provenance_log(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform file-based provenance log to DB format.

    File-based format (provenance.py):
        - id, timestamp, input_hash, output_hash
        - input_json, output_json, compressed
        - model_version, adapter_version, commit_sha
        - runtime_ms, status, tenant_id, run_id, plan_hash

    DB format (CostSimProvenanceModel):
        - run_id, tenant_id, variant_slug, source
        - model_version, adapter_version, commit_sha
        - input_hash, output_hash
        - v1_cost, v2_cost, cost_delta
        - payload, runtime_ms
    """
    # Extract cost from output if available
    v1_cost = None
    try:
        output = record.get("output_json", "{}")
        if record.get("compressed", False):
            import base64
            import gzip

            decoded = base64.b64decode(output)
            output = gzip.decompress(decoded).decode()

        output_data = json.loads(output) if isinstance(output, str) else output
        v1_cost = output_data.get("estimated_cost_cents")
    except Exception:
        pass

    # Extract input for payload
    payload = None
    try:
        input_json = record.get("input_json", "{}")
        if record.get("compressed", False):
            import base64
            import gzip

            decoded = base64.b64decode(input_json)
            input_json = gzip.decompress(decoded).decode()
        payload = json.loads(input_json) if isinstance(input_json, str) else input_json
    except Exception:
        pass

    return {
        "run_id": record.get("run_id"),
        "tenant_id": record.get("tenant_id"),
        "variant_slug": "v1",
        "source": "backfill",
        "model_version": record.get("model_version"),
        "adapter_version": record.get("adapter_version"),
        "commit_sha": record.get("commit_sha"),
        "input_hash": record.get("input_hash") or record.get("plan_hash"),
        "output_hash": record.get("output_hash"),
        "v1_cost": float(v1_cost) if v1_cost is not None else None,
        "v2_cost": None,  # V2 will be populated during comparison
        "payload": payload,
        "runtime_ms": record.get("runtime_ms"),
    }


def transform_historical_run(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform historical run data to DB format.

    Historical format (from various sources):
        - plan: simulation plan
        - cost_cents: estimated cost
        - duration_ms: estimated duration
        - tenant_id, run_id
    """
    plan = record.get("plan", {})
    input_hash = record.get("input_hash") or compute_input_hash(plan)

    return {
        "run_id": record.get("run_id"),
        "tenant_id": record.get("tenant_id"),
        "variant_slug": "v1",
        "source": "backfill",
        "input_hash": input_hash,
        "v1_cost": float(record.get("cost_cents", 0)) if record.get("cost_cents") is not None else None,
        "v2_cost": None,
        "payload": {"plan": plan} if plan else None,
        "runtime_ms": record.get("duration_ms"),
    }


async def backfill_from_directory(
    directory: Path,
    dry_run: bool = False,
    batch_size: int = 100,
) -> Dict[str, int]:
    """
    Backfill provenance records from a directory of JSONL files.

    Args:
        directory: Path to directory containing provenance_*.jsonl files
        dry_run: If True, preview without writing to DB
        batch_size: Records per batch

    Returns:
        Statistics dictionary
    """
    from app.costsim.provenance_async import check_duplicate, write_provenance

    stats = {"files": 0, "records": 0, "inserted": 0, "skipped": 0, "errors": 0}

    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return stats

    # Find all provenance files
    files = sorted(directory.glob("provenance_*.jsonl"))
    logger.info(f"Found {len(files)} provenance files in {directory}")

    for file_path in files:
        stats["files"] += 1
        logger.info(f"Processing {file_path.name}...")

        records = load_jsonl_file(file_path)
        stats["records"] += len(records)

        for record in records:
            try:
                transformed = transform_provenance_log(record)
                input_hash = transformed.get("input_hash")

                # Check for duplicate
                if input_hash and await check_duplicate(input_hash):
                    stats["skipped"] += 1
                    continue

                if dry_run:
                    logger.debug(f"[DRY-RUN] Would insert: {input_hash}")
                    stats["inserted"] += 1
                else:
                    await write_provenance(**transformed)
                    stats["inserted"] += 1

            except Exception as e:
                logger.error(f"Failed to process record: {e}")
                stats["errors"] += 1

    return stats


async def backfill_from_file(
    file_path: Path,
    dry_run: bool = False,
) -> Dict[str, int]:
    """
    Backfill from a single JSON or JSONL file.

    Args:
        file_path: Path to input file
        dry_run: If True, preview without writing to DB

    Returns:
        Statistics dictionary
    """
    from app.costsim.provenance_async import check_duplicate, write_provenance

    stats = {"records": 0, "inserted": 0, "skipped": 0, "errors": 0}

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return stats

    # Detect file format
    if file_path.suffix == ".jsonl":
        records = load_jsonl_file(file_path)
    else:
        with open(file_path, "r") as f:
            data = json.load(f)
            records = data if isinstance(data, list) else [data]

    stats["records"] = len(records)
    logger.info(f"Loaded {len(records)} records from {file_path}")

    for record in records:
        try:
            # Detect format and transform
            if "input_json" in record:
                transformed = transform_provenance_log(record)
            else:
                transformed = transform_historical_run(record)

            input_hash = transformed.get("input_hash")

            # Check for duplicate
            if input_hash and await check_duplicate(input_hash):
                stats["skipped"] += 1
                continue

            if dry_run:
                logger.debug(f"[DRY-RUN] Would insert: {input_hash}")
                stats["inserted"] += 1
            else:
                await write_provenance(**transformed)
                stats["inserted"] += 1

        except Exception as e:
            logger.error(f"Failed to process record: {e}")
            stats["errors"] += 1

    return stats


async def verify_backfill() -> Dict[str, Any]:
    """
    Verify the provenance backfill by checking DB counts and data quality.

    Returns:
        Verification results dictionary
    """
    from app.costsim.provenance_async import count_provenance, get_drift_stats, query_provenance

    results = {
        "verified": False,
        "total_records": 0,
        "v1_records": 0,
        "v1_with_cost": 0,
        "sample_records": [],
        "drift_stats": {},
    }

    # Get total counts
    results["total_records"] = await count_provenance()
    results["v1_records"] = await count_provenance(variant_slug="v1")

    # Get sample records to verify data
    samples = await query_provenance(variant_slug="v1", limit=5)
    results["sample_records"] = samples

    # Count records with v1_cost
    samples_with_cost = await query_provenance(limit=1000)
    results["v1_with_cost"] = sum(1 for s in samples_with_cost if s.get("v1_cost") is not None)

    # Get drift stats
    results["drift_stats"] = await get_drift_stats()

    # Verification checks
    results["verified"] = results["total_records"] > 0 and results["v1_records"] > 0

    return results


async def run_psql_verification():
    """Run direct psql verification queries."""
    import subprocess

    db_url = os.environ.get("DATABASE_URL", "")

    if not db_url:
        logger.error("DATABASE_URL not set")
        return

    queries = [
        ("Total records", "SELECT count(*) FROM costsim_provenance;"),
        ("V1 records", "SELECT count(*) FROM costsim_provenance WHERE variant_slug = 'v1';"),
        ("Records with v1_cost", "SELECT count(*) FROM costsim_provenance WHERE v1_cost IS NOT NULL;"),
        (
            "Sample records",
            """
            SELECT id, run_id, variant_slug, v1_cost, v2_cost, created_at
            FROM costsim_provenance
            ORDER BY created_at DESC
            LIMIT 5;
        """,
        ),
    ]

    for name, query in queries:
        print(f"\n--- {name} ---")
        try:
            result = subprocess.run(
                ["psql", db_url, "-c", query],
                capture_output=True,
                text=True,
                timeout=30,
            )
            print(result.stdout)
            if result.stderr:
                print(f"Error: {result.stderr}")
        except Exception as e:
            print(f"Failed to run query: {e}")


async def main():
    parser = argparse.ArgumentParser(description="Backfill V1 baseline provenance records for CostSim V2")
    parser.add_argument(
        "--dir",
        type=Path,
        help="Directory containing provenance_*.jsonl files",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Single JSON or JSONL file to backfill",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without writing to database",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify backfill results",
    )
    parser.add_argument(
        "--psql",
        action="store_true",
        help="Run direct psql verification queries",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Records per batch (default: 100)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check DATABASE_URL
    if not os.environ.get("DATABASE_URL"):
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)

    # Run psql verification
    if args.psql:
        await run_psql_verification()
        return

    # Verify mode
    if args.verify:
        logger.info("Verifying provenance backfill...")
        results = await verify_backfill()

        print("\n" + "=" * 60)
        print("PROVENANCE BACKFILL VERIFICATION")
        print("=" * 60)
        print(f"Total records:     {results['total_records']}")
        print(f"V1 records:        {results['v1_records']}")
        print(f"V1 with cost:      {results['v1_with_cost']}")
        print(f"Verified:          {'PASS' if results['verified'] else 'FAIL'}")

        if results["drift_stats"]:
            print("\nDrift Statistics:")
            for key, value in results["drift_stats"].items():
                print(f"  {key}: {value}")

        if results["sample_records"]:
            print("\nSample Records:")
            for record in results["sample_records"][:3]:
                print(
                    f"  - id={record['id']}, v1_cost={record.get('v1_cost')}, "
                    f"input_hash={record.get('input_hash', '')[:8]}..."
                )

        print("=" * 60)

        # Exit code based on verification
        sys.exit(0 if results["verified"] else 1)

    # Backfill mode
    if args.dir:
        logger.info(f"Backfilling from directory: {args.dir}")
        if args.dry_run:
            logger.info("[DRY-RUN MODE] No changes will be made")

        stats = await backfill_from_directory(
            args.dir,
            dry_run=args.dry_run,
            batch_size=args.batch_size,
        )

        print("\n" + "=" * 60)
        print("BACKFILL SUMMARY")
        print("=" * 60)
        print(f"Files processed:  {stats['files']}")
        print(f"Records found:    {stats['records']}")
        print(f"Inserted:         {stats['inserted']}")
        print(f"Skipped (dup):    {stats['skipped']}")
        print(f"Errors:           {stats['errors']}")
        print("=" * 60)

    elif args.file:
        logger.info(f"Backfilling from file: {args.file}")
        if args.dry_run:
            logger.info("[DRY-RUN MODE] No changes will be made")

        stats = await backfill_from_file(args.file, dry_run=args.dry_run)

        print("\n" + "=" * 60)
        print("BACKFILL SUMMARY")
        print("=" * 60)
        print(f"Records found:    {stats['records']}")
        print(f"Inserted:         {stats['inserted']}")
        print(f"Skipped (dup):    {stats['skipped']}")
        print(f"Errors:           {stats['errors']}")
        print("=" * 60)

    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python3 scripts/backfill_provenance.py --dir /var/lib/aos/provenance")
        print("  python3 scripts/backfill_provenance.py --file historical.json")
        print("  python3 scripts/backfill_provenance.py --verify")
        print("  python3 scripts/backfill_provenance.py --psql")


if __name__ == "__main__":
    asyncio.run(main())
