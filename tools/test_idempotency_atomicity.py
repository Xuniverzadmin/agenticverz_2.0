#!/usr/bin/env python3
"""
tools/test_idempotency_atomicity.py

Concurrent idempotency atomicity test for Redis.
Verifies that exactly one concurrent request wins when claiming the same idempotency key.
"""
import asyncio
import os
import json
import uuid
import time
from argparse import ArgumentParser

try:
    import redis.asyncio as aioredis
except ImportError:
    import aioredis

LUA_SCRIPT = """
local existing = redis.call('GET', KEYS[1])
if existing then
  return existing
else
  redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[2])
  return nil
end
"""


async def attempt_claim(pool, script_sha, key, value, ttl):
    """Attempt to claim the idempotency key using the Lua script."""
    try:
        res = await pool.evalsha(script_sha, 1, key, json.dumps(value), str(ttl))
        return res
    except Exception:
        # Fallback to EVAL if EVALSHA fails
        res = await pool.eval(LUA_SCRIPT, 1, key, json.dumps(value), str(ttl))
        return res


async def worker(idx, pool, script_sha, key, ttl, results):
    """Worker coroutine that attempts to claim the key."""
    val = {"owner": f"worker-{idx}", "ts": int(time.time()), "id": str(uuid.uuid4())}
    res = await attempt_claim(pool, script_sha, key, val, ttl)
    results[idx] = {"attempted": val, "got_existing": res}
    status = "WINNER" if res is None else "FOUND_EXISTING"
    print(f"  worker-{idx:02d}: {status}")


async def main():
    parser = ArgumentParser(description="Test Redis idempotency atomicity")
    parser.add_argument(
        "--redis-url",
        default=os.environ.get("REDIS_URL"),
        help="Redis connection URL (default: $REDIS_URL)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=20,
        help="Number of concurrent workers (default: 20)",
    )
    parser.add_argument(
        "--key",
        default="idemp:atomic:test",
        help="Redis key to test (default: idemp:atomic:test)",
    )
    parser.add_argument(
        "--ttl",
        type=int,
        default=3600,
        help="TTL in seconds for the key (default: 3600)",
    )
    args = parser.parse_args()

    if not args.redis_url:
        print("ERROR: Missing REDIS_URL env or --redis-url argument")
        return 1

    print("Connecting to Redis...")
    print(f"  URL: {args.redis_url[:30]}...")

    pool = await aioredis.from_url(args.redis_url, decode_responses=True)

    # Test connection
    try:
        pong = await pool.ping()
        print(f"  Connection: OK (ping={pong})")
    except Exception as e:
        print(f"  Connection: FAILED ({e})")
        return 1

    # Load the Lua script
    script_sha = await pool.script_load(LUA_SCRIPT)
    print(f"  Script SHA: {script_sha[:16]}...")

    key = args.key
    concurrency = args.concurrency
    ttl = args.ttl

    # Clean up any existing key
    await pool.delete(key)
    print("\nRunning atomicity test:")
    print(f"  Key: {key}")
    print(f"  Concurrency: {concurrency} workers")
    print(f"  TTL: {ttl}s")
    print()

    results = [None] * concurrency

    # Launch all workers concurrently
    tasks = [worker(i, pool, script_sha, key, ttl, results) for i in range(concurrency)]
    await asyncio.gather(*tasks)

    # Analyze results
    winners = [r for r in results if r and r["got_existing"] is None]
    found_existing = [r for r in results if r and r["got_existing"] is not None]

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total attempts:    {len(results)}")
    print(f"Winners (set):     {len(winners)}")
    print(f"Found existing:    {len(found_existing)}")

    # Get stored value
    stored = await pool.get(key)

    if len(winners) == 1:
        print("\nRESULT: SUCCESS - Exactly one winner")
        print("\nWinner details:")
        winner_val = winners[0]["attempted"]
        print(f"  Owner: {winner_val['owner']}")
        print(f"  ID: {winner_val['id']}")
        print(f"\nStored value matches winner: {stored == json.dumps(winner_val)}")
        exit_code = 0
    elif len(winners) == 0:
        print("\nRESULT: ANOMALY - No winners (key may have pre-existed)")
        exit_code = 1
    else:
        print(f"\nRESULT: FAILURE - Multiple winners detected ({len(winners)})")
        print("This indicates a race condition in the idempotency logic!")
        for i, w in enumerate(winners):
            print(f"  Winner {i+1}: {w['attempted']['owner']}")
        exit_code = 1

    # Cleanup
    await pool.delete(key)
    await pool.aclose()

    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
