# Checkpoint Offload to Cloudflare R2 (M11)
"""
Offloads old checkpoints from PostgreSQL to Cloudflare R2 for cost optimization.

Features:
- Gzip compression before upload (typically 5-10x reduction)
- Date-partitioned S3-compatible key structure
- Configurable retention policy
- Async batch processing
- SAFE OFFLOAD: upload → verify → delete sequence
- SHA256 integrity hash verification
- Exponential backoff retry with jitter

This module is designed to be run as a scheduled job (e.g., daily cron).

Environment Variables:
- DATABASE_URL: PostgreSQL connection string
- R2_ENDPOINT: Cloudflare R2 endpoint
- R2_BUCKET: R2 bucket name
- R2_ACCESS_KEY_ID: R2 access key
- R2_SECRET_ACCESS_KEY: R2 secret key
- CHECKPOINT_RETENTION_DAYS: Days to keep in DB (default: 7)
- CHECKPOINT_OFFLOAD_OLDER_THAN_DAYS: Offload checkpoints older than (default: 3)
- CHECKPOINT_OFFLOAD_MAX_RETRIES: Max retries per checkpoint (default: 3)
"""

import os
import io
import gzip
import json
import hashlib
import logging
import random
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger("nova.stores.checkpoint_offload")

# Configuration
RETENTION_DAYS = int(os.getenv("CHECKPOINT_RETENTION_DAYS", "7"))
OFFLOAD_OLDER_THAN_DAYS = int(os.getenv("CHECKPOINT_OFFLOAD_OLDER_THAN_DAYS", "3"))
BATCH_SIZE = int(os.getenv("CHECKPOINT_OFFLOAD_BATCH_SIZE", "100"))
MAX_RETRIES = int(os.getenv("CHECKPOINT_OFFLOAD_MAX_RETRIES", "3"))
BASE_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 30.0  # seconds


# =============================================================================
# Retry/Backoff Utilities
# =============================================================================

