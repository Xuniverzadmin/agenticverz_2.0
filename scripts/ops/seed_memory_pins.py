#!/usr/bin/env python3
"""
Idempotent memory pins seeder for AOS M7.

Usage:
    # Basic seeding
    python3 seed_memory_pins.py --file memory_pins_seed.json --base http://localhost:8000

    # With verification
    python3 seed_memory_pins.py --file memory_pins_seed.json --base http://localhost:8000 --verify

    # With wait for API and SQL verification
    DATABASE_URL=postgresql://user:pass@host/db python3 seed_memory_pins.py \\
        --file memory_pins_seed.json --base http://localhost:8000 --wait --verify --sql-verify

    # Dry run (no changes)
    python3 seed_memory_pins.py --file memory_pins_seed.json --base http://localhost:8000 --dry-run

Environment:
    MACHINE_SECRET_TOKEN - Token for machine auth (optional, used if X-Machine-Token header needed)
    DATABASE_URL - PostgreSQL connection string (for --sql-verify)
"""

import argparse
import json
import os
import sys
import time
from typing import Optional
from urllib.parse import urljoin

import requests


def wait_for_api(base_url: str, timeout: int = 30, interval: int = 2) -> bool:
    """Wait for API to be healthy."""
    health_url = urljoin(base_url, "/health")
    start = time.time()

    while time.time() - start < timeout:
        try:
            resp = requests.get(health_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "healthy":
                    print(f"✓ API healthy at {base_url}")
                    return True
        except requests.RequestException:
            pass

        print(f"  Waiting for API... ({int(time.time() - start)}s)")
        time.sleep(interval)

    print(f"✗ API not healthy after {timeout}s")
    return False


def upsert_pin(base_url: str, pin: dict, token: Optional[str], dry_run: bool) -> tuple[bool, str]:
    """Upsert a single memory pin."""
    url = urljoin(base_url, "/api/v1/memory/pins")
    headers = {"Content-Type": "application/json"}

    if token:
        headers["X-Machine-Token"] = token

    if dry_run:
        return True, f"[DRY-RUN] Would upsert: {pin['tenant_id']}:{pin['key']}"

    try:
        resp = requests.post(url, json=pin, headers=headers, timeout=10)

        if resp.status_code in (200, 201):
            data = resp.json()
            return True, f"✓ Upserted: {pin['tenant_id']}:{pin['key']} (id={data.get('id')})"
        else:
            return False, f"✗ Failed: {pin['tenant_id']}:{pin['key']} - {resp.status_code}: {resp.text[:200]}"

    except requests.RequestException as e:
        return False, f"✗ Error: {pin['tenant_id']}:{pin['key']} - {e}"


def verify_pin(base_url: str, pin: dict, token: Optional[str]) -> tuple[bool, str]:
    """Verify a pin exists via API."""
    key = pin["key"]
    tenant_id = pin["tenant_id"]
    url = urljoin(base_url, f"/api/v1/memory/pins/{key}?tenant_id={tenant_id}")
    headers = {}

    if token:
        headers["X-Machine-Token"] = token

    try:
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            if data.get("key") == key and data.get("tenant_id") == tenant_id:
                return True, f"✓ Verified: {tenant_id}:{key}"
            return False, f"✗ Mismatch: {tenant_id}:{key} - got {data}"
        else:
            return False, f"✗ Not found: {tenant_id}:{key} - {resp.status_code}"

    except requests.RequestException as e:
        return False, f"✗ Error verifying: {tenant_id}:{key} - {e}"


def verify_sql(database_url: str, pins: list[dict]) -> tuple[int, int]:
    """Verify pins exist in database via SQL."""
    try:
        import psycopg2
    except ImportError:
        print("  Warning: psycopg2 not installed, skipping SQL verification")
        return 0, 0

    success = 0
    failed = 0

    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        for pin in pins:
            cur.execute(
                "SELECT id, key FROM system.memory_pins WHERE tenant_id = %s AND key = %s",
                (pin["tenant_id"], pin["key"])
            )
            row = cur.fetchone()

            if row:
                print(f"  ✓ SQL verified: {pin['tenant_id']}:{pin['key']} (id={row[0]})")
                success += 1
            else:
                print(f"  ✗ SQL missing: {pin['tenant_id']}:{pin['key']}")
                failed += 1

        cur.close()
        conn.close()

    except Exception as e:
        print(f"  ✗ SQL verification error: {e}")
        return 0, len(pins)

    return success, failed


def main():
    parser = argparse.ArgumentParser(description="Seed memory pins for AOS")
    parser.add_argument("--file", "-f", required=True, help="JSON file with pins to seed")
    parser.add_argument("--base", "-b", required=True, help="Base URL of AOS API")
    parser.add_argument("--verify", "-v", action="store_true", help="Verify pins after seeding")
    parser.add_argument("--sql-verify", action="store_true", help="Verify pins in database via SQL")
    parser.add_argument("--wait", "-w", action="store_true", help="Wait for API to be healthy")
    parser.add_argument("--wait-timeout", type=int, default=30, help="Timeout for waiting (default: 30s)")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Don't make changes, just show what would happen")
    parser.add_argument("--token", "-t", help="Machine token (or use MACHINE_SECRET_TOKEN env)")
    args = parser.parse_args()

    # Load seed file
    try:
        with open(args.file) as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading seed file: {e}")
        sys.exit(1)

    pins = data.get("pins", [])
    if not pins:
        print("No pins found in seed file")
        sys.exit(1)

    print(f"Loaded {len(pins)} pins from {args.file}")

    # Get token
    token = args.token or os.environ.get("MACHINE_SECRET_TOKEN")

    # Wait for API if requested
    if args.wait:
        if not wait_for_api(args.base, timeout=args.wait_timeout):
            sys.exit(1)

    # Upsert pins
    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Seeding pins to {args.base}...")
    upsert_success = 0
    upsert_failed = 0

    for pin in pins:
        ok, msg = upsert_pin(args.base, pin, token, args.dry_run)
        print(f"  {msg}")
        if ok:
            upsert_success += 1
        else:
            upsert_failed += 1

    print(f"\nUpsert: {upsert_success} succeeded, {upsert_failed} failed")

    # API verification
    if args.verify and not args.dry_run:
        print("\nVerifying pins via API...")
        verify_success = 0
        verify_failed = 0

        for pin in pins:
            ok, msg = verify_pin(args.base, pin, token)
            print(f"  {msg}")
            if ok:
                verify_success += 1
            else:
                verify_failed += 1

        print(f"\nAPI Verification: {verify_success} verified, {verify_failed} failed")

    # SQL verification
    if args.sql_verify and not args.dry_run:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            print("\nWarning: DATABASE_URL not set, skipping SQL verification")
        else:
            print("\nVerifying pins via SQL...")
            sql_success, sql_failed = verify_sql(database_url, pins)
            print(f"\nSQL Verification: {sql_success} verified, {sql_failed} failed")

    # Exit code
    if upsert_failed > 0:
        sys.exit(1)

    print("\n✓ Seeding complete!")
    sys.exit(0)


if __name__ == "__main__":
    main()
