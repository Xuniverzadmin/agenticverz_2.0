# capability_id: CAP-009
# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: scheduler
#   Execution: async
# Role: Storage maintenance jobs
# Callers: scheduler
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Reference: Storage System

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
# Uploads files to Cloudflare R2 with exponential backoff
# External cloud storage calls are non-deterministic
FEATURE_INTENT = FeatureIntent.EXTERNAL_SIDE_EFFECT
RETRY_POLICY = RetryPolicy.NEVER

"""
R2 Object Storage Helper for Failure Pattern Aggregation

Provides robust upload to Cloudflare R2 with:
- Exponential backoff retries (tenacity)
- Local file fallback on failure
- SHA256 verification
- Prometheus metrics integration
- Audit trail support
- Vault integration for secrets

Usage:
    from app.jobs.storage import write_candidate_json_and_upload

    result = write_candidate_json_and_upload(payload)
    if result["status"] == "uploaded":
        print(f"Uploaded to {result['key']}")
    else:
        print(f"Fallback to local: {result['path']}")
"""

import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.utils.metrics_helpers import get_or_create_counter, get_or_create_histogram

logger = logging.getLogger("nova.jobs.storage")

# =============================================================================
# Vault Integration - Load R2 Secrets
# =============================================================================


def _load_r2_secrets_from_vault() -> Dict[str, str]:
    """
    Load R2 credentials from HashiCorp Vault.

    Returns dict with R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, etc.
    Falls back to environment variables if Vault unavailable.
    """
    try:
        from app.secrets.vault_client import VaultClient

        vault_addr = os.getenv("VAULT_ADDR")
        vault_token = os.getenv("VAULT_TOKEN")

        if not vault_addr or not vault_token:
            logger.debug("Vault not configured, using environment variables for R2")
            return {}

        client = VaultClient(addr=vault_addr, token=vault_token)

        if not client.is_available():
            logger.warning("Vault not available, using environment variables for R2")
            client.close()
            return {}

        try:
            secrets = client.get_secret("r2-storage")
            logger.info(f"Loaded {len(secrets)} R2 secrets from Vault")
            client.close()
            return secrets
        except ValueError as e:
            logger.warning(f"Failed to load R2 secrets from Vault: {e}")
            client.close()
            return {}

    except ImportError:
        logger.debug("Vault client not available, using environment variables for R2")
        return {}
    except Exception as e:
        logger.warning(f"Error loading R2 secrets from Vault: {e}")
        return {}


# Load secrets from Vault (falls back to env vars)
_vault_secrets = _load_r2_secrets_from_vault()

# =============================================================================
# Environment Configuration (with Vault fallback)
# =============================================================================

R2_ACCOUNT_ID = _vault_secrets.get("R2_ACCOUNT_ID") or os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = _vault_secrets.get("R2_ACCESS_KEY_ID") or os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = _vault_secrets.get("R2_SECRET_ACCESS_KEY") or os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = _vault_secrets.get("R2_BUCKET") or os.getenv("R2_BUCKET", "candidate-failure-patterns")
R2_ENDPOINT = _vault_secrets.get("R2_ENDPOINT") or os.getenv("R2_ENDPOINT")
UPLOAD_PREFIX = os.getenv("R2_UPLOAD_PREFIX", "failure_patterns")
LOCAL_FALLBACK_DIR = os.getenv("AGG_LOCAL_FALLBACK", "/opt/agenticverz/state/fallback-uploads")
MAX_RETRIES = int(os.getenv("R2_MAX_RETRIES", "5"))

# Ensure fallback directory exists
os.makedirs(LOCAL_FALLBACK_DIR, exist_ok=True)

# =============================================================================
# Prometheus Metrics
# =============================================================================

# Using idempotent registration (PIN-120 PREV-1)
R2_UPLOAD_ATTEMPTS = get_or_create_counter(
    "failure_agg_r2_upload_attempt_total",
    "Total R2 upload attempts",
    ["status"],  # uploaded, fallback_local, error
)

