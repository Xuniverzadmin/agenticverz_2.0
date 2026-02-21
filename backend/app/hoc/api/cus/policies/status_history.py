# capability_id: CAP-009
# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Status History API endpoints (M6)
# Callers: Customer Console
# Allowed Imports: L4 (via registry)
# Forbidden Imports: L1, L5, L6, sqlalchemy, sqlmodel, app.db
# Reference: M6 Status History, L2 first-principles purity
"""
API endpoints for immutable status history audit trail.

Endpoints:
- GET /status_history - Query status history with filters
- GET /status_history/{entity_type}/{entity_id} - Get history for specific entity
- GET /status_history/export - Export to CSV/JSONL with signed URL
- GET /status_history/stats - Get statistics for audit reporting

Security:
- Tenant isolation via tenant_id filter
- Audit logging for all access
- Signed URLs for exports (time-limited)
"""

from __future__ import annotations

import csv
import hashlib
import hmac
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)
from app.schemas.response import wrap_dict

router = APIRouter(prefix="/status_history", tags=["status_history"])

# Configuration
EXPORT_DIR = Path(os.getenv("STATUS_HISTORY_EXPORT_DIR", "/var/lib/aos/exports"))
SIGNED_URL_SECRET = os.getenv("SIGNED_URL_SECRET", "aos-status-history-secret-key")
SIGNED_URL_TTL_SECONDS = int(os.getenv("SIGNED_URL_TTL_SECONDS", "3600"))  # 1 hour


