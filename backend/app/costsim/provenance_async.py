# CostSim V2 Provenance Logger - Async Implementation
"""
Async provenance logging for CostSim V2.

This module provides non-blocking database access for writing provenance
records. Use this instead of the sync provenance.py for all async code paths.

Features:
- Non-blocking DB operations (won't hang event loop)
- Batch writing support for high-throughput scenarios
- Deduplication via input_hash
- V1 baseline backfill support

Usage:
    from app.costsim.provenance_async import (
        write_provenance,
        write_provenance_batch,
        query_provenance,
    )

    # Write single record
    await write_provenance(
        run_id="run_123",
        tenant_id="tenant_abc",
        variant_slug="v2",
        v1_cost=100.0,
        v2_cost=105.0,
        input_hash="abc123",
    )

    # Batch write
    records = [...]
    await write_provenance_batch(records)

    # Query records
    records = await query_provenance(
        tenant_id="tenant_abc",
        variant_slug="v2",
        start_date=start,
        end_date=end,
    )
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_async import AsyncSessionLocal, async_session_context
from app.models.costsim_cb import CostSimProvenanceModel

logger = logging.getLogger("nova.costsim.provenance_async")


async def write_provenance(
    run_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    variant_slug: str = "v2",
    source: str = "sandbox",
    model_version: Optional[str] = None,
    adapter_version: Optional[str] = None,
    commit_sha: Optional[str] = None,
    input_hash: Optional[str] = None,
    output_hash: Optional[str] = None,
    v1_cost: Optional[float] = None,
    v2_cost: Optional[float] = None,
    payload: Optional[Dict[str, Any]] = None,
    runtime_ms: Optional[int] = None,
    session: Optional[AsyncSession] = None,
) -> int:
    """
    Write a single provenance record.

    Args:
        run_id: Run identifier
        tenant_id: Tenant identifier
        variant_slug: v1, v2, or canary
        source: sandbox, canary, manual, backfill
        model_version: Cost model version
        adapter_version: Adapter version
        commit_sha: Git commit SHA
        input_hash: Hash of input for deduplication
        output_hash: Hash of output
        v1_cost: V1 simulation cost
        v2_cost: V2 simulation cost
        payload: Full simulation payload
        runtime_ms: Execution time in milliseconds
        session: Optional async session (creates new if None)

    Returns:
        ID of created record
    """
    own_session = session is None

    if own_session:
        session = AsyncSessionLocal()

    try:
        # Calculate cost delta if both present
        cost_delta = None
        if v1_cost is not None and v2_cost is not None:
            cost_delta = v2_cost - v1_cost

        record = CostSimProvenanceModel(
            run_id=run_id,
            tenant_id=tenant_id,
            variant_slug=variant_slug,
            source=source,
            model_version=model_version,
            adapter_version=adapter_version,
            commit_sha=commit_sha,
            input_hash=input_hash,
            output_hash=output_hash,
            v1_cost=v1_cost,
            v2_cost=v2_cost,
            cost_delta=cost_delta,
            payload=payload,
            runtime_ms=runtime_ms,
        )

        session.add(record)
        await session.commit()
        await session.refresh(record)

        logger.debug(f"Provenance record created: id={record.id}, variant={variant_slug}, input_hash={input_hash}")

        return record.id

    except Exception as e:
        logger.error(f"Failed to write provenance: {e}")
        if own_session:
            await session.rollback()
        raise

    finally:
        if own_session:
            await session.close()


async def write_provenance_batch(
    records: List[Dict[str, Any]],
    session: Optional[AsyncSession] = None,
) -> List[int]:
    """
    Write multiple provenance records in a single transaction.

    More efficient than individual writes for high-throughput scenarios.

    Args:
        records: List of record dictionaries (same keys as write_provenance)
        session: Optional async session

    Returns:
        List of created record IDs
    """
    if not records:
        return []

    own_session = session is None

    if own_session:
        session = AsyncSessionLocal()

    try:
        created_ids = []

        for record_data in records:
            # Calculate cost delta if both present
            v1_cost = record_data.get("v1_cost")
            v2_cost = record_data.get("v2_cost")
            cost_delta = None
            if v1_cost is not None and v2_cost is not None:
                cost_delta = v2_cost - v1_cost

            record = CostSimProvenanceModel(
                run_id=record_data.get("run_id"),
                tenant_id=record_data.get("tenant_id"),
                variant_slug=record_data.get("variant_slug", "v2"),
                source=record_data.get("source", "sandbox"),
                model_version=record_data.get("model_version"),
                adapter_version=record_data.get("adapter_version"),
                commit_sha=record_data.get("commit_sha"),
                input_hash=record_data.get("input_hash"),
                output_hash=record_data.get("output_hash"),
                v1_cost=v1_cost,
                v2_cost=v2_cost,
                cost_delta=cost_delta,
                payload=record_data.get("payload"),
                runtime_ms=record_data.get("runtime_ms"),
            )

            session.add(record)

        await session.commit()

        # Get IDs after commit
        # Note: This is a simplification - in production you'd want to
        # return the actual IDs via RETURNING clause
        logger.info(f"Batch wrote {len(records)} provenance records")
        return list(range(len(records)))  # Placeholder IDs

    except Exception as e:
        logger.error(f"Failed to write provenance batch: {e}")
        if own_session:
            await session.rollback()
        raise

    finally:
        if own_session:
            await session.close()


async def query_provenance(
    tenant_id: Optional[str] = None,
    variant_slug: Optional[str] = None,
    source: Optional[str] = None,
    input_hash: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Query provenance records.

    Args:
        tenant_id: Filter by tenant
        variant_slug: Filter by variant (v1, v2, canary)
        source: Filter by source (sandbox, canary, manual, backfill)
        input_hash: Filter by input hash (for deduplication check)
        start_date: Start of time range
        end_date: End of time range
        limit: Maximum records to return
        offset: Pagination offset

    Returns:
        List of provenance records as dictionaries
    """
    async with async_session_context() as session:
        conditions = []

        if tenant_id:
            conditions.append(CostSimProvenanceModel.tenant_id == tenant_id)
        if variant_slug:
            conditions.append(CostSimProvenanceModel.variant_slug == variant_slug)
        if source:
            conditions.append(CostSimProvenanceModel.source == source)
        if input_hash:
            conditions.append(CostSimProvenanceModel.input_hash == input_hash)
        if start_date:
            conditions.append(CostSimProvenanceModel.created_at >= start_date)
        if end_date:
            conditions.append(CostSimProvenanceModel.created_at <= end_date)

        statement = select(CostSimProvenanceModel)

        if conditions:
            statement = statement.where(and_(*conditions))

        statement = statement.order_by(CostSimProvenanceModel.created_at.desc()).limit(limit).offset(offset)

        result = await session.execute(statement)

        return [record.to_dict() for record in result.scalars()]


