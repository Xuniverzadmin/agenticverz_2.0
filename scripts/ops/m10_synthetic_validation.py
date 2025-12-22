#!/usr/bin/env python3
"""
M10 Synthetic Data Validation for Neon + Upstash

Injects synthetic test data into production databases and validates
read/write health during the 48h monitoring window.

Usage:
    python -m scripts.ops.m10_synthetic_validation --inject   # Inject test data
    python -m scripts.ops.m10_synthetic_validation --validate # Validate data integrity
    python -m scripts.ops.m10_synthetic_validation --cleanup  # Remove test data
    python -m scripts.ops.m10_synthetic_validation --full     # Inject + Validate + Cleanup
    python -m scripts.ops.m10_synthetic_validation --daemon   # Run periodic validation

Environment:
    DATABASE_URL - Neon PostgreSQL connection string
    REDIS_URL - Upstash Redis connection string
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("m10.synthetic_validation")

# Test data prefix for easy identification and cleanup
TEST_PREFIX = "m10_synthetic_test_"


class NeonValidator:
    """Validates Neon PostgreSQL health with synthetic data."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None

    async def connect(self):
        """Establish database connection."""
        try:
            import asyncpg

            self.conn = await asyncpg.connect(self.database_url, ssl="require")
            logger.info("Connected to Neon PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neon: {e}")
            return False

    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()

    async def inject_test_data(self) -> dict:
        """Inject synthetic test records into M10 tables."""
        results = {"success": True, "records": {}, "errors": []}

        test_id = f"{TEST_PREFIX}{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc)

        try:
            # 1. Insert into failure_matches (using actual schema)
            failure_match_id = await self.conn.fetchval(
                """
                INSERT INTO failure_matches (
                    run_id, error_code, error_message, match_type,
                    confidence_score, category, severity, is_retryable,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """,
                f"{test_id}_run",
                "SYNTHETIC_VALIDATION",
                f"Synthetic validation test at {timestamp.isoformat()}",
                "synthetic",
                0.99,
                "test",
                "low",
                False,
                timestamp,
            )
            results["records"]["failure_matches"] = str(failure_match_id)
            logger.info(f"Injected failure_matches record: {failure_match_id}")

            # 2. Insert into recovery_candidates (using actual schema)
            recovery_id = await self.conn.fetchval(
                """
                INSERT INTO recovery_candidates (
                    failure_match_id, suggestion, confidence,
                    decision, source, error_code, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """,
                failure_match_id,
                "Synthetic validation - no action needed",
                0.95,
                "pending",
                "synthetic_validation",
                "SYNTHETIC_VALIDATION",
                timestamp,
            )
            results["records"]["recovery_candidates"] = str(recovery_id)
            logger.info(f"Injected recovery_candidates record: {recovery_id}")

            # 3. Insert into failure_pattern_exports (if exists)
            try:
                export_id = await self.conn.fetchval(
                    """
                    INSERT INTO failure_pattern_exports (
                        s3_key, status, size_bytes, created_at
                    ) VALUES ($1, $2, $3, $4)
                    RETURNING id
                """,
                    f"{test_id}_export.json",
                    "synthetic_test",
                    1024,
                    timestamp,
                )
                results["records"]["failure_pattern_exports"] = str(export_id)
                logger.info(f"Injected failure_pattern_exports record: {export_id}")
            except Exception as e:
                logger.warning(f"Could not insert into failure_pattern_exports: {e}")

            # Store test_id for validation/cleanup
            results["test_id"] = test_id
            results["timestamp"] = timestamp.isoformat()

        except Exception as e:
            results["success"] = False
            results["errors"].append(str(e))
            logger.error(f"Failed to inject test data: {e}")

        return results

    async def validate_test_data(self, test_id: str = None) -> dict:
        """Validate that test data can be read back correctly."""
        results = {"success": True, "checks": {}, "errors": []}

        try:
            # Check failure_matches table is readable
            count = await self.conn.fetchval(
                """
                SELECT COUNT(*) FROM failure_matches
                WHERE error_code = 'SYNTHETIC_VALIDATION'
            """
            )
            results["checks"]["failure_matches_readable"] = True
            results["checks"]["failure_matches_count"] = count
            logger.info(f"failure_matches: {count} synthetic records found")

            # Check recovery_candidates table is readable
            count = await self.conn.fetchval(
                """
                SELECT COUNT(*) FROM recovery_candidates
                WHERE source = 'synthetic_validation'
            """
            )
            results["checks"]["recovery_candidates_readable"] = True
            results["checks"]["recovery_candidates_count"] = count
            logger.info(f"recovery_candidates: {count} synthetic records found")

            # Check we can do a JOIN (validates referential integrity)
            join_count = await self.conn.fetchval(
                """
                SELECT COUNT(*) FROM recovery_candidates rc
                JOIN failure_matches fm ON rc.failure_match_id = fm.id
                WHERE fm.error_code = 'SYNTHETIC_VALIDATION'
            """
            )
            results["checks"]["join_works"] = True
            results["checks"]["join_count"] = join_count
            logger.info(f"JOIN test: {join_count} records")

            # Check write latency with a simple insert/delete
            start = time.time()
            test_val = f"{TEST_PREFIX}latency_{uuid.uuid4().hex[:8]}"
            row_id = await self.conn.fetchval(
                """
                INSERT INTO failure_matches (
                    run_id, error_code, match_type, confidence_score, created_at
                ) VALUES ($1, 'LATENCY_TEST', 'latency', 0.0, NOW())
                RETURNING id
            """,
                test_val,
            )
            await self.conn.execute("DELETE FROM failure_matches WHERE id = $1", row_id)
            latency_ms = (time.time() - start) * 1000
            results["checks"]["write_latency_ms"] = round(latency_ms, 2)
            logger.info(f"Write latency: {latency_ms:.2f}ms")

            if latency_ms > 5000:
                results["errors"].append(f"High write latency: {latency_ms:.2f}ms")

        except Exception as e:
            results["success"] = False
            results["errors"].append(str(e))
            logger.error(f"Validation failed: {e}")

        return results

    async def cleanup_test_data(self) -> dict:
        """Remove all synthetic test data."""
        results = {"success": True, "deleted": {}, "errors": []}

        try:
            # Delete from recovery_candidates first (foreign key constraint)
            deleted = await self.conn.execute(
                """
                DELETE FROM recovery_candidates
                WHERE source = 'synthetic_validation'
            """
            )
            results["deleted"]["recovery_candidates"] = deleted
            logger.info(f"Deleted recovery_candidates: {deleted}")

            # Delete from failure_matches
            deleted = await self.conn.execute(
                """
                DELETE FROM failure_matches
                WHERE error_code IN ('SYNTHETIC_VALIDATION', 'LATENCY_TEST')
            """
            )
            results["deleted"]["failure_matches"] = deleted
            logger.info(f"Deleted failure_matches: {deleted}")

            # Delete from failure_pattern_exports
            try:
                deleted = await self.conn.execute(
                    """
                    DELETE FROM failure_pattern_exports
                    WHERE status = 'synthetic_test'
                """
                )
                results["deleted"]["failure_pattern_exports"] = deleted
                logger.info(f"Deleted failure_pattern_exports: {deleted}")
            except Exception:
                pass  # Table might not exist

        except Exception as e:
            results["success"] = False
            results["errors"].append(str(e))
            logger.error(f"Cleanup failed: {e}")

        return results


