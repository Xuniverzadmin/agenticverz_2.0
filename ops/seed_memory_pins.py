#!/usr/bin/env python3
"""
Memory Pins Seeder - M7 Implementation (Enhanced)

Idempotent seeder for memory pins that uses machine JWT or token.
Supports bypass when RBAC is in staging mode.

Features:
- Health check with wait for API availability
- API-based verification
- Direct SQL verification (optional)
- Retry logic for transient failures
- Detailed reporting

Usage:
    # With machine JWT
    MACHINE_JWT=<token> python3 seed_memory_pins.py \
        --file ops/memory_pins_seed.json \
        --base http://localhost:8000

    # With machine token header
    MACHINE_TOKEN=<token> python3 seed_memory_pins.py \
        --file ops/memory_pins_seed.json \
        --base http://localhost:8000

    # Full verification (API + SQL)
    MACHINE_TOKEN=<token> DATABASE_URL=postgresql://user:pass@host/db \
        python3 seed_memory_pins.py \
        --file ops/memory_pins_seed.json \
        --base http://localhost:8000 \
        --verify \
        --sql-verify

    # Dry run (no changes)
    python3 seed_memory_pins.py --file ops/memory_pins_seed.json --base http://localhost:8000 --dry-run

Environment Variables:
    MACHINE_JWT       - JWT token for authorization
    MACHINE_TOKEN     - Alternative: plain token for X-Machine-Token header
    SEED_TIMEOUT      - Request timeout in seconds (default: 10)
    SEED_RETRIES      - Number of retries for failed requests (default: 3)
    SEED_WAIT_TIMEOUT - Timeout for waiting for API (default: 30)
    DATABASE_URL      - PostgreSQL connection string for SQL verification
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("seed_memory_pins")

# Configuration
SEED_TIMEOUT = float(os.getenv("SEED_TIMEOUT", "10"))
SEED_RETRIES = int(os.getenv("SEED_RETRIES", "3"))
SEED_WAIT_TIMEOUT = int(os.getenv("SEED_WAIT_TIMEOUT", "30"))


def wait_for_api(base_url: str, timeout: int = None) -> bool:
    """
    Wait for API to become available.

    Args:
        base_url: API base URL
        timeout: Maximum wait time in seconds

    Returns:
        True if API became available, False if timeout
    """
    if timeout is None:
        timeout = SEED_WAIT_TIMEOUT

    health_endpoints = [
        f"{base_url}/health",
        f"{base_url}/ready",
        f"{base_url}/api/v1/memory/pins",  # Memory pins endpoint
    ]

    start_time = time.time()
    logger.info(f"Waiting for API at {base_url} (timeout: {timeout}s)...")

    while time.time() - start_time < timeout:
        for endpoint in health_endpoints:
            try:
                response = requests.get(endpoint, timeout=3)
                if response.status_code < 500:
                    logger.info(f"API available at {endpoint} (status: {response.status_code})")
                    return True
            except requests.exceptions.RequestException:
                pass

        time.sleep(1.0)

    logger.error(f"API not available after {timeout}s")
    return False


def retry_request(
    func,
    *args,
    retries: int = None,
    delay: float = 1.0,
    **kwargs
) -> Any:
    """
    Retry a request function with exponential backoff.

    Args:
        func: Function to call
        retries: Number of retries
        delay: Initial delay between retries
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result of func

    Raises:
        Last exception if all retries fail
    """
    if retries is None:
        retries = SEED_RETRIES

    last_exception = None

    for attempt in range(retries + 1):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            last_exception = e
            if attempt < retries:
                wait_time = delay * (2 ** attempt)
                logger.warning(f"Request failed (attempt {attempt + 1}/{retries + 1}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                logger.error(f"Request failed after {retries + 1} attempts: {e}")

    raise last_exception


def verify_pin_sql(tenant_id: str, key: str) -> Optional[Dict[str, Any]]:
    """
    Verify a pin exists using direct SQL query.

    Requires DATABASE_URL environment variable.

    Returns:
        Pin data if found, None otherwise
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.debug("DATABASE_URL not set, skipping SQL verification")
        return None

    try:
        import psycopg2
        import psycopg2.extras

        conn = psycopg2.connect(database_url)
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT tenant_id, key, value, source, created_at, updated_at, ttl_seconds, expires_at
                    FROM system.memory_pins
                    WHERE tenant_id = %s AND key = %s
                      AND (expires_at IS NULL OR expires_at > now())
                """, (tenant_id, key))
                row = cur.fetchone()
                if row:
                    return dict(row)
                return None
        finally:
            conn.close()

    except ImportError:
        logger.warning("psycopg2 not installed, skipping SQL verification")
        return None
    except Exception as e:
        logger.error(f"SQL verification error: {e}")
        return None


def load_seed_file(path: str) -> List[Dict[str, Any]]:
    """Load seed data from JSON file."""
    with open(path, "r") as f:
        data = json.load(f)

    # Support both list format and object with "entries" key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "entries" in data:
        return data["entries"]
    else:
        raise ValueError("Seed file must be a list or object with 'entries' key")


def get_auth_headers() -> Dict[str, str]:
    """Get authorization headers from environment."""
    headers = {"Content-Type": "application/json"}

    # Prefer JWT token
    jwt_token = os.getenv("MACHINE_JWT")
    if jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"
        return headers

    # Fallback to machine token
    machine_token = os.getenv("MACHINE_TOKEN") or os.getenv("MACHINE_SECRET_TOKEN")
    if machine_token:
        headers["X-Machine-Token"] = machine_token
        return headers

    logger.warning("No MACHINE_JWT or MACHINE_TOKEN set - requests may fail with RBAC enabled")
    return headers


def upsert_pin(
    base_url: str,
    tenant_id: str,
    key: str,
    value: Any,
    source: str = "seed",
    ttl_seconds: Optional[int] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Create or update a memory pin.

    Args:
        base_url: API base URL (e.g., http://localhost:8000)
        tenant_id: Tenant identifier
        key: Pin key
        value: Pin value (will be JSON-encoded)
        source: Source identifier
        ttl_seconds: Optional TTL
        dry_run: If True, don't actually make the request

    Returns:
        API response dict or dry-run placeholder
    """
    url = f"{base_url}/api/v1/memory/pins"
    headers = get_auth_headers()
    timeout = float(os.getenv("SEED_TIMEOUT", "10"))

    payload = {
        "tenant_id": tenant_id,
        "key": key,
        "value": value,
        "source": source
    }

    if ttl_seconds is not None:
        payload["ttl_seconds"] = ttl_seconds

    if dry_run:
        logger.info(f"[DRY-RUN] Would upsert: {tenant_id}/{key}")
        return {"dry_run": True, "key": key, "tenant_id": tenant_id}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)

        if response.status_code not in (200, 201):
            logger.error(f"Failed to upsert {tenant_id}/{key}: {response.status_code} - {response.text}")
            response.raise_for_status()

        logger.info(f"Upserted: {tenant_id}/{key}")
        return response.json()

    except requests.exceptions.Timeout:
        logger.error(f"Timeout upserting {tenant_id}/{key}")
        raise
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error upserting {tenant_id}/{key}: {e}")
        raise