R2_UPLOAD_DURATION = get_or_create_histogram(
    "failure_agg_r2_upload_duration_seconds",
    "R2 upload duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

R2_UPLOAD_FALLBACK = get_or_create_counter(
    "failure_agg_r2_upload_fallback_total", "Total uploads that fell back to local storage"
)

R2_RETRY_SUCCESS = get_or_create_counter("failure_agg_r2_retry_success_total", "Uploads that succeeded after retry")

R2_UPLOAD_BYTES = get_or_create_counter("failure_agg_r2_upload_bytes_total", "Total bytes uploaded to R2")

# =============================================================================
# S3 Client Factory
# =============================================================================


def make_s3_client():
    """Create S3-compatible client for Cloudflare R2."""
    if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        raise ValueError("R2 configuration incomplete. Required: R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")

    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",  # Required for Cloudflare R2
        config=Config(
            signature_version="s3v4",
            retries={"max_attempts": 0},  # We handle retries ourselves
        ),
    )


def is_r2_configured() -> bool:
    """Check if R2 storage is properly configured."""
    return all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET])


# =============================================================================
# Utility Functions
# =============================================================================


def sha256_bytes(data: bytes) -> str:
    """Compute SHA256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()


def generate_object_key(prefix: Optional[str] = None) -> str:
    """
    Generate object key with date-partitioned path.

    Format: {prefix}/YYYY/MM/DD/candidates_{timestamp}_{sha12}.json
    """
    ts = time.gmtime()
    date_path = time.strftime("%Y/%m/%d", ts)
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", ts)

    # SHA will be appended after payload is known
    key_prefix = prefix or UPLOAD_PREFIX
    return f"{key_prefix}/{date_path}/candidates_{timestamp}"


# =============================================================================
# Core Upload Functions
# =============================================================================


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=0.5, min=1, max=10),
    retry=retry_if_exception_type(ClientError),
    reraise=True,
)
def upload_to_r2_bytes(key: str, payload_bytes: bytes, content_type: str = "application/json") -> Dict[str, Any]:
    """
    Upload bytes to R2 with retry logic.

    Args:
        key: Object key (path in bucket)
        payload_bytes: Raw bytes to upload
        content_type: MIME type

    Returns:
        Dict with key, size, sha256

    Raises:
        ClientError: On persistent upload failure
    """
    client = make_s3_client()
    checksum = sha256_bytes(payload_bytes)

    # Upload with metadata
    client.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=payload_bytes,
        ContentType=content_type,
        Metadata={
            "sha256": checksum,
            "uploaded_by": "failure_aggregation_job",
            "upload_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
    )

    # Verify upload with HEAD request
    meta = client.head_object(Bucket=R2_BUCKET, Key=key)

    return {
        "key": key,
        "size": meta["ContentLength"],
        "sha256": checksum,
        "etag": meta.get("ETag", "").strip('"'),
    }


def write_local_fallback(payload_bytes: bytes, filename: str) -> str:
    """
    Write payload to local fallback storage.

    Args:
        payload_bytes: Raw bytes to write
        filename: Target filename

    Returns:
        Full path to written file
    """
    local_path = os.path.join(LOCAL_FALLBACK_DIR, filename)

    with open(local_path, "wb") as f:
        f.write(payload_bytes)

    logger.warning(f"Wrote fallback to local storage: {local_path}")
    return local_path


# =============================================================================
# Main Entry Point
# =============================================================================


def write_candidate_json_and_upload(
    payload: Dict[str, Any],
    prefix: Optional[str] = None,
    record_to_db: bool = True,
) -> Dict[str, Any]:
    """
    Write candidate failure patterns JSON to R2 with local fallback.

    This is the main entry point for the failure aggregation job.

    Args:
        payload: Dictionary to serialize as JSON
        prefix: Optional prefix override (default: R2_UPLOAD_PREFIX)
        record_to_db: If True, record export to failure_pattern_exports table

    Returns:
        Dict with:
        - status: "uploaded" | "fallback_local" | "disabled"
        - key/path: R2 key or local path
        - size: bytes uploaded
        - sha256: content hash
        - error: error message (if fallback)
    """
    start_time = time.time()

    # Check if R2 is configured
    if not is_r2_configured():
        logger.info("R2 not configured, using local storage only")
        return {
            "status": "disabled",
            "message": "R2 storage not configured",
        }

    # Serialize payload
    payload_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    sha = sha256_bytes(payload_bytes)[:12]

    # Generate key with SHA suffix
    base_key = generate_object_key(prefix)
    key = f"{base_key}_{sha}.json"
    filename = f"candidates_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}_{sha}.json"

    try:
        # Attempt R2 upload
        result = upload_to_r2_bytes(key, payload_bytes)

        duration = time.time() - start_time
        R2_UPLOAD_DURATION.observe(duration)
        R2_UPLOAD_ATTEMPTS.labels(status="uploaded").inc()
        R2_UPLOAD_BYTES.inc(result["size"])

        # Record to database if requested
        if record_to_db:
            try:
                _record_export_to_db(
                    s3_key=result["key"],
                    size_bytes=result["size"],
                    sha256=result["sha256"],
                    status="uploaded",
                )
            except Exception as db_err:
                logger.warning(f"Failed to record export to DB: {db_err}")

        logger.info(f"Uploaded to R2: {result['key']} ({result['size']} bytes)")

        return {
            "status": "uploaded",
            "key": result["key"],
            "size": result["size"],
            "sha256": result["sha256"],
            "etag": result.get("etag"),
            "duration_seconds": duration,
        }

    except Exception as e:
        # Upload failed - fall back to local storage
        duration = time.time() - start_time
        R2_UPLOAD_DURATION.observe(duration)
        R2_UPLOAD_ATTEMPTS.labels(status="fallback_local").inc()
        R2_UPLOAD_FALLBACK.inc()

        logger.error(f"R2 upload failed after {MAX_RETRIES} attempts: {e}")

        # Write to local fallback
        local_path = write_local_fallback(payload_bytes, filename)

        # Record to database as fallback
        if record_to_db:
            try:
                _record_export_to_db(
                    s3_key=local_path,
                    size_bytes=len(payload_bytes),
                    sha256=sha256_bytes(payload_bytes),
                    status="fallback_local",
                    notes=str(e),
                )
            except Exception as db_err:
                logger.warning(f"Failed to record fallback to DB: {db_err}")

        return {
            "status": "fallback_local",
            "path": local_path,
            "size": len(payload_bytes),
            "sha256": sha256_bytes(payload_bytes),
            "error": str(e),
            "duration_seconds": duration,
        }


def retry_local_fallback(file_path: str, prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Retry uploading a local fallback file to R2.

    Called by the retry worker to process files in LOCAL_FALLBACK_DIR.

    Args:
        file_path: Path to local JSON file
        prefix: Optional prefix override

    Returns:
        Upload result dict
    """
    if not os.path.exists(file_path):
        return {"status": "error", "error": f"File not found: {file_path}"}

    try:
        with open(file_path, "rb") as f:
            payload_bytes = f.read()

        # Parse to validate JSON
        json.loads(payload_bytes.decode("utf-8"))

        sha = sha256_bytes(payload_bytes)[:12]
        base_key = generate_object_key(prefix)
        key = f"{base_key}_{sha}.json"

        result = upload_to_r2_bytes(key, payload_bytes)

        R2_RETRY_SUCCESS.inc()
        R2_UPLOAD_BYTES.inc(result["size"])

        # Mark local file as uploaded
        uploaded_path = file_path + ".uploaded"
        os.rename(file_path, uploaded_path)

        # Update DB record
        try:
            _update_export_status(file_path, "uploaded", result["key"])
        except Exception as db_err:
            logger.warning(f"Failed to update export status: {db_err}")

        logger.info(f"Retry successful: {file_path} -> {result['key']}")

        return {
            "status": "uploaded",
            "key": result["key"],
            "size": result["size"],
            "sha256": result["sha256"],
            "original_path": file_path,
        }

    except Exception as e:
        logger.error(f"Retry failed for {file_path}: {e}")
        return {
            "status": "error",
            "path": file_path,
            "error": str(e),
        }


