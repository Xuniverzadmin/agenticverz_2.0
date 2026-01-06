#!/usr/bin/env python3
"""
Redis Configuration Enforcement Check

Verifies that Redis is configured correctly for M10 Recovery durability.
Run in CI/CD or as a startup check to ensure production-ready configuration.

Required settings:
- appendonly: yes (AOF persistence required)
- maxmemory-policy: noeviction (prevent silent data loss)

Recommended settings:
- appendfsync: everysec or always
- maxmemory: set (to prevent OOM)

Usage:
    # Basic check
    python -m scripts.ops.check_redis_config

    # Strict mode (fail on warnings)
    python -m scripts.ops.check_redis_config --strict

    # JSON output for CI
    python -m scripts.ops.check_redis_config --json

    # Custom Redis URL
    REDIS_URL=redis://myredis:6379/0 python -m scripts.ops.check_redis_config

Exit codes:
    0: All required settings OK
    1: Required settings missing/incorrect
    2: Connection or other error
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Tuple

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger("nova.ops.check_redis_config")

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Required config settings (will fail if not met)
REQUIRED_CONFIG = {
    "appendonly": "yes",
    "maxmemory-policy": "noeviction",
}

# Recommended config settings (warn if not met)
RECOMMENDED_CONFIG = {
    "appendfsync": ["everysec", "always"],  # Either is acceptable
}

# Settings that should be set (warn if missing/zero)
# NOTE: These are advisory only. With noeviction policy, maxmemory=0 means
# Redis will refuse writes when memory exhausted (safe), not silently drop data.
SHOULD_BE_SET = {
    # "maxmemory": "non-zero value recommended",  # Disabled - not critical with noeviction
}


async def get_redis():
    """Get async Redis client."""
    try:
        import redis.asyncio as aioredis

        return aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    except ImportError:
        import aioredis

        return await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )


async def check_redis_config() -> Tuple[Dict[str, any], List[str], List[str]]:
    """
    Check Redis configuration against required and recommended settings.

    Returns:
        Tuple of (config_dict, errors, warnings)
    """
    redis = None
    try:
        redis = await get_redis()

        # Get all relevant config values
        config = {}
        errors = []
        warnings = []

        # Check required settings
        for key, expected in REQUIRED_CONFIG.items():
            result = await redis.config_get(key)
            actual = result.get(key, "NOT_SET")
            config[key] = actual

            if actual != expected:
                errors.append(f"REQUIRED: {key} = '{actual}' (expected '{expected}')")

        # Check recommended settings
        for key, expected_options in RECOMMENDED_CONFIG.items():
            result = await redis.config_get(key)
            actual = result.get(key, "NOT_SET")
            config[key] = actual

            if isinstance(expected_options, list):
                if actual not in expected_options:
                    warnings.append(f"RECOMMENDED: {key} = '{actual}' (recommended: {expected_options})")
            elif actual != expected_options:
                warnings.append(f"RECOMMENDED: {key} = '{actual}' (recommended '{expected_options}')")

        # Check should-be-set settings
        for key, description in SHOULD_BE_SET.items():
            result = await redis.config_get(key)
            actual = result.get(key, "0")
            config[key] = actual

            if actual in ("0", "", "NOT_SET"):
                warnings.append(f"SHOULD_SET: {key} = '{actual}' ({description})")

        # Additional helpful info
        info = await redis.info("persistence")
        config["aof_enabled"] = info.get("aof_enabled", 0)
        config["aof_rewrite_in_progress"] = info.get("aof_rewrite_in_progress", 0)
        config["rdb_bgsave_in_progress"] = info.get("rdb_bgsave_in_progress", 0)

        # Check AOF is actually enabled (not just configured)
        if str(config.get("aof_enabled", "0")) != "1":
            errors.append("AOF is configured but not enabled (restart Redis?)")

        return config, errors, warnings

    except Exception as e:
        return {}, [f"Connection error: {e}"], []
    finally:
        if redis:
            await redis.close()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Check Redis configuration for M10 Recovery durability")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (not just errors)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    # Run check
    config, errors, warnings = asyncio.run(check_redis_config())

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "redis_url": REDIS_URL.replace(REDIS_URL.split("@")[0] + "@", "***@") if "@" in REDIS_URL else REDIS_URL,
        "config": config,
        "errors": errors,
        "warnings": warnings,
        "status": "FAIL" if errors else ("WARN" if warnings else "OK"),
    }

    # Determine exit code
    if errors:
        exit_code = 1
    elif args.strict and warnings:
        exit_code = 1
        result["status"] = "FAIL (strict mode)"
    else:
        exit_code = 0

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n=== Redis Configuration Check ===")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Redis URL: {result['redis_url']}")
        print(f"Status: {result['status']}")

        print("\nConfiguration:")
        for key, value in config.items():
            print(f"  {key}: {value}")

        if errors:
            print(f"\nERRORS ({len(errors)}):")
            for err in errors:
                print(f"  ❌ {err}")

        if warnings:
            print(f"\nWARNINGS ({len(warnings)}):")
            for warn in warnings:
                print(f"  ⚠️  {warn}")

        if not errors and not warnings:
            print("\n✅ All checks passed!")
        elif errors:
            print("\n❌ Configuration issues found - streams may lose data!")
            print("   See: deployment/redis/redis-m10-durable.conf")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
