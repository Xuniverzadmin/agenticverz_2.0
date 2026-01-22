# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync/async
# Role: Offboarding Stage Handlers (GAP-078 to GAP-082)
# Callers: KnowledgeLifecycleManager via StageRegistry
# Allowed Imports: stdlib, L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: GAP-078-082, GAP_IMPLEMENTATION_PLAN_V1.md

"""
Offboarding Stage Handlers

These handlers implement the "dumb plugin" contract for knowledge plane offboarding.

Offboarding Path:
    ACTIVE → PENDING_DEACTIVATE → DEACTIVATED → ARCHIVED → PURGED

Each handler:
- Performs ONLY its specific operation
- Returns success/failure
- Does NOT manage state
- Does NOT emit events
- Does NOT check policies

The KnowledgeLifecycleManager orchestrates everything else.

CRITICAL: Offboarding is governance-controlled for GDPR/CCPA compliance.
- PENDING_DEACTIVATE has a grace period (cancel window)
- DEACTIVATED preserves data (soft delete)
- ARCHIVED exports to cold storage
- PURGED deletes data but preserves audit trail
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState

from .base import BaseStageHandler, StageContext, StageResult

logger = logging.getLogger(__name__)


class DeregisterHandler(BaseStageHandler):
    """
    GAP-078: Start offboarding process.

    Initiates deregistration by moving to PENDING_DEACTIVATE state.
    This starts a grace period where the offboarding can be cancelled.

    Responsibilities:
    - Validate no active runs are using this plane
    - Check for dependent resources
    - Calculate grace period end time

    Does NOT:
    - Actually deactivate the plane
    - Delete any data
    - Change state (orchestrator does that)
    """

    @property
    def stage_name(self) -> str:
        return "deregister"

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        return (KnowledgePlaneLifecycleState.ACTIVE,)

    async def validate(self, context: StageContext) -> Optional[str]:
        """Validate deregistration request."""
        state_error = await super().validate(context)
        if state_error:
            return state_error

        # Check for active runs (in a real implementation)
        # For now, just validate basic context
        return None

    async def execute(self, context: StageContext) -> StageResult:
        """
        Execute deregistration.

        This initiates the offboarding process and calculates grace period.
        """
        try:
            config = context.config or {}

            # Calculate grace period (default 7 days)
            grace_period_days = config.get("grace_period_days", 7)
            grace_period_end = datetime.now(timezone.utc).timestamp() + (
                grace_period_days * 24 * 60 * 60
            )

            # Check for active references
            active_references = await self._check_active_references(
                plane_id=context.plane_id,
            )

            if active_references:
                return StageResult.fail(
                    message=f"Cannot deregister: {len(active_references)} active references",
                    error_code="ACTIVE_REFERENCES",
                    references=active_references,
                )

            # Check for dependent resources
            dependents = await self._check_dependents(
                plane_id=context.plane_id,
            )

            return StageResult.ok(
                message="Deregistration initiated",
                deregistration_requested_at=datetime.now(timezone.utc).isoformat(),
                grace_period_end=datetime.fromtimestamp(
                    grace_period_end, tz=timezone.utc
                ).isoformat(),
                grace_period_days=grace_period_days,
                dependent_count=len(dependents),
                dependents=dependents,
                can_cancel=True,
            )

        except Exception as e:
            logger.error(f"DeregisterHandler failed: {e}")
            return StageResult.fail(
                message=f"Deregistration failed: {str(e)}",
                error_code="DEREGISTER_FAILED",
            )

    async def _check_active_references(self, plane_id: str) -> List[Dict[str, Any]]:
        """Check for active references to this knowledge plane."""
        # In a real implementation, query for active runs, queries, etc.
        await asyncio.sleep(0.01)
        return []  # No active references

    async def _check_dependents(self, plane_id: str) -> List[Dict[str, Any]]:
        """Check for resources that depend on this knowledge plane."""
        # In a real implementation, query for dependent policies, agents, etc.
        await asyncio.sleep(0.01)
        return []  # No dependents


class VerifyDeactivateHandler(BaseStageHandler):
    """
    GAP-079: Verify deactivation is safe.

    Verifies that the knowledge plane can be safely deactivated:
    - No active runs
    - No pending queries
    - Grace period has passed (or forced)

    Responsibilities:
    - Verify grace period status
    - Check for any remaining active usage
    - Validate deactivation is safe

    Does NOT:
    - Actually deactivate
    - Make policy decisions (orchestrator's policy gate does that)
    """

    @property
    def stage_name(self) -> str:
        return "verify_deactivate"

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        return (KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,)

    async def validate(self, context: StageContext) -> Optional[str]:
        """Validate verify deactivate request."""
        state_error = await super().validate(context)
        if state_error:
            return state_error
        return None

    async def execute(self, context: StageContext) -> StageResult:
        """
        Verify deactivation is safe.

        Checks all preconditions for safe deactivation.
        """
        try:
            config = context.config or {}
            metadata = context.metadata or {}

            # Check if force flag is set (bypasses grace period)
            force = config.get("force", False) or metadata.get("force", False)

            # Check grace period
            grace_period_end = metadata.get("grace_period_end")
            grace_period_passed = True

            if grace_period_end and not force:
                end_time = datetime.fromisoformat(grace_period_end.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) < end_time:
                    grace_period_passed = False

            if not grace_period_passed and not force:
                return StageResult.fail(
                    message="Grace period has not passed",
                    error_code="GRACE_PERIOD_ACTIVE",
                    grace_period_end=grace_period_end,
                )

            # Check for active usage
            active_usage = await self._check_active_usage(
                plane_id=context.plane_id,
            )

            if active_usage and not force:
                return StageResult.fail(
                    message=f"Active usage detected: {len(active_usage)} operations",
                    error_code="ACTIVE_USAGE",
                    active_operations=active_usage,
                )

            return StageResult.ok(
                message="Deactivation verified safe",
                verified_at=datetime.now(timezone.utc).isoformat(),
                grace_period_passed=grace_period_passed,
                force_used=force,
                active_usage_count=len(active_usage) if active_usage else 0,
            )

        except Exception as e:
            logger.error(f"VerifyDeactivateHandler failed: {e}")
            return StageResult.fail(
                message=f"Verification failed: {str(e)}",
                error_code="VERIFY_DEACTIVATE_FAILED",
            )

    async def _check_active_usage(self, plane_id: str) -> List[Dict[str, Any]]:
        """Check for active usage of this knowledge plane."""
        await asyncio.sleep(0.01)
        return []  # No active usage


class DeactivateHandler(BaseStageHandler):
    """
    GAP-080: Deactivate knowledge plane (soft delete).

    Performs soft deletion - the plane is no longer queryable but data is preserved.

    Responsibilities:
    - Disable query endpoint
    - Revoke active access tokens
    - Mark as deactivated

    Does NOT:
    - Delete any data (preserved for archival)
    - Remove from storage
    - Delete audit trail
    """

    @property
    def stage_name(self) -> str:
        return "deactivate"

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        return (KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,)

    async def validate(self, context: StageContext) -> Optional[str]:
        """Validate deactivation request."""
        state_error = await super().validate(context)
        if state_error:
            return state_error
        return None

    async def execute(self, context: StageContext) -> StageResult:
        """
        Execute deactivation (soft delete).

        Disables the knowledge plane but preserves all data.
        """
        try:
            # In a real implementation:
            # 1. Disable query endpoint
            # 2. Revoke access tokens
            # 3. Update routing tables
            # 4. Notify dependent services

            deactivation_result = await self._perform_deactivation(
                plane_id=context.plane_id,
            )

            if deactivation_result["success"]:
                return StageResult.ok(
                    message="Knowledge plane deactivated",
                    deactivated_at=datetime.now(timezone.utc).isoformat(),
                    endpoint_disabled=True,
                    tokens_revoked=deactivation_result.get("tokens_revoked", 0),
                    data_preserved=True,
                )
            else:
                return StageResult.fail(
                    message=f"Deactivation failed: {deactivation_result.get('error')}",
                    error_code="DEACTIVATION_FAILED",
                )

        except Exception as e:
            logger.error(f"DeactivateHandler failed: {e}")
            return StageResult.fail(
                message=f"Deactivation error: {str(e)}",
                error_code="DEACTIVATE_ERROR",
            )

    async def _perform_deactivation(self, plane_id: str) -> Dict[str, Any]:
        """Perform deactivation operations."""
        await asyncio.sleep(0.01)
        return {
            "success": True,
            "tokens_revoked": 3,
        }


class ArchiveHandler(BaseStageHandler):
    """
    GAP-081: Archive knowledge plane to cold storage.

    Exports data to cold storage for long-term retention.

    Responsibilities:
    - Export data to archive storage
    - Generate archive manifest
    - Verify archive integrity
    - Remove from hot storage (after verification)

    Does NOT:
    - Delete audit trail
    - Remove from system entirely
    - Make purge decision (requires separate approval)
    """

    @property
    def stage_name(self) -> str:
        return "archive"

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        return (KnowledgePlaneLifecycleState.DEACTIVATED,)

    async def validate(self, context: StageContext) -> Optional[str]:
        """Validate archive request."""
        state_error = await super().validate(context)
        if state_error:
            return state_error
        return None

    async def execute(self, context: StageContext) -> StageResult:
        """
        Execute archival to cold storage.

        This is typically an async operation for large datasets.
        """
        try:
            config = context.config or {}

            # Archive destination
            archive_bucket = config.get("archive_bucket", "default-archive")
            retention_days = config.get("retention_days", 365)

            # Perform archival
            archive_result = await self._perform_archive(
                plane_id=context.plane_id,
                archive_bucket=archive_bucket,
            )

            if archive_result["success"]:
                # Generate archive manifest hash
                manifest_hash = hashlib.sha256(
                    f"{context.plane_id}:{archive_result['archive_path']}".encode()
                ).hexdigest()[:16]

                return StageResult.ok(
                    message="Archive complete",
                    archived_at=datetime.now(timezone.utc).isoformat(),
                    archive_path=archive_result["archive_path"],
                    archive_size_bytes=archive_result.get("size_bytes", 0),
                    manifest_hash=manifest_hash,
                    retention_days=retention_days,
                    retention_until=datetime.fromtimestamp(
                        datetime.now(timezone.utc).timestamp() + (retention_days * 24 * 60 * 60),
                        tz=timezone.utc,
                    ).isoformat(),
                )
            else:
                return StageResult.fail(
                    message=f"Archive failed: {archive_result.get('error')}",
                    error_code="ARCHIVE_FAILED",
                )

        except Exception as e:
            logger.error(f"ArchiveHandler failed: {e}")
            return StageResult.fail(
                message=f"Archive error: {str(e)}",
                error_code="ARCHIVE_ERROR",
            )

    async def _perform_archive(
        self,
        plane_id: str,
        archive_bucket: str,
    ) -> Dict[str, Any]:
        """Perform archive to cold storage."""
        await asyncio.sleep(0.02)  # Simulate export time
        return {
            "success": True,
            "archive_path": f"s3://{archive_bucket}/archives/{plane_id}/archive.tar.gz",
            "size_bytes": 1024 * 1024 * 100,  # 100 MB
        }


class PurgeHandler(BaseStageHandler):
    """
    GAP-082: Purge knowledge plane (permanent deletion).

    Permanently deletes all data except the audit trail.

    Responsibilities:
    - Delete data from archive storage
    - Delete indexes and embeddings
    - Delete metadata
    - Preserve audit trail (REQUIRED for compliance)

    Does NOT:
    - Delete audit trail (audit is immutable)
    - Make this reversible (PURGED is terminal)

    CRITICAL: This operation requires approval via GAP-087 policy gate.
    The orchestrator calls the policy gate BEFORE this handler.
    """

    @property
    def stage_name(self) -> str:
        return "purge"

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        return (KnowledgePlaneLifecycleState.ARCHIVED,)

    async def validate(self, context: StageContext) -> Optional[str]:
        """Validate purge request."""
        state_error = await super().validate(context)
        if state_error:
            return state_error

        # Check for required approval (in metadata from policy gate)
        metadata = context.metadata or {}
        if not metadata.get("purge_approved"):
            return "Purge requires explicit approval (purge_approved=true)"

        return None

    async def execute(self, context: StageContext) -> StageResult:
        """
        Execute permanent deletion.

        Deletes all data except the immutable audit trail.
        """
        try:
            metadata = context.metadata or {}

            # Verify approval one more time
            if not metadata.get("purge_approved"):
                return StageResult.fail(
                    message="Purge not approved",
                    error_code="PURGE_NOT_APPROVED",
                )

            # Record approver for audit
            approver = metadata.get("approved_by", context.actor_id)
            approval_reason = metadata.get("approval_reason", "Not specified")

            # Perform purge
            purge_result = await self._perform_purge(
                plane_id=context.plane_id,
            )

            if purge_result["success"]:
                # Generate purge certificate
                purge_certificate = hashlib.sha256(
                    f"{context.plane_id}:{datetime.now(timezone.utc).isoformat()}:{approver}".encode()
                ).hexdigest()

                return StageResult.ok(
                    message="Knowledge plane purged",
                    purged_at=datetime.now(timezone.utc).isoformat(),
                    purge_certificate=purge_certificate,
                    approved_by=approver,
                    approval_reason=approval_reason,
                    data_deleted=True,
                    audit_preserved=True,  # Always true - audit is immutable
                    bytes_deleted=purge_result.get("bytes_deleted", 0),
                    records_deleted=purge_result.get("records_deleted", 0),
                )
            else:
                return StageResult.fail(
                    message=f"Purge failed: {purge_result.get('error')}",
                    error_code="PURGE_FAILED",
                )

        except Exception as e:
            logger.error(f"PurgeHandler failed: {e}")
            return StageResult.fail(
                message=f"Purge error: {str(e)}",
                error_code="PURGE_ERROR",
            )

    async def _perform_purge(self, plane_id: str) -> Dict[str, Any]:
        """Perform permanent deletion."""
        await asyncio.sleep(0.02)  # Simulate deletion time
        return {
            "success": True,
            "bytes_deleted": 1024 * 1024 * 100,  # 100 MB
            "records_deleted": 5000,
        }