def verify_pin(base_url: str, tenant_id: str, key: str) -> Optional[Dict[str, Any]]:
    """Verify a pin exists by fetching it."""
    url = f"{base_url}/api/v1/memory/pins/{key}"
    headers = get_auth_headers()
    timeout = float(os.getenv("SEED_TIMEOUT", "10"))

    try:
        response = requests.get(
            url,
            params={"tenant_id": tenant_id},
            headers=headers,
            timeout=timeout
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            logger.warning(f"Unexpected status {response.status_code} verifying {tenant_id}/{key}")
            return None

    except Exception as e:
        logger.error(f"Error verifying {tenant_id}/{key}: {e}")
        return None


def process_seed_entry(
    base_url: str,
    entry: Dict[str, Any],
    dry_run: bool = False,
    verify: bool = False,
    sql_verify: bool = False
) -> Dict[str, int]:
    """
    Process a single seed entry.

    Entry format:
    {
        "tenant_id": "global",
        "pins": {
            "key1": {"foo": "bar"},
            "key2": {"baz": 123}
        },
        "source": "seed_script",
        "ttl_seconds": null
    }

    Returns:
        Dict with counts: {"success": N, "failed": N, "verified_api": N, "verified_sql": N}
    """
    tenant_id = entry.get("tenant_id", "global")
    pins = entry.get("pins", {})
    source = entry.get("source", "seed_script")
    ttl_seconds = entry.get("ttl_seconds")

    stats = {"success": 0, "failed": 0, "verified_api": 0, "verified_sql": 0}

    for key, value in pins.items():
        try:
            # Use retry wrapper for upsert
            def do_upsert():
                return upsert_pin(
                    base_url=base_url,
                    tenant_id=tenant_id,
                    key=key,
                    value=value,
                    source=source,
                    ttl_seconds=ttl_seconds,
                    dry_run=dry_run
                )

            if dry_run:
                do_upsert()
            else:
                retry_request(do_upsert)

            stats["success"] += 1

            if not dry_run:
                # API verification
                if verify:
                    result = verify_pin(base_url, tenant_id, key)
                    if result:
                        stats["verified_api"] += 1
                        logger.debug(f"API verified: {tenant_id}/{key}")
                    else:
                        logger.warning(f"API verification failed for {tenant_id}/{key}")

                # SQL verification
                if sql_verify:
                    result = verify_pin_sql(tenant_id, key)
                    if result:
                        stats["verified_sql"] += 1
                        logger.debug(f"SQL verified: {tenant_id}/{key}")
                    else:
                        logger.warning(f"SQL verification failed for {tenant_id}/{key}")

        except Exception as e:
            logger.error(f"Failed to process {tenant_id}/{key}: {e}")
            stats["failed"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Seed memory pins from JSON file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Seed to local development
    MACHINE_TOKEN=dev-token python3 seed_memory_pins.py \\
        --file ops/memory_pins_seed.json \\
        --base http://localhost:8000

    # Seed to staging with full verification
    MACHINE_JWT=$STAGING_JWT DATABASE_URL=$DB_URL python3 seed_memory_pins.py \\
        --file ops/memory_pins_seed.json \\
        --base https://staging.example.com \\
        --verify --sql-verify

    # Dry run
    python3 seed_memory_pins.py \\
        --file ops/memory_pins_seed.json \\
        --base http://localhost:8000 \\
        --dry-run

    # Wait for API and seed
    python3 seed_memory_pins.py \\
        --file ops/memory_pins_seed.json \\
        --base http://localhost:8000 \\
        --wait --wait-timeout 60
        """
    )

    parser.add_argument(
        "--file", "-f",
        required=True,
        help="Path to seed JSON file"
    )
    parser.add_argument(
        "--base", "-b",
        required=True,
        help="API base URL (e.g., http://localhost:8000)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually make requests, just log what would happen"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify each pin via API after upserting"
    )
    parser.add_argument(
        "--sql-verify",
        action="store_true",
        help="Verify each pin via direct SQL after upserting (requires DATABASE_URL)"
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for API to become available before seeding"
    )
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=30,
        help="Timeout in seconds to wait for API (default: 30)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Wait for API if requested
    if args.wait:
        if not wait_for_api(args.base, timeout=args.wait_timeout):
            logger.error("API did not become available in time")
            sys.exit(2)

    # Load seed data
    logger.info(f"Loading seed file: {args.file}")
    try:
        entries = load_seed_file(args.file)
    except FileNotFoundError:
        logger.error(f"Seed file not found: {args.file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in seed file: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid seed file format: {e}")
        sys.exit(1)

    logger.info(f"Found {len(entries)} entries to process")

    if args.dry_run:
        logger.info("=== DRY RUN MODE ===")

    # Check if SQL verification is possible
    if args.sql_verify and not os.getenv("DATABASE_URL"):
        logger.warning("--sql-verify specified but DATABASE_URL not set, SQL verification will be skipped")

    # Process entries
    total_stats = {"success": 0, "failed": 0, "verified_api": 0, "verified_sql": 0}

    for i, entry in enumerate(entries, 1):
        tenant_id = entry.get("tenant_id", "global")
        pin_count = len(entry.get("pins", {}))
        logger.info(f"Processing entry {i}/{len(entries)}: tenant={tenant_id}, pins={pin_count}")

        stats = process_seed_entry(
            base_url=args.base,
            entry=entry,
            dry_run=args.dry_run,
            verify=args.verify,
            sql_verify=args.sql_verify
        )

        for k in total_stats:
            total_stats[k] += stats.get(k, 0)

    # Summary
    logger.info("=" * 50)
    logger.info("Seed Complete")
    logger.info(f"  Success:      {total_stats['success']}")
    logger.info(f"  Failed:       {total_stats['failed']}")
    if args.verify:
        logger.info(f"  Verified API: {total_stats['verified_api']}")
    if args.sql_verify:
        logger.info(f"  Verified SQL: {total_stats['verified_sql']}")

    if total_stats["failed"] > 0:
        logger.warning("Some pins failed to seed!")
        sys.exit(1)

    # Verify counts match
    if args.verify and total_stats["verified_api"] < total_stats["success"]:
        logger.warning(f"API verification incomplete: {total_stats['verified_api']}/{total_stats['success']}")
        sys.exit(1)

    if args.sql_verify and os.getenv("DATABASE_URL") and total_stats["verified_sql"] < total_stats["success"]:
        logger.warning(f"SQL verification incomplete: {total_stats['verified_sql']}/{total_stats['success']}")
        sys.exit(1)

    logger.info("All pins seeded and verified successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