# =============================================================================
# Database Recording
# =============================================================================


def _record_export_to_db(
    s3_key: str,
    size_bytes: int,
    sha256: str,
    status: str,
    notes: Optional[str] = None,
) -> None:
    """Record export to failure_pattern_exports table."""
    try:
        from sqlmodel import Session, text

        from app.db import engine

        query = text(
            """
            INSERT INTO failure_pattern_exports
            (s3_key, size_bytes, sha256, status, uploader, notes)
            VALUES (:s3_key, :size_bytes, :sha256, :status, :uploader, :notes)
        """
        )

        with Session(engine) as session:
            session.execute(
                query,
                {
                    "s3_key": s3_key,
                    "size_bytes": size_bytes,
                    "sha256": sha256,
                    "status": status,
                    "uploader": "failure_aggregation_job",
                    "notes": notes,
                },
            )
            session.commit()

    except Exception as e:
        logger.warning(f"Failed to record export to DB: {e}")
        raise


def _update_export_status(
    original_key: str,
    new_status: str,
    new_s3_key: Optional[str] = None,
) -> None:
    """Update export status after retry."""
    try:
        from sqlmodel import Session, text

        from app.db import engine

        if new_s3_key:
            query = text(
                """
                UPDATE failure_pattern_exports
                SET status = :status, s3_key = :new_key, uploaded_at = now()
                WHERE s3_key = :original_key
            """
            )
            params = {"status": new_status, "new_key": new_s3_key, "original_key": original_key}
        else:
            query = text(
                """
                UPDATE failure_pattern_exports
                SET status = :status
                WHERE s3_key = :original_key
            """
            )
            params = {"status": new_status, "original_key": original_key}

        with Session(engine) as session:
            session.execute(query, params)
            session.commit()

    except Exception as e:
        logger.warning(f"Failed to update export status: {e}")
        raise