# Request/Response models
class StatusHistoryQuery(BaseModel):
    """Query parameters for status history."""

    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    entity_id: Optional[str] = Field(None, description="Filter by entity ID")
    tenant_id: Optional[str] = Field(None, description="Filter by tenant")
    actor_type: Optional[str] = Field(None, description="Filter by actor type")
    start_time: Optional[datetime] = Field(None, description="Filter from this time")
    end_time: Optional[datetime] = Field(None, description="Filter until this time")
    limit: int = Field(100, ge=1, le=1000, description="Max results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class StatusHistoryResponse(BaseModel):
    """Single status history record."""

    id: str
    entity_type: str
    entity_id: str
    old_status: Optional[str]
    new_status: str
    actor_type: str
    actor_id: Optional[str]
    reason: Optional[str]
    tenant_id: Optional[str]
    correlation_id: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    sequence: Optional[int]


class StatusHistoryListResponse(BaseModel):
    """Paginated list of status history records."""

    items: List[StatusHistoryResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class ExportRequest(BaseModel):
    """Request for status history export."""

    format: str = Field("csv", description="Export format: csv or jsonl")
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    tenant_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ExportResponse(BaseModel):
    """Response with signed URL for export download."""

    export_id: str
    download_url: str
    expires_at: datetime
    format: str
    record_count: int


class StatsResponse(BaseModel):
    """Statistics for audit reporting."""

    total_records: int
    records_by_entity_type: Dict[str, int]
    records_by_actor_type: Dict[str, int]
    records_by_status: Dict[str, int]
    oldest_record: Optional[datetime]
    newest_record: Optional[datetime]
    time_range_days: Optional[float]


# Helper functions
def generate_signed_url(export_id: str, format: str) -> tuple[str, datetime]:
    """
    Generate a signed URL for export download.

    Args:
        export_id: Export file identifier
        format: Export format (csv/jsonl)

    Returns:
        Tuple of (signed_url, expires_at)
    """
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=SIGNED_URL_TTL_SECONDS)
    expires_ts = int(expires_at.timestamp())

    # Create signature
    message = f"{export_id}:{format}:{expires_ts}"
    signature = hmac.new(SIGNED_URL_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()[:32]

    # Build URL (relative - would be full URL in production)
    url = f"/status_history/download/{export_id}?format={format}&expires={expires_ts}&sig={signature}"

    return url, expires_at


def verify_signed_url(export_id: str, format: str, expires_ts: int, signature: str) -> bool:
    """
    Verify a signed URL signature.

    Args:
        export_id: Export file identifier
        format: Export format
        expires_ts: Expiration timestamp
        signature: Provided signature

    Returns:
        True if valid, False otherwise
    """
    # Check expiration
    if expires_ts < int(time.time()):
        return False

    # Verify signature
    message = f"{export_id}:{format}:{expires_ts}"
    expected_signature = hmac.new(SIGNED_URL_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()[:32]

    return hmac.compare_digest(signature, expected_signature)


# API Endpoints
@router.get("", response_model=StatusHistoryListResponse)
async def query_status_history(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    actor_type: Optional[str] = Query(None, description="Filter by actor type"),
    new_status: Optional[str] = Query(None, description="Filter by new status"),
    start_time: Optional[datetime] = Query(None, description="Filter from this time"),
    end_time: Optional[datetime] = Query(None, description="Filter until this time"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session=Depends(get_session_dep),
):
    """
    Query status history with filters.

    Supports filtering by:
    - entity_type: run, agent, approval, workflow, costsim
    - entity_id: Specific entity ID
    - tenant_id: Tenant scope (required in production)
    - actor_type: system, user, agent, scheduler
    - new_status: Target status
    - start_time/end_time: Time range
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "policies.guard_read",
        OperationContext(
            session=session,
            tenant_id=tenant_id or "global",
            params={
                "method": "query_status_history",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "tenant_id": tenant_id,
                "actor_type": actor_type,
                "new_status": new_status,
                "start_time": start_time,
                "end_time": end_time,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail=op.error)

    results, total = op.data

    return StatusHistoryListResponse(
        items=[
            StatusHistoryResponse(
                id=r.id,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                old_status=r.old_status,
                new_status=r.new_status,
                actor_type=r.actor_type,
                actor_id=r.actor_id,
                reason=r.reason,
                tenant_id=r.tenant_id,
                correlation_id=r.correlation_id,
                metadata=r.get_metadata(),
                created_at=r.created_at,
                sequence=r.sequence,
            )
            for r in results
        ],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(results)) < total,
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=StatusHistoryListResponse)
async def get_entity_history(
    entity_type: str,
    entity_id: str,
    limit: int = Query(100, ge=1, le=1000),
    session=Depends(get_session_dep),
):
    """
    Get complete status history for a specific entity.

    Returns all status transitions in chronological order.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "policies.guard_read",
        OperationContext(
            session=session,
            tenant_id="global",
            params={
                "method": "get_entity_status_history",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "limit": limit,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail=op.error)

    results = op.data

    return StatusHistoryListResponse(
        items=[
            StatusHistoryResponse(
                id=r.id,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                old_status=r.old_status,
                new_status=r.new_status,
                actor_type=r.actor_type,
                actor_id=r.actor_id,
                reason=r.reason,
                tenant_id=r.tenant_id,
                correlation_id=r.correlation_id,
                metadata=r.get_metadata(),
                created_at=r.created_at,
                sequence=r.sequence,
            )
            for r in results
        ],
        total=len(results),
        limit=limit,
        offset=0,
        has_more=False,
    )


@router.post("/export", response_model=ExportResponse)
async def create_export(
    request: ExportRequest,
    session=Depends(get_session_dep),
):
    """
    Create an export of status history records.

    Returns a signed URL for download that expires in 1 hour.

    Supported formats:
    - csv: Comma-separated values
    - jsonl: JSON Lines (one JSON object per line)
    """
    if request.format not in ("csv", "jsonl"):
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'jsonl'")

    registry = get_operation_registry()
    op = await registry.execute(
        "policies.guard_read",
        OperationContext(
            session=session,
            tenant_id=request.tenant_id or "global",
            params={
                "method": "get_all_status_history",
                "entity_type": request.entity_type,
                "entity_id": request.entity_id,
                "tenant_id": request.tenant_id,
                "start_time": request.start_time,
                "end_time": request.end_time,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail=op.error)

    results = op.data

    # Generate export ID
    export_id = str(uuid.uuid4())[:12]

    # Ensure export directory exists
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Write export file
    if request.format == "csv":
        file_path = EXPORT_DIR / f"{export_id}.csv"
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(results[0].__class__.csv_headers() if results else [])
            for record in results:
                writer.writerow(record.to_csv_row())
    else:  # jsonl
        file_path = EXPORT_DIR / f"{export_id}.jsonl"
        with open(file_path, "w") as f:
            for record in results:
                f.write(json.dumps(record.to_dict()) + "\n")

    # Generate signed URL
    download_url, expires_at = generate_signed_url(export_id, request.format)

    return ExportResponse(
        export_id=export_id,
        download_url=download_url,
        expires_at=expires_at,
        format=request.format,
        record_count=len(results),
    )


@router.get("/download/{export_id}")
async def download_export(
    export_id: str,
    format: str = Query(..., description="Export format"),
    expires: int = Query(..., description="Expiration timestamp"),
    sig: str = Query(..., description="Signature"),
):
    """
    Download an exported file using signed URL.

    This endpoint verifies the signature and expiration before
    returning the file contents.
    """
    # Verify signature
    if not verify_signed_url(export_id, format, expires, sig):
        raise HTTPException(status_code=403, detail="Invalid or expired signature")

    # Find file
    extension = "csv" if format == "csv" else "jsonl"
    file_path = EXPORT_DIR / f"{export_id}.{extension}"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export not found")

    # Read and return file
    with open(file_path, "r") as f:
        content = f.read()

    media_type = "text/csv" if format == "csv" else "application/x-ndjson"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=status_history_{export_id}.{extension}"},
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    session=Depends(get_session_dep),
):
    """
    Get statistics about status history records.

    Useful for audit reporting and monitoring.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "policies.guard_read",
        OperationContext(
            session=session,
            tenant_id=tenant_id or "global",
            params={
                "method": "get_status_history_stats",
                "tenant_id": tenant_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail=op.error)

    stats = op.data

    return StatsResponse(
        total_records=stats["total_records"],
        records_by_entity_type=stats["records_by_entity_type"],
        records_by_actor_type=stats["records_by_actor_type"],
        records_by_status=stats["records_by_status"],
        oldest_record=stats["oldest_record"],
        newest_record=stats["newest_record"],
        time_range_days=stats["time_range_days"],
    )