class UpstashValidator:
    """Validates Upstash Redis health with synthetic data."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None

    async def connect(self):
        """Establish Redis connection."""
        try:
            import redis.asyncio as redis

            self.client = redis.from_url(self.redis_url)
            await self.client.ping()
            logger.info("Connected to Upstash Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Upstash: {e}")
            return False

    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()

    async def inject_test_data(self) -> dict:
        """Inject synthetic test data into Redis."""
        results = {"success": True, "records": {}, "errors": []}

        test_id = f"{TEST_PREFIX}{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            # 1. Set a simple key-value
            key = f"{TEST_PREFIX}kv:{test_id}"
            await self.client.set(
                key,
                json.dumps(
                    {
                        "test_id": test_id,
                        "timestamp": timestamp,
                        "type": "synthetic_validation",
                    }
                ),
                ex=3600,
            )  # 1 hour TTL
            results["records"]["key_value"] = key
            logger.info(f"Injected KV record: {key}")

            # 2. Add to a stream
            stream_key = f"{TEST_PREFIX}stream:validation"
            msg_id = await self.client.xadd(
                stream_key,
                {
                    "test_id": test_id,
                    "timestamp": timestamp,
                    "event": "synthetic_injection",
                },
            )
            results["records"]["stream"] = {
                "key": stream_key,
                "msg_id": msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
            }
            logger.info(f"Injected stream record: {stream_key} -> {msg_id}")

            # 3. Add to a hash
            hash_key = f"{TEST_PREFIX}hash:stats"
            await self.client.hset(
                hash_key,
                mapping={
                    "last_test_id": test_id,
                    "last_timestamp": timestamp,
                    "injection_count": await self.client.hincrby(
                        hash_key, "injection_count", 1
                    ),
                },
            )
            results["records"]["hash"] = hash_key
            logger.info(f"Injected hash record: {hash_key}")

            # 4. Add to a sorted set (for time-series tracking)
            zset_key = f"{TEST_PREFIX}zset:timeline"
            score = time.time()
            await self.client.zadd(zset_key, {test_id: score})
            results["records"]["sorted_set"] = {"key": zset_key, "score": score}
            logger.info(f"Injected sorted set record: {zset_key}")

            results["test_id"] = test_id
            results["timestamp"] = timestamp

        except Exception as e:
            results["success"] = False
            results["errors"].append(str(e))
            logger.error(f"Failed to inject Redis test data: {e}")

        return results

    async def validate_test_data(self) -> dict:
        """Validate Redis read operations and data integrity."""
        results = {"success": True, "checks": {}, "errors": []}

        try:
            # 1. Check KV read
            keys = await self.client.keys(f"{TEST_PREFIX}kv:*")
            results["checks"]["kv_count"] = len(keys)
            if keys:
                sample = await self.client.get(keys[0])
                results["checks"]["kv_readable"] = sample is not None
            logger.info(f"KV records: {len(keys)}")

            # 2. Check stream read
            stream_key = f"{TEST_PREFIX}stream:validation"
            stream_len = await self.client.xlen(stream_key)
            results["checks"]["stream_length"] = stream_len
            if stream_len > 0:
                msgs = await self.client.xrange(stream_key, count=1)
                results["checks"]["stream_readable"] = len(msgs) > 0
            logger.info(f"Stream length: {stream_len}")

            # 3. Check hash read
            hash_key = f"{TEST_PREFIX}hash:stats"
            hash_data = await self.client.hgetall(hash_key)
            results["checks"]["hash_fields"] = len(hash_data)
            results["checks"]["hash_readable"] = len(hash_data) > 0
            logger.info(f"Hash fields: {len(hash_data)}")

            # 4. Check sorted set
            zset_key = f"{TEST_PREFIX}zset:timeline"
            zset_count = await self.client.zcard(zset_key)
            results["checks"]["zset_count"] = zset_count
            logger.info(f"Sorted set count: {zset_count}")

            # 5. Check latency
            start = time.time()
            await self.client.ping()
            latency_ms = (time.time() - start) * 1000
            results["checks"]["ping_latency_ms"] = round(latency_ms, 2)
            logger.info(f"Ping latency: {latency_ms:.2f}ms")

            if latency_ms > 1000:
                results["errors"].append(f"High Redis latency: {latency_ms:.2f}ms")

        except Exception as e:
            results["success"] = False
            results["errors"].append(str(e))
            logger.error(f"Redis validation failed: {e}")

        return results

    async def cleanup_test_data(self) -> dict:
        """Remove all synthetic test data from Redis."""
        results = {"success": True, "deleted": {}, "errors": []}

        try:
            # Find and delete all test keys
            keys = await self.client.keys(f"{TEST_PREFIX}*")
            if keys:
                deleted = await self.client.delete(*keys)
                results["deleted"]["keys"] = deleted
                logger.info(f"Deleted {deleted} Redis keys")
            else:
                results["deleted"]["keys"] = 0
                logger.info("No test keys to delete")

        except Exception as e:
            results["success"] = False
            results["errors"].append(str(e))
            logger.error(f"Redis cleanup failed: {e}")

        return results


async def run_full_validation(neon_url: str, redis_url: str) -> dict:
    """Run complete inject -> validate -> cleanup cycle."""
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "neon": {},
        "redis": {},
        "overall_success": True,
    }

    # Neon validation
    neon = NeonValidator(neon_url)
    if await neon.connect():
        results["neon"]["inject"] = await neon.inject_test_data()
        results["neon"]["validate"] = await neon.validate_test_data()
        results["neon"]["cleanup"] = await neon.cleanup_test_data()
        await neon.close()

        if not all(
            [
                results["neon"]["inject"]["success"],
                results["neon"]["validate"]["success"],
                results["neon"]["cleanup"]["success"],
            ]
        ):
            results["overall_success"] = False
    else:
        results["neon"]["error"] = "Connection failed"
        results["overall_success"] = False

    # Redis validation
    redis_v = UpstashValidator(redis_url)
    if await redis_v.connect():
        results["redis"]["inject"] = await redis_v.inject_test_data()
        results["redis"]["validate"] = await redis_v.validate_test_data()
        results["redis"]["cleanup"] = await redis_v.cleanup_test_data()
        await redis_v.close()

        if not all(
            [
                results["redis"]["inject"]["success"],
                results["redis"]["validate"]["success"],
                results["redis"]["cleanup"]["success"],
            ]
        ):
            results["overall_success"] = False
    else:
        results["redis"]["error"] = "Connection failed"
        results["overall_success"] = False

    return results


async def run_daemon(neon_url: str, redis_url: str, interval: int = 300):
    """Run periodic validation in daemon mode."""
    logger.info(f"Starting synthetic validation daemon (interval={interval}s)")

    while True:
        try:
            results = await run_full_validation(neon_url, redis_url)

            status = "PASS" if results["overall_success"] else "FAIL"
            logger.info(f"Validation cycle complete: {status}")

            # Log summary
            if results["overall_success"]:
                neon_latency = (
                    results.get("neon", {})
                    .get("validate", {})
                    .get("checks", {})
                    .get("write_latency_ms", "N/A")
                )
                redis_latency = (
                    results.get("redis", {})
                    .get("validate", {})
                    .get("checks", {})
                    .get("ping_latency_ms", "N/A")
                )
                logger.info(
                    f"  Neon write latency: {neon_latency}ms, Redis ping: {redis_latency}ms"
                )
            else:
                errors = []
                for db in ["neon", "redis"]:
                    for phase in ["inject", "validate", "cleanup"]:
                        phase_errors = (
                            results.get(db, {}).get(phase, {}).get("errors", [])
                        )
                        errors.extend(phase_errors)
                if errors:
                    logger.error(f"  Errors: {errors}")

        except Exception as e:
            logger.error(f"Daemon cycle error: {e}")

        await asyncio.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="M10 Synthetic Data Validation")
    parser.add_argument("--inject", action="store_true", help="Inject test data")
    parser.add_argument("--validate", action="store_true", help="Validate test data")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup test data")
    parser.add_argument(
        "--full", action="store_true", help="Run full inject/validate/cleanup cycle"
    )
    parser.add_argument("--daemon", action="store_true", help="Run periodic validation")
    parser.add_argument(
        "--interval", type=int, default=300, help="Daemon interval in seconds"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    redis_url = os.getenv("REDIS_URL")

    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)
    if not redis_url:
        print("ERROR: REDIS_URL not set", file=sys.stderr)
        sys.exit(1)

    async def run():
        if args.daemon:
            await run_daemon(database_url, redis_url, args.interval)
        elif args.full:
            results = await run_full_validation(database_url, redis_url)
            if args.json:
                print(json.dumps(results, indent=2, default=str))
            else:
                status = "PASS" if results["overall_success"] else "FAIL"
                print(f"\n=== Synthetic Validation: {status} ===")
                print(f"Timestamp: {results['timestamp']}")

                for db in ["neon", "redis"]:
                    print(f"\n{db.upper()}:")
                    db_results = results.get(db, {})
                    if "error" in db_results:
                        print(f"  ERROR: {db_results['error']}")
                    else:
                        for phase in ["inject", "validate", "cleanup"]:
                            phase_data = db_results.get(phase, {})
                            phase_status = "OK" if phase_data.get("success") else "FAIL"
                            print(f"  {phase}: {phase_status}")
                            if phase_data.get("errors"):
                                for err in phase_data["errors"]:
                                    print(f"    - {err}")

            sys.exit(0 if results["overall_success"] else 1)
        else:
            # Individual operations
            neon = NeonValidator(database_url)
            redis_v = UpstashValidator(redis_url)

            results = {}

            if args.inject or args.validate or args.cleanup:
                if await neon.connect() and await redis_v.connect():
                    if args.inject:
                        results["neon_inject"] = await neon.inject_test_data()
                        results["redis_inject"] = await redis_v.inject_test_data()
                    if args.validate:
                        results["neon_validate"] = await neon.validate_test_data()
                        results["redis_validate"] = await redis_v.validate_test_data()
                    if args.cleanup:
                        results["neon_cleanup"] = await neon.cleanup_test_data()
                        results["redis_cleanup"] = await redis_v.cleanup_test_data()
                    await neon.close()
                    await redis_v.close()

            if args.json:
                print(json.dumps(results, indent=2, default=str))
            else:
                for key, val in results.items():
                    status = "OK" if val.get("success") else "FAIL"
                    print(f"{key}: {status}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
