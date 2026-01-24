# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: async
# Role: Workflow checkpoint persistence and recovery
# Authority: Checkpoint state mutation (optimistic locking via version)
# Callers: workflow engine
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Contract: EXECUTION_SEMANTIC_CONTRACT.md (Guarantee 4: Exactly-Once Step Execution)

# Checkpoint Store (M4 + Hardening)
"""
DB-backed checkpoint store for workflow resume-on-restart.

Provides:
1. Atomic checkpoint save/load with optimistic locking
2. Step output persistence for dependency resolution
3. Status tracking (running, completed, aborted, failed)
4. Content hashing for replay verification
5. Version-based concurrency control

Design:
- Checkpoints are keyed by run_id (primary key)
- Step outputs stored as JSON for resuming with dependencies
- Uses SQLModel for type safety and migrations
- Optimistic locking via version column prevents lost updates
- Async SQLAlchemy + asyncpg for non-blocking DB operations
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import DateTime
from sqlalchemy import create_engine as create_sync_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, SQLModel, select, text

logger = logging.getLogger("nova.workflow.checkpoint")


class CheckpointVersionConflictError(Exception):
    """Raised when concurrent update detected via version mismatch."""

    def __init__(self, run_id: str, expected_version: int, actual_version: int):
        super().__init__(f"Version conflict for run_id={run_id}: expected={expected_version}, actual={actual_version}")
        self.run_id = run_id
        self.expected_version = expected_version
        self.actual_version = actual_version


class WorkflowCheckpoint(SQLModel, table=True):
    """
    DB model for workflow checkpoints.

    Table: workflow_checkpoints
    Primary key: run_id
    Concurrency: version column for optimistic locking
    """

    __tablename__ = "workflow_checkpoints"

    run_id: str = Field(primary_key=True, index=True, max_length=255)
    workflow_id: str = Field(default="", max_length=255)
    tenant_id: str = Field(default="", max_length=255, index=True)  # For multi-tenant isolation
    next_step_index: int = Field(default=0)
    last_result_hash: Optional[str] = Field(default=None, max_length=64)
    step_outputs_json: Optional[str] = Field(default=None)  # JSON of step outputs
    status: str = Field(default="running", max_length=32)  # running, completed, aborted, failed
    version: int = Field(default=1)  # Optimistic locking version
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )
    started_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )  # Step start time for debugging
    ended_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )  # Step end time for debugging

    @property
    def step_outputs(self) -> Dict[str, Any]:
        """Parse step outputs from JSON."""
        if self.step_outputs_json:
            try:
                return json.loads(self.step_outputs_json)
            except json.JSONDecodeError:
                return {}
        return {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "tenant_id": self.tenant_id,
            "next_step_index": self.next_step_index,
            "last_result_hash": self.last_result_hash,
            "step_outputs": self.step_outputs,
            "status": self.status,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }


@dataclass
class CheckpointData:
    """
    Immutable checkpoint data returned by load().

    Separates DB model from business logic.
    """

    run_id: str
    workflow_id: str
    tenant_id: str
    next_step_index: int
    last_result_hash: Optional[str]
    step_outputs: Dict[str, Any]
    status: str
    version: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


def _convert_to_async_url(url: str) -> str:
    """Convert a PostgreSQL URL to async format for asyncpg."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