# =============================================================================
# Verification Utilities
# =============================================================================


def verify_r2_object(key: str) -> Dict[str, Any]:
    """
    Verify an object exists in R2 and return metadata.

    Args:
        key: Object key to verify

    Returns:
        Dict with metadata or error
    """
    try:
        client = make_s3_client()
        response = client.head_object(Bucket=R2_BUCKET, Key=key)

        return {
            "exists": True,
            "key": key,
            "size": response["ContentLength"],
            "last_modified": response["LastModified"].isoformat(),
            "etag": response.get("ETag", "").strip('"'),
            "metadata": response.get("Metadata", {}),
        }

    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return {"exists": False, "key": key}
        raise


def list_r2_objects(
    prefix: Optional[str] = None,
    max_keys: int = 100,
) -> Dict[str, Any]:
    """
    List objects in R2 bucket.

    Args:
        prefix: Optional prefix filter
        max_keys: Maximum objects to return

    Returns:
        Dict with objects list
    """
    try:
        client = make_s3_client()

        params = {
            "Bucket": R2_BUCKET,
            "MaxKeys": max_keys,
        }
        if prefix:
            params["Prefix"] = prefix

        response = client.list_objects_v2(**params)

        objects = []
        for obj in response.get("Contents", []):
            objects.append(
                {
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                }
            )

        return {
            "bucket": R2_BUCKET,
            "prefix": prefix,
            "count": len(objects),
            "objects": objects,
            "is_truncated": response.get("IsTruncated", False),
        }

    except Exception as e:
        return {"error": str(e)}
