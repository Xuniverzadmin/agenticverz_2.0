# M11 Audit Store
# Append-only operation log for deterministic replay

import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("m11.audit")


@dataclass
class OpRecord:
    """Single operation record in the audit log."""
    op_id: str
    workflow_run_id: str
    op_index: int
    op_type: str  # skill name
    args: Dict[str, Any]
    args_hash: str
    skill_version: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    result_hash: Optional[str] = None
    status: str = "pending"
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    transient: bool = False
    idempotency_key: Optional[str] = None
    tenant_id: str = "default"
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


def compute_hash(data: Any) -> str:
    """Compute SHA256 hash of JSON-serializable data."""
    canonical = json.dumps(data, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:32]


class AuditStore:
    """
    Append-only audit store for M11 skill operations.

    Provides:
    - Record operations with monotonic op_index
    - Retrieve operations for replay
    - Update operation results
    - Query workflow summary
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL not provided")

        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)

    def append_op(
        self,
        workflow_run_id: str,
        op_type: str,
        args: Dict[str, Any],
        skill_version: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        tenant_id: str = "default",
        transient: bool = False,
    ) -> OpRecord:
        """
        Append a new operation to the audit log.

        Args:
            workflow_run_id: Unique workflow run identifier
            op_type: Skill name
            args: Skill arguments
            skill_version: Skill version
            idempotency_key: Optional idempotency key
            tenant_id: Tenant identifier
            transient: If True, operation can be skipped in replay

        Returns:
            OpRecord with assigned op_id and op_index
        """
        op_id = f"op_{uuid.uuid4().hex[:16]}"
        args_hash = compute_hash(args)

        with self.Session() as session:
            # Get next op_index atomically
            result = session.execute(
                text("SELECT m11_audit.next_op_index(:wf_id)"),
                {"wf_id": workflow_run_id}
            )
            op_index = result.scalar()

            # Insert operation
            session.execute(
                text("""
                    INSERT INTO m11_audit.ops
                    (op_id, workflow_run_id, op_index, op_type, skill_version,
                     args, args_hash, status, idempotency_key, tenant_id, transient)
                    VALUES
                    (:op_id, :wf_id, :op_index, :op_type, :skill_version,
                     CAST(:args_json AS jsonb), :args_hash, 'pending', :idem_key, :tenant_id, :transient)
                """),
                {
                    "op_id": op_id,
                    "wf_id": workflow_run_id,
                    "op_index": op_index,
                    "op_type": op_type,
                    "skill_version": skill_version,
                    "args_json": json.dumps(args),
                    "args_hash": args_hash,
                    "idem_key": idempotency_key,
                    "tenant_id": tenant_id,
                    "transient": transient,
                }
            )
            session.commit()

            return OpRecord(
                op_id=op_id,
                workflow_run_id=workflow_run_id,
                op_index=op_index,
                op_type=op_type,
                args=args,
                args_hash=args_hash,
                skill_version=skill_version,
                idempotency_key=idempotency_key,
                tenant_id=tenant_id,
                transient=transient,
                status="pending",
            )

    def update_result(
        self,
        op_id: str,
        result: Dict[str, Any],
        status: str = "completed",
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        """Update operation with result after execution."""
        result_hash = compute_hash(result)

        with self.Session() as session:
            session.execute(
                text("""
                    UPDATE m11_audit.ops
                    SET result = CAST(:result_json AS jsonb),
                        result_hash = :result_hash,
                        status = :status,
                        error_code = :error_code,
                        error_message = :error_message,
                        duration_ms = :duration_ms,
                        completed_at = now()
                    WHERE op_id = :op_id
                """),
                {
                    "op_id": op_id,
                    "result_json": json.dumps(result),
                    "result_hash": result_hash,
                    "status": status,
                    "error_code": error_code,
                    "error_message": error_message,
                    "duration_ms": duration_ms,
                }
            )
            session.commit()

    def get_ops(self, workflow_run_id: str) -> List[OpRecord]:
        """Get all operations for a workflow in op_index order."""
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT op_id, workflow_run_id, op_index, op_type, skill_version,
                           args, args_hash, result, result_hash, status,
                           error_code, error_message, duration_ms, transient,
                           idempotency_key, tenant_id, created_at, completed_at
                    FROM m11_audit.ops
                    WHERE workflow_run_id = :wf_id
                    ORDER BY op_index
                """),
                {"wf_id": workflow_run_id}
            )

            ops = []
            for row in result:
                ops.append(OpRecord(
                    op_id=row[0],
                    workflow_run_id=row[1],
                    op_index=row[2],
                    op_type=row[3],
                    skill_version=row[4],
                    args=row[5] if isinstance(row[5], dict) else json.loads(row[5]) if row[5] else {},
                    args_hash=row[6],
                    result=row[7] if isinstance(row[7], dict) else json.loads(row[7]) if row[7] else None,
                    result_hash=row[8],
                    status=row[9],
                    error_code=row[10],
                    error_message=row[11],
                    duration_ms=row[12],
                    transient=row[13],
                    idempotency_key=row[14],
                    tenant_id=row[15],
                    created_at=row[16],
                    completed_at=row[17],
                ))
            return ops

    def get_op(self, op_id: str) -> Optional[OpRecord]:
        """Get a single operation by ID."""
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT op_id, workflow_run_id, op_index, op_type, skill_version,
                           args, args_hash, result, result_hash, status,
                           error_code, error_message, duration_ms, transient,
                           idempotency_key, tenant_id, created_at, completed_at
                    FROM m11_audit.ops
                    WHERE op_id = :op_id
                """),
                {"op_id": op_id}
            )
            row = result.fetchone()
            if not row:
                return None

            return OpRecord(
                op_id=row[0],
                workflow_run_id=row[1],
                op_index=row[2],
                op_type=row[3],
                skill_version=row[4],
                args=row[5] if isinstance(row[5], dict) else json.loads(row[5]) if row[5] else {},
                args_hash=row[6],
                result=row[7] if isinstance(row[7], dict) else json.loads(row[7]) if row[7] else None,
                result_hash=row[8],
                status=row[9],
                error_code=row[10],
                error_message=row[11],
                duration_ms=row[12],
                transient=row[13],
                idempotency_key=row[14],
                tenant_id=row[15],
                created_at=row[16],
                completed_at=row[17],
            )

    def record_replay_run(
        self,
        replay_id: str,
        workflow_run_id: str,
        mode: str,
        ops_total: int,
    ) -> None:
        """Record start of a replay run."""
        with self.Session() as session:
            session.execute(
                text("""
                    INSERT INTO m11_audit.replay_runs
                    (replay_id, workflow_run_id, mode, status, ops_total)
                    VALUES (:replay_id, :wf_id, :mode, 'running', :ops_total)
                """),
                {
                    "replay_id": replay_id,
                    "wf_id": workflow_run_id,
                    "mode": mode,
                    "ops_total": ops_total,
                }
            )
            session.commit()

    def complete_replay_run(
        self,
        replay_id: str,
        status: str,
        ops_verified: int,
        ops_failed: int,
        ops_skipped: int,
        first_mismatch_op_index: Optional[int] = None,
        mismatch_diff: Optional[Dict] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Record completion of a replay run."""
        with self.Session() as session:
            session.execute(
                text("""
                    UPDATE m11_audit.replay_runs
                    SET status = :status,
                        ops_verified = :ops_verified,
                        ops_failed = :ops_failed,
                        ops_skipped = :ops_skipped,
                        first_mismatch_op_index = :first_mismatch,
                        mismatch_diff = CAST(:diff_json AS jsonb),
                        error_message = :error_msg,
                        completed_at = now()
                    WHERE replay_id = :replay_id
                """),
                {
                    "replay_id": replay_id,
                    "status": status,
                    "ops_verified": ops_verified,
                    "ops_failed": ops_failed,
                    "ops_skipped": ops_skipped,
                    "first_mismatch": first_mismatch_op_index,
                    "diff_json": json.dumps(mismatch_diff) if mismatch_diff else None,
                    "error_msg": error_message,
                }
            )
            session.commit()