async def _retry_with_backoff(
    func,
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_RETRY_DELAY,
    max_delay: float = MAX_RETRY_DELAY,
    operation_name: str = "operation"
) -> Tuple[bool, Any, Optional[str]]:
    """
    Retry an async function with exponential backoff and jitter.

    Returns:
        (success: bool, result: Any, error_msg: Optional[str])
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            result = await func() if asyncio.iscoroutinefunction(func) else func()
            return (True, result, None)
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = min(base_delay * (2 ** attempt), max_delay)
                jitter = random.uniform(0, delay * 0.1)
                wait_time = delay + jitter
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {wait_time:.2f}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"{operation_name} failed after {max_retries} attempts: {e}")

    return (False, None, last_error)


def _compute_sha256(data: bytes) -> str:
    """Compute SHA256 hash of data."""
    return hashlib.sha256(data).hexdigest()


def _verify_upload_integrity(r2_client, bucket: str, key: str, expected_sha256: str) -> bool:
    """
    Verify uploaded object integrity by checking ETag or re-downloading.

    Returns True if integrity check passes.
    """
    try:
        # First try HEAD to check metadata
        head = r2_client.head_object(Bucket=bucket, Key=key)

        # Check if we stored the hash in metadata
        stored_hash = head.get("Metadata", {}).get("sha256", "")
        if stored_hash and stored_hash == expected_sha256:
            return True

        # Fallback: re-download and verify
        response = r2_client.get_object(Bucket=bucket, Key=key)
        downloaded_data = response["Body"].read()
        actual_sha256 = _compute_sha256(downloaded_data)

        if actual_sha256 == expected_sha256:
            return True

        logger.error(
            f"Integrity mismatch for {key}: expected {expected_sha256[:16]}..., "
            f"got {actual_sha256[:16]}..."
        )
        return False

    except Exception as e:
        logger.error(f"Integrity verification failed for {key}: {e}")
        return False


def _get_r2_client():
    """Get R2 client from stores factory."""
    from app.stores import get_r2_client
    return get_r2_client()


def _get_r2_bucket() -> str:
    """Get R2 bucket name."""
    from app.stores import get_r2_bucket
    return get_r2_bucket()


async def offload_old_checkpoints(
    older_than_days: Optional[int] = None,
    batch_size: Optional[int] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Offload old checkpoints from PostgreSQL to Cloudflare R2.

    Args:
        older_than_days: Offload checkpoints older than this many days
        batch_size: Number of checkpoints to process per batch
        dry_run: If True, don't actually delete from DB or upload to R2

    Returns:
        Dict with offload statistics:
        {
            "processed": int,
            "uploaded": int,
            "deleted": int,
            "errors": int,
            "dry_run": bool
        }
    """
    older_than_days = older_than_days or OFFLOAD_OLDER_THAN_DAYS
    batch_size = batch_size or BATCH_SIZE

    r2_client = _get_r2_client()
    r2_bucket = _get_r2_bucket()

    if not r2_client or not r2_bucket:
        logger.warning("R2 not configured, skipping checkpoint offload")
        return {"processed": 0, "uploaded": 0, "deleted": 0, "errors": 0, "skipped": True}

    # Get database connection
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set, cannot offload checkpoints")
        return {"processed": 0, "uploaded": 0, "deleted": 0, "errors": 1, "error": "DATABASE_URL not set"}

    stats = {
        "processed": 0,
        "uploaded": 0,
        "verified": 0,
        "deleted": 0,
        "errors": 0,
        "integrity_failures": 0,
        "retry_count": 0,
        "dry_run": dry_run,
        "cutoff_date": None,
    }

    try:
        import asyncpg

        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        stats["cutoff_date"] = cutoff.isoformat()

        # Parse connection string for asyncpg
        conn = await asyncpg.connect(database_url)

        try:
            # Fetch old checkpoints
            rows = await conn.fetch(
                """
                SELECT run_id, workflow_id, tenant_id, next_step_index,
                       last_result_hash, step_outputs_json, status, version,
                       created_at, updated_at, started_at, ended_at
                FROM workflow_checkpoints
                WHERE created_at < $1
                ORDER BY created_at ASC
                LIMIT $2
                """,
                cutoff,
                batch_size
            )

            logger.info(f"Found {len(rows)} checkpoints older than {cutoff}")

            for row in rows:
                stats["processed"] += 1
                run_id = row["run_id"]

                try:
                    # Build checkpoint data
                    checkpoint_data = {
                        "run_id": run_id,
                        "workflow_id": row["workflow_id"],
                        "tenant_id": row["tenant_id"],
                        "next_step_index": row["next_step_index"],
                        "last_result_hash": row["last_result_hash"],
                        "step_outputs": json.loads(row["step_outputs_json"]) if row["step_outputs_json"] else {},
                        "status": row["status"],
                        "version": row["version"],
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                        "started_at": row["started_at"].isoformat() if row["started_at"] else None,
                        "ended_at": row["ended_at"].isoformat() if row["ended_at"] else None,
                    }

                    # Compress
                    buf = io.BytesIO()
                    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
                        gz.write(json.dumps(checkpoint_data, sort_keys=True).encode("utf-8"))
                    compressed_data = buf.getvalue()

                    # Compute SHA256 hash for integrity verification
                    data_sha256 = _compute_sha256(compressed_data)

                    # Build R2 key with date partitioning
                    created_at = row["created_at"]
                    tenant_id = row["tenant_id"] or "default"
                    key = f"checkpoints/{tenant_id}/{created_at.strftime('%Y/%m/%d')}/{run_id}.json.gz"

                    if not dry_run:
                        # STEP 1: Upload to R2 with retry
                        # Use default args to capture values by value, not reference
                        def make_upload_fn(bucket=r2_bucket, k=key, data=compressed_data,
                                          rid=run_id, tid=tenant_id, st=row["status"], sha=data_sha256):
                            def upload_fn():
                                return r2_client.put_object(
                                    Bucket=bucket,
                                    Key=k,
                                    Body=data,
                                    ContentType="application/gzip",
                                    Metadata={
                                        "run_id": rid,
                                        "tenant_id": tid,
                                        "status": st,
                                        "sha256": sha,
                                    }
                                )
                            return upload_fn

                        upload_success, _, upload_error = await _retry_with_backoff(
                            make_upload_fn(),
                            operation_name=f"Upload {run_id}"
                        )

                        if not upload_success:
                            logger.error(f"Upload failed for {run_id}: {upload_error}")
                            stats["errors"] += 1
                            continue

                        stats["uploaded"] += 1

                        # STEP 2: Verify upload integrity
                        def make_verify_fn(client=r2_client, bucket=r2_bucket, k=key, sha=data_sha256):
                            def verify_fn():
                                return _verify_upload_integrity(client, bucket, k, sha)
                            return verify_fn

                        verify_success, verify_result, verify_error = await _retry_with_backoff(
                            make_verify_fn(),
                            max_retries=2,
                            operation_name=f"Verify {run_id}"
                        )

                        # verify_result is the boolean from _verify_upload_integrity
                        if not verify_success or not verify_result:
                            logger.error(f"Integrity verification failed for {run_id}, NOT deleting from DB")
                            stats["integrity_failures"] += 1
                            # Do NOT delete - data may be corrupted in R2
                            continue

                        stats["verified"] += 1

                        # STEP 3: Delete from DB only after verified upload
                        async def make_delete_fn(connection=conn, rid=run_id):
                            return await connection.execute(
                                "DELETE FROM workflow_checkpoints WHERE run_id = $1",
                                rid
                            )

                        delete_success, _, delete_error = await _retry_with_backoff(
                            lambda rid=run_id: conn.execute(
                                "DELETE FROM workflow_checkpoints WHERE run_id = $1",
                                rid
                            ),
                            operation_name=f"Delete {run_id}"
                        )

                        if not delete_success:
                            logger.error(f"DB delete failed for {run_id}: {delete_error}")
                            # Data is safe in R2, but we couldn't delete from DB
                            # This is acceptable - will be retried next run
                            stats["errors"] += 1
                            continue

                        stats["deleted"] += 1
                        logger.debug(f"Offloaded checkpoint {run_id} to {key} (sha256: {data_sha256[:16]}...)")

                    else:
                        logger.debug(f"[DRY RUN] Would offload checkpoint {run_id} to {key} (sha256: {data_sha256[:16]}...)")
                        stats["uploaded"] += 1
                        stats["verified"] += 1
                        stats["deleted"] += 1

                except Exception as e:
                    logger.error(f"Error offloading checkpoint {run_id}: {e}")
                    stats["errors"] += 1

        finally:
            await conn.close()

    except ImportError:
        logger.error("asyncpg not installed, cannot offload checkpoints")
        stats["errors"] += 1
        stats["error"] = "asyncpg not installed"
    except Exception as e:
        logger.error(f"Checkpoint offload failed: {e}")
        stats["errors"] += 1
        stats["error"] = str(e)

    logger.info(f"Checkpoint offload complete: {stats}")
    return stats