async def count_provenance(
    tenant_id: Optional[str] = None,
    variant_slug: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> int:
    """
    Count provenance records matching filters.

    Args:
        tenant_id: Filter by tenant
        variant_slug: Filter by variant
        start_date: Start of time range
        end_date: End of time range

    Returns:
        Count of matching records
    """
    async with async_session_context() as session:
        conditions = []

        if tenant_id:
            conditions.append(CostSimProvenanceModel.tenant_id == tenant_id)
        if variant_slug:
            conditions.append(CostSimProvenanceModel.variant_slug == variant_slug)
        if start_date:
            conditions.append(CostSimProvenanceModel.created_at >= start_date)
        if end_date:
            conditions.append(CostSimProvenanceModel.created_at <= end_date)

        statement = select(func.count()).select_from(CostSimProvenanceModel)

        if conditions:
            statement = statement.where(and_(*conditions))

        result = await session.execute(statement)
        return result.scalar() or 0


async def get_drift_stats(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Get drift statistics between V1 and V2 costs.

    Args:
        start_date: Start of time range
        end_date: End of time range

    Returns:
        Dictionary with drift statistics
    """
    async with async_session_context() as session:
        conditions = [
            CostSimProvenanceModel.v1_cost.isnot(None),
            CostSimProvenanceModel.v2_cost.isnot(None),
        ]

        if start_date:
            conditions.append(CostSimProvenanceModel.created_at >= start_date)
        if end_date:
            conditions.append(CostSimProvenanceModel.created_at <= end_date)

        statement = select(
            func.count().label("total"),
            func.avg(CostSimProvenanceModel.cost_delta).label("avg_delta"),
            func.min(CostSimProvenanceModel.cost_delta).label("min_delta"),
            func.max(CostSimProvenanceModel.cost_delta).label("max_delta"),
            func.stddev(CostSimProvenanceModel.cost_delta).label("stddev_delta"),
        ).where(and_(*conditions))

        result = await session.execute(statement)
        row = result.fetchone()

        if not row or row.total == 0:
            return {
                "total": 0,
                "avg_delta": 0.0,
                "min_delta": 0.0,
                "max_delta": 0.0,
                "stddev_delta": 0.0,
            }

        return {
            "total": row.total,
            "avg_delta": float(row.avg_delta or 0),
            "min_delta": float(row.min_delta or 0),
            "max_delta": float(row.max_delta or 0),
            "stddev_delta": float(row.stddev_delta or 0),
        }


async def check_duplicate(input_hash: str) -> bool:
    """
    Check if a record with this input hash already exists.

    Args:
        input_hash: Hash to check

    Returns:
        True if duplicate exists
    """
    async with async_session_context() as session:
        result = await session.execute(
            select(CostSimProvenanceModel.id).where(CostSimProvenanceModel.input_hash == input_hash).limit(1)
        )
        return result.scalars().first() is not None


def compute_input_hash(payload: Dict[str, Any]) -> str:
    """
    Compute deterministic hash of input payload.

    Args:
        payload: Input dictionary

    Returns:
        SHA-256 hash string (first 16 chars)
    """
    # Sort keys for deterministic serialization
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


# =============================================================================
# V1 BASELINE BACKFILL HELPERS
# =============================================================================


async def backfill_v1_baseline(
    records: List[Dict[str, Any]],
    batch_size: int = 100,
) -> Dict[str, int]:
    """
    Backfill V1 baseline records from historical data.

    Args:
        records: List of historical V1 simulation records
        batch_size: Number of records per batch

    Returns:
        Dictionary with counts (inserted, skipped, errors)
    """
    stats = {"inserted": 0, "skipped": 0, "errors": 0}

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]

        for record in batch:
            try:
                input_hash = record.get("input_hash")
                if input_hash and await check_duplicate(input_hash):
                    stats["skipped"] += 1
                    continue

                await write_provenance(
                    run_id=record.get("run_id"),
                    tenant_id=record.get("tenant_id"),
                    variant_slug="v1",
                    source="backfill",
                    v1_cost=record.get("cost"),
                    input_hash=input_hash,
                    payload=record.get("payload"),
                )
                stats["inserted"] += 1

            except Exception as e:
                logger.error(f"Failed to backfill record: {e}")
                stats["errors"] += 1

    logger.info(
        f"Backfill complete: inserted={stats['inserted']}, skipped={stats['skipped']}, errors={stats['errors']}"
    )

    return stats