class CheckpointStore:
    """
    Async checkpoint store for workflow persistence with optimistic locking.

    Concurrency Safety:
    - Uses version column for optimistic locking
    - Concurrent updates to same run_id will detect conflicts
    - Callers should reload and retry on CheckpointVersionConflictError
    - All operations are truly async using asyncpg

    Usage:
        store = CheckpointStore(engine_url)
        await store.save(run_id, next_step_index=2, ...)
        ck = await store.load(run_id)
        if ck:
            resume_from = ck.next_step_index
    """

    def __init__(self, engine_url: Optional[str] = None):
        """
        Initialize checkpoint store with async engine.

        Args:
            engine_url: Database connection URL. If None, uses DATABASE_URL env var.
        """
        url = engine_url or os.getenv("DATABASE_URL")
        if not url:
            raise ValueError("DATABASE_URL required for CheckpointStore")

        # Convert to async URL for asyncpg
        async_url = _convert_to_async_url(url)
        self._sync_url = url

        # Async engine for runtime operations
        self.engine = create_async_engine(
            async_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )

        # Async session factory
        self._async_session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Sync engine for table creation (DDL)
        self._sync_engine = create_sync_engine(url, echo=False)

    def init_tables(self) -> None:
        """Create checkpoint table if not exists (sync for DDL)."""
        SQLModel.metadata.create_all(self._sync_engine, tables=[WorkflowCheckpoint.__table__])

    async def ping(self) -> bool:
        """
        Verify database connectivity with a lightweight query.

        Returns:
            True if database is reachable, False otherwise
        """
        try:
            async with self._async_session_factory() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.warning(f"Database ping failed: {e}")
            return False

    async def save(
        self,
        run_id: str,
        next_step_index: int,
        last_result_hash: Optional[str] = None,
        step_outputs: Optional[Dict[str, Any]] = None,
        status: str = "running",
        workflow_id: str = "",
        tenant_id: str = "",
        expected_version: Optional[int] = None,
        started_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
    ) -> str:
        """
        Save or update checkpoint with optimistic locking (async).

        Args:
            run_id: Unique run identifier
            next_step_index: Next step to execute (0-based)
            last_result_hash: Hash of last step result (for replay verification)
            step_outputs: Dict of step_id -> output (for dependency resolution)
            status: Current status (running, completed, aborted, failed)
            workflow_id: Optional workflow ID for reference
            tenant_id: Optional tenant ID for multi-tenant isolation
            expected_version: Expected version for optimistic locking (None for new)
            started_at: Optional step start time
            ended_at: Optional step end time

        Returns:
            Content hash of the saved checkpoint

        Raises:
            CheckpointVersionConflictError: If expected_version doesn't match
        """
        now = datetime.now(timezone.utc)
        step_outputs_json = json.dumps(step_outputs or {}, sort_keys=True)

        async with self._async_session_factory() as session:
            async with session.begin():
                # Use raw SQL for get to work with async session
                result = await session.execute(select(WorkflowCheckpoint).where(WorkflowCheckpoint.run_id == run_id))
                existing = result.scalar_one_or_none()

                if existing:
                    # Optimistic locking check
                    if expected_version is not None and existing.version != expected_version:
                        raise CheckpointVersionConflictError(
                            run_id=run_id,
                            expected_version=expected_version,
                            actual_version=existing.version,
                        )

                    existing.next_step_index = next_step_index
                    existing.last_result_hash = last_result_hash
                    existing.step_outputs_json = step_outputs_json
                    existing.status = status
                    existing.updated_at = now
                    existing.version = existing.version + 1  # Increment version
                    if workflow_id:
                        existing.workflow_id = workflow_id
                    if tenant_id:
                        existing.tenant_id = tenant_id
                    if started_at:
                        existing.started_at = started_at
                    if ended_at:
                        existing.ended_at = ended_at
                    session.add(existing)
                else:
                    checkpoint = WorkflowCheckpoint(
                        run_id=run_id,
                        workflow_id=workflow_id,
                        tenant_id=tenant_id,
                        next_step_index=next_step_index,
                        last_result_hash=last_result_hash,
                        step_outputs_json=step_outputs_json,
                        status=status,
                        version=1,  # Initial version
                        created_at=now,
                        updated_at=now,
                        started_at=started_at or now,
                        ended_at=ended_at,
                    )
                    session.add(checkpoint)
                # Commit happens automatically at end of async with session.begin()

        # Compute content hash for replay verification
        content = {
            "run_id": run_id,
            "next_step_index": next_step_index,
            "status": status,
            "step_outputs": step_outputs or {},
        }
        content_hash = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]

        logger.debug(
            "checkpoint_saved",
            extra={
                "run_id": run_id,
                "next_step_index": next_step_index,
                "status": status,
                "content_hash": content_hash,
            },
        )

        return content_hash

    async def save_with_retry(
        self,
        run_id: str,
        next_step_index: int,
        last_result_hash: Optional[str] = None,
        step_outputs: Optional[Dict[str, Any]] = None,
        status: str = "running",
        workflow_id: str = "",
        tenant_id: str = "",
        max_retries: int = 3,
    ) -> str:
        """
        Save checkpoint with automatic retry on version conflict.

        Args:
            run_id: Unique run identifier
            next_step_index: Next step to execute
            last_result_hash: Hash of last step result
            step_outputs: Dict of step_id -> output
            status: Current status
            workflow_id: Optional workflow ID
            tenant_id: Optional tenant ID
            max_retries: Max retry attempts on conflict

        Returns:
            Content hash of the saved checkpoint

        Raises:
            CheckpointVersionConflictError: If all retries exhausted
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                # Load current version
                current = await self.load(run_id)
                expected_version = current.version if current else None

                return await self.save(
                    run_id=run_id,
                    next_step_index=next_step_index,
                    last_result_hash=last_result_hash,
                    step_outputs=step_outputs,
                    status=status,
                    workflow_id=workflow_id,
                    tenant_id=tenant_id,
                    expected_version=expected_version,
                )
            except CheckpointVersionConflictError as e:
                last_error = e
                logger.warning(
                    "checkpoint_version_conflict",
                    extra={
                        "run_id": run_id,
                        "attempt": attempt + 1,
                        "expected": e.expected_version,
                        "actual": e.actual_version,
                    },
                )
                continue

        raise last_error or CheckpointVersionConflictError(run_id, -1, -1)

    async def load(self, run_id: str) -> Optional[CheckpointData]:
        """
        Load checkpoint for a run (async).

        Args:
            run_id: Unique run identifier

        Returns:
            CheckpointData if found, None otherwise
        """
        async with self._async_session_factory() as session:
            result = await session.execute(select(WorkflowCheckpoint).where(WorkflowCheckpoint.run_id == run_id))
            checkpoint = result.scalar_one_or_none()

            if checkpoint is None:
                return None

            return CheckpointData(
                run_id=checkpoint.run_id,
                workflow_id=checkpoint.workflow_id,
                tenant_id=checkpoint.tenant_id,
                next_step_index=checkpoint.next_step_index,
                last_result_hash=checkpoint.last_result_hash,
                step_outputs=checkpoint.step_outputs,
                status=checkpoint.status,
                version=checkpoint.version,
                created_at=checkpoint.created_at,
                updated_at=checkpoint.updated_at,
                started_at=checkpoint.started_at,
                ended_at=checkpoint.ended_at,
            )

    async def delete(self, run_id: str) -> bool:
        """
        Delete checkpoint for a run (async).

        Args:
            run_id: Unique run identifier

        Returns:
            True if deleted, False if not found
        """
        async with self._async_session_factory() as session:
            async with session.begin():
                result = await session.execute(select(WorkflowCheckpoint).where(WorkflowCheckpoint.run_id == run_id))
                checkpoint = result.scalar_one_or_none()
                if checkpoint:
                    await session.delete(checkpoint)
                    return True
                return False

    async def list_running(self, limit: int = 100, tenant_id: Optional[str] = None) -> list[CheckpointData]:
        """
        List running workflows (for recovery on startup, async).

        Args:
            limit: Maximum number of results
            tenant_id: Optional tenant ID filter

        Returns:
            List of CheckpointData for running workflows
        """
        async with self._async_session_factory() as session:
            statement = select(WorkflowCheckpoint).where(WorkflowCheckpoint.status == "running")
            if tenant_id:
                statement = statement.where(WorkflowCheckpoint.tenant_id == tenant_id)
            statement = statement.limit(limit)

            result = await session.execute(statement)
            rows = result.scalars().all()

            return [
                CheckpointData(
                    run_id=r.run_id,
                    workflow_id=r.workflow_id,
                    tenant_id=r.tenant_id,
                    next_step_index=r.next_step_index,
                    last_result_hash=r.last_result_hash,
                    step_outputs=r.step_outputs,
                    status=r.status,
                    version=r.version,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                    started_at=r.started_at,
                    ended_at=r.ended_at,
                )
                for r in rows
            ]


# In-memory checkpoint store for testing
class InMemoryCheckpointStore:
    """
    In-memory checkpoint store for unit tests.

    Same interface as CheckpointStore but no DB dependency.
    Includes version-based optimistic locking for consistency.
    Uses asyncio.Lock for proper async concurrency control.
    """

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()  # Async lock for concurrent async tests

    def init_tables(self) -> None:
        pass

    async def ping(self) -> bool:
        """Always returns True for in-memory store."""
        return True

    async def save(
        self,
        run_id: str,
        next_step_index: int,
        last_result_hash: Optional[str] = None,
        step_outputs: Optional[Dict[str, Any]] = None,
        status: str = "running",
        workflow_id: str = "",
        tenant_id: str = "",
        expected_version: Optional[int] = None,
        started_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
    ) -> str:
        now = datetime.now(timezone.utc)

        async with self._lock:
            existing = self._store.get(run_id)

            if existing:
                # Optimistic locking check
                if expected_version is not None and existing["version"] != expected_version:
                    raise CheckpointVersionConflictError(
                        run_id=run_id,
                        expected_version=expected_version,
                        actual_version=existing["version"],
                    )

                self._store[run_id] = {
                    "run_id": run_id,
                    "workflow_id": workflow_id or existing.get("workflow_id", ""),
                    "tenant_id": tenant_id or existing.get("tenant_id", ""),
                    "next_step_index": next_step_index,
                    "last_result_hash": last_result_hash,
                    "step_outputs": step_outputs or {},
                    "status": status,
                    "version": existing["version"] + 1,  # Increment version
                    "created_at": existing["created_at"],
                    "updated_at": now,
                    "started_at": started_at or existing.get("started_at"),
                    "ended_at": ended_at,
                }
            else:
                self._store[run_id] = {
                    "run_id": run_id,
                    "workflow_id": workflow_id,
                    "tenant_id": tenant_id,
                    "next_step_index": next_step_index,
                    "last_result_hash": last_result_hash,
                    "step_outputs": step_outputs or {},
                    "status": status,
                    "version": 1,  # Initial version
                    "created_at": now,
                    "updated_at": now,
                    "started_at": started_at or now,
                    "ended_at": ended_at,
                }

        content = {
            "run_id": run_id,
            "next_step_index": next_step_index,
            "status": status,
            "step_outputs": step_outputs or {},
        }
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]

    async def save_with_retry(
        self,
        run_id: str,
        next_step_index: int,
        last_result_hash: Optional[str] = None,
        step_outputs: Optional[Dict[str, Any]] = None,
        status: str = "running",
        workflow_id: str = "",
        tenant_id: str = "",
        max_retries: int = 3,
    ) -> str:
        """
        Save checkpoint with automatic retry on version conflict.
        Same interface as CheckpointStore.save_with_retry.
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                current = await self.load(run_id)
                expected_version = current.version if current else None

                return await self.save(
                    run_id=run_id,
                    next_step_index=next_step_index,
                    last_result_hash=last_result_hash,
                    step_outputs=step_outputs,
                    status=status,
                    workflow_id=workflow_id,
                    tenant_id=tenant_id,
                    expected_version=expected_version,
                )
            except CheckpointVersionConflictError as e:
                last_error = e
                continue

        raise last_error or CheckpointVersionConflictError(run_id, -1, -1)

    async def load(self, run_id: str) -> Optional[CheckpointData]:
        async with self._lock:
            data = self._store.get(run_id)
            if data is None:
                return None

            # Return data while still holding lock to prevent race conditions
            return CheckpointData(
                run_id=data["run_id"],
                workflow_id=data["workflow_id"],
                tenant_id=data.get("tenant_id", ""),
                next_step_index=data["next_step_index"],
                last_result_hash=data["last_result_hash"],
                step_outputs=data["step_outputs"],
                status=data["status"],
                version=data["version"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                started_at=data.get("started_at"),
                ended_at=data.get("ended_at"),
            )

    async def delete(self, run_id: str) -> bool:
        async with self._lock:
            if run_id in self._store:
                del self._store[run_id]
                return True
            return False

    async def list_running(self, limit: int = 100, tenant_id: Optional[str] = None) -> list[CheckpointData]:
        results = []
        async with self._lock:
            for run_id, data in self._store.items():
                if data["status"] == "running":
                    if tenant_id and data.get("tenant_id") != tenant_id:
                        continue
                    results.append(
                        CheckpointData(
                            run_id=data["run_id"],
                            workflow_id=data["workflow_id"],
                            tenant_id=data.get("tenant_id", ""),
                            next_step_index=data["next_step_index"],
                            last_result_hash=data["last_result_hash"],
                            step_outputs=data["step_outputs"],
                            status=data["status"],
                            version=data["version"],
                            created_at=data["created_at"],
                            updated_at=data["updated_at"],
                            started_at=data.get("started_at"),
                            ended_at=data.get("ended_at"),
                        )
                    )
                    if len(results) >= limit:
                        break
        return results