async def restore_checkpoint_from_r2(
    run_id: str,
    tenant_id: str = "default",
    created_date: Optional[datetime] = None
) -> Optional[Dict[str, Any]]:
    """
    Restore a checkpoint from R2 archive.

    Args:
        run_id: The run ID to restore
        tenant_id: Tenant ID (for key path)
        created_date: Original creation date (for key path)

    Returns:
        Checkpoint data dict, or None if not found
    """
    r2_client = _get_r2_client()
    r2_bucket = _get_r2_bucket()

    if not r2_client or not r2_bucket:
        logger.warning("R2 not configured, cannot restore checkpoint")
        return None

    # If we don't know the date, we need to scan (expensive)
    if created_date is None:
        logger.warning(f"No created_date provided for {run_id}, scanning R2 (slow)")
        # Try recent dates first
        for days_ago in range(30):
            date = datetime.now(timezone.utc) - timedelta(days=days_ago)
            key = f"checkpoints/{tenant_id}/{date.strftime('%Y/%m/%d')}/{run_id}.json.gz"
            try:
                response = r2_client.get_object(Bucket=r2_bucket, Key=key)
                compressed_data = response["Body"].read()
                with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as gz:
                    return json.loads(gz.read().decode("utf-8"))
            except r2_client.exceptions.NoSuchKey:
                continue
            except Exception as e:
                logger.error(f"Error restoring checkpoint from {key}: {e}")
                continue
        return None

    # Direct lookup
    key = f"checkpoints/{tenant_id}/{created_date.strftime('%Y/%m/%d')}/{run_id}.json.gz"
    try:
        response = r2_client.get_object(Bucket=r2_bucket, Key=key)
        compressed_data = response["Body"].read()
        with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as gz:
            return json.loads(gz.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"Error restoring checkpoint from {key}: {e}")
        return None


async def get_offload_stats() -> Dict[str, Any]:
    """
    Get statistics about checkpoint storage.

    Returns:
        Dict with storage statistics
    """
    stats = {
        "db_count": 0,
        "db_oldest": None,
        "r2_enabled": False,
        "r2_bucket": None,
    }

    # Check R2 configuration
    r2_client = _get_r2_client()
    r2_bucket = _get_r2_bucket()
    stats["r2_enabled"] = r2_client is not None
    stats["r2_bucket"] = r2_bucket

    # Get DB stats
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        try:
            import asyncpg
            conn = await asyncpg.connect(database_url)
            try:
                row = await conn.fetchrow(
                    """
                    SELECT COUNT(*) as count, MIN(created_at) as oldest
                    FROM workflow_checkpoints
                    """
                )
                stats["db_count"] = row["count"]
                stats["db_oldest"] = row["oldest"].isoformat() if row["oldest"] else None
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting DB stats: {e}")
            stats["db_error"] = str(e)

    return stats


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import asyncio
    import argparse

    parser = argparse.ArgumentParser(description="Checkpoint offload to R2")
    parser.add_argument("--older-than", type=int, default=OFFLOAD_OLDER_THAN_DAYS,
                        help="Offload checkpoints older than N days")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE,
                        help="Batch size for processing")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't actually delete or upload")
    parser.add_argument("--stats", action="store_true",
                        help="Just show storage stats")
    args = parser.parse_args()

    async def main():
        if args.stats:
            stats = await get_offload_stats()
            print(json.dumps(stats, indent=2, default=str))
        else:
            result = await offload_old_checkpoints(
                older_than_days=args.older_than,
                batch_size=args.batch_size,
                dry_run=args.dry_run
            )
            print(json.dumps(result, indent=2, default=str))

    asyncio.run(main())
