# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync/async
# Role: Onboarding Stage Handlers (GAP-071 to GAP-077)
# Callers: KnowledgeLifecycleManager via StageRegistry
# Allowed Imports: stdlib, L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: GAP-071-077, GAP_IMPLEMENTATION_PLAN_V1.md

"""
Onboarding Stage Handlers

These handlers implement the "dumb plugin" contract for knowledge plane onboarding.

Onboarding Path:
    DRAFT → PENDING_VERIFY → VERIFIED → INGESTING → INDEXED →
    CLASSIFIED → PENDING_ACTIVATE → ACTIVE

Each handler:
- Performs ONLY its specific operation
- Returns success/failure
- Does NOT manage state
- Does NOT emit events
- Does NOT check policies

The KnowledgeLifecycleManager orchestrates everything else.
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState

from .base import BaseStageHandler, StageContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class RegisterHandler(BaseStageHandler):
    """
    GAP-071: Register knowledge plane.

    Creates the initial knowledge plane record in DRAFT state.
    This is a special handler - it doesn't transition FROM a state,
    it creates a new entity.

    Responsibilities:
    - Validate registration request
    - Create plane configuration
    - Initialize metadata

    Does NOT:
    - Create database records (orchestrator does that)
    - Set state (orchestrator does that)
    - Emit events (orchestrator does that)
    """

    @property
    def stage_name(self) -> str:
        return "register"

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        # Register doesn't execute FROM a state - it creates new planes
        # We use an empty tuple since orchestrator handles this specially
        return ()

    async def validate(self, context: StageContext) -> Optional[str]:
        """Validate registration request."""
        # Check required fields
        if not context.tenant_id:
            return "tenant_id is required for registration"

        # Check config has minimum required fields
        config = context.config or {}
        if not config.get("name") and not config.get("source_type"):
            return "Registration requires either 'name' or 'source_type' in config"

        return None

    async def execute(self, context: StageContext) -> StageResult:
        """
        Execute registration.

        Note: This doesn't create the plane - the orchestrator does.
        This handler validates and prepares the registration data.
        """
        try:
            config = context.config or {}

            # Generate plane name if not provided
            name = config.get("name") or f"Knowledge Plane {context.plane_id}"

            # Prepare registration data
            registration_data = {
                "name": name,
                "source_type": config.get("source_type", "unknown"),
                "description": config.get("description"),
                "registered_at": datetime.now(timezone.utc).isoformat(),
                "registered_by": context.actor_id,
            }

            logger.info(
                f"RegisterHandler: Prepared registration for plane {context.plane_id} "
                f"(tenant={context.tenant_id})"
            )

            return StageResult.ok(
                message=f"Registration prepared for {name}",
                registration_data=registration_data,
            )

        except Exception as e:
            logger.error(f"RegisterHandler failed: {e}")
            return StageResult.fail(
                message=f"Registration failed: {str(e)}",
                error_code="REGISTER_FAILED",
            )


class VerifyHandler(BaseStageHandler):
    """
    GAP-072: Verify knowledge plane connectivity.

    Verifies that the knowledge source is accessible and credentials are valid.

    Responsibilities:
    - Test connection to source
    - Validate credentials
    - Check source schema/structure

    Does NOT:
    - Store credentials (already done at registration)
    - Update state (orchestrator does that)
    - Retry on failure (orchestrator handles retry logic)
    """

    @property
    def stage_name(self) -> str:
        return "verify"

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        return (KnowledgePlaneLifecycleState.DRAFT,)

    async def validate(self, context: StageContext) -> Optional[str]:
        """Validate verification request."""
        # Check state first (from base class)
        state_error = await super().validate(context)
        if state_error:
            return state_error

        # Note: In a real implementation, you'd check for connection details
        # For now, we validate that basic config exists
        if not context.config:
            return "No configuration provided for verification"
        return None

    async def execute(self, context: StageContext) -> StageResult:
        """
        Execute verification.

        This is an async operation - returns PENDING with job_id.
        The orchestrator will call complete_job when verification finishes.
        """
        try:
            config = context.config or {}

            # In a real implementation, this would:
            # 1. Test connection to the data source
            # 2. Validate credentials
            # 3. Check source is readable
            # 4. Verify schema compatibility

            # For now, simulate verification
            source_type = config.get("source_type", "unknown")

            # Generate verification job ID
            job_id = f"verify_{context.plane_id}_{int(datetime.now(timezone.utc).timestamp())}"

            # Simulate async verification
            # In production: queue actual verification job
            verification_result = await self._simulate_verification(
                source_type=source_type,
                connection_string=context.connection_string,
            )

            if verification_result["success"]:
                return StageResult.ok(
                    message="Verification successful",
                    verified_at=datetime.now(timezone.utc).isoformat(),
                    source_type=source_type,
                    schema_info=verification_result.get("schema_info"),
                    connection_latency_ms=verification_result.get("latency_ms", 0),
                )
            else:
                return StageResult.fail(
                    message=f"Verification failed: {verification_result.get('error')}",
                    error_code="VERIFICATION_FAILED",
                    source_type=source_type,
                )

        except Exception as e:
            logger.error(f"VerifyHandler failed: {e}")
            return StageResult.fail(
                message=f"Verification error: {str(e)}",
                error_code="VERIFY_ERROR",
            )

    async def _simulate_verification(
        self,
        source_type: str,
        connection_string: Optional[str],
    ) -> Dict[str, Any]:
        """Simulate verification for testing."""
        # Simulate network latency
        await asyncio.sleep(0.01)  # 10ms

        # Simulate verification result
        return {
            "success": True,
            "latency_ms": 45,
            "schema_info": {
                "tables": ["documents", "metadata"],
                "record_count_estimate": 10000,
            },
        }


class IngestHandler(BaseStageHandler):
    """
    GAP-073: Ingest data from knowledge source.
    GAP-159: Real execution via DataIngestionExecutor.

    Reads data from the source and stores it for processing.

    Responsibilities:
    - Read data from source via ConnectorRegistry
    - Transform to internal format
    - Store raw data for indexing

    Does NOT:
    - Create indexes (IndexHandler does that)
    - Classify data (ClassifyHandler does that)
    - Track progress in state (orchestrator does that)
    """

    @property
    def stage_name(self) -> str:
        return "ingest"

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        return (KnowledgePlaneLifecycleState.VERIFIED,)

    async def validate(self, context: StageContext) -> Optional[str]:
        """Validate ingestion request."""
        if not context.config:
            return "No configuration for ingestion"
        return None

    async def execute(self, context: StageContext) -> StageResult:
        """
        Execute data ingestion.

        Uses DataIngestionExecutor (GAP-159) for real data source reads.
        Falls back to simulation if no connector configured.
        """
        try:
            config = context.config or {}

            # GAP-159: Use real ingestion executor
            from app.services.lifecycle_stages.execution import (
                get_ingestion_executor,
            )

            executor = get_ingestion_executor()

            # Execute ingestion with progress tracking
            ingestion_result = await executor.execute(
                plane_id=context.plane_id,
                tenant_id=context.tenant_id,
                config=config,
                progress_callback=None,  # Orchestrator handles progress
            )

            if ingestion_result.success:
                # Store batches in context metadata for next stages
                return StageResult.ok(
                    message="Ingestion complete",
                    records_ingested=ingestion_result.records_ingested,
                    bytes_processed=ingestion_result.bytes_processed,
                    batch_count=len(ingestion_result.batches),
                    source_type=ingestion_result.source_type.value,
                    duration_ms=ingestion_result.duration_ms,
                    ingested_at=datetime.now(timezone.utc).isoformat(),
                    # Store batches for indexing stage
                    _ingestion_batches=[
                        {
                            "batch_id": b.batch_id,
                            "record_count": b.record_count,
                            "byte_size": b.byte_size,
                            "checksum": b.checksum,
                        }
                        for b in ingestion_result.batches
                    ],
                )
            else:
                return StageResult.fail(
                    message=f"Ingestion failed: {ingestion_result.error}",
                    error_code=ingestion_result.error_code or "INGESTION_FAILED",
                    source_type=ingestion_result.source_type.value,
                    duration_ms=ingestion_result.duration_ms,
                )

        except Exception as e:
            logger.error(f"IngestHandler failed: {e}")
            return StageResult.fail(
                message=f"Ingestion error: {str(e)}",
                error_code="INGEST_ERROR",
            )


class IndexHandler(BaseStageHandler):
    """
    GAP-074: Create indexes and embeddings.
    GAP-160: Real execution via IndexingExecutor.

    Creates vector embeddings and search indexes for the ingested data.

    Responsibilities:
    - Generate embeddings via configured provider
    - Create vector indexes in VectorConnector
    - Build search structures

    Does NOT:
    - Classify data (ClassifyHandler does that)
    - Manage index lifecycle (orchestrator does that)
    """

    @property
    def stage_name(self) -> str:
        return "index"

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        return (KnowledgePlaneLifecycleState.INGESTING,)

    async def validate(self, context: StageContext) -> Optional[str]:
        """Validate indexing request."""
        return None

    async def execute(self, context: StageContext) -> StageResult:
        """
        Execute indexing.

        Uses IndexingExecutor (GAP-160) for real embedding generation
        and vector storage.
        """
        try:
            config = context.config or {}

            # GAP-160: Use real indexing executor
            from app.services.lifecycle_stages.execution import (
                get_indexing_executor,
                IngestionBatch,
                IngestionSourceType,
            )

            executor = get_indexing_executor()

            # Get ingestion batches from metadata
            # In production, these would be retrieved from storage
            ingestion_batch_data = context.metadata.get("_ingestion_batches", [])

            # Reconstruct batch objects (simplified - in production use storage)
            ingestion_batches = []
            for batch_info in ingestion_batch_data:
                batch = IngestionBatch(
                    batch_id=batch_info.get("batch_id", f"{context.plane_id}_batch"),
                    records=batch_info.get("records", []),
                    source_type=IngestionSourceType.UNKNOWN,
                    record_count=batch_info.get("record_count", 0),
                    byte_size=batch_info.get("byte_size", 0),
                )
                ingestion_batches.append(batch)

            # If no batches from metadata, create simulated batch for testing
            if not ingestion_batches:
                ingestion_batches = [
                    IngestionBatch(
                        batch_id=f"{context.plane_id}_sim",
                        records=[
                            {"id": f"doc_{i}", "content": f"Document {i} content"}
                            for i in range(100)
                        ],
                        source_type=IngestionSourceType.UNKNOWN,
                    )
                ]

            # Execute indexing
            indexing_result = await executor.execute(
                plane_id=context.plane_id,
                tenant_id=context.tenant_id,
                ingestion_batches=ingestion_batches,
                config=config,
                progress_callback=None,  # Orchestrator handles progress
            )

            if indexing_result.success:
                return StageResult.ok(
                    message="Indexing complete",
                    vectors_created=indexing_result.vectors_created,
                    index_size_bytes=indexing_result.index_size_bytes,
                    dimensions=indexing_result.dimensions,
                    duration_ms=indexing_result.duration_ms,
                    indexed_at=datetime.now(timezone.utc).isoformat(),
                )
            else:
                return StageResult.fail(
                    message=f"Indexing failed: {indexing_result.error}",
                    error_code=indexing_result.error_code or "INDEXING_FAILED",
                    duration_ms=indexing_result.duration_ms,
                )

        except Exception as e:
            logger.error(f"IndexHandler failed: {e}")
            return StageResult.fail(
                message=f"Indexing error: {str(e)}",
                error_code="INDEX_ERROR",
            )


class ClassifyHandler(BaseStageHandler):
    """
    GAP-075: Classify data sensitivity and schema.
    GAP-161: Real execution via ClassificationExecutor.

    Analyzes the data to determine:
    - Sensitivity level (public, internal, confidential, restricted)
    - Data schema/structure
    - Content categories
    - PII presence

    Responsibilities:
    - Detect PII via pattern matching
    - Classify sensitivity based on content
    - Categorize content

    Does NOT:
    - Enforce policies (policy gate does that)
    - Block activation (orchestrator does that)
    """

    @property
    def stage_name(self) -> str:
        return "classify"

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        return (KnowledgePlaneLifecycleState.INDEXED,)

    async def validate(self, context: StageContext) -> Optional[str]:
        """Validate classification request."""
        return None

    async def execute(self, context: StageContext) -> StageResult:
        """
        Execute classification.

        Uses ClassificationExecutor (GAP-161) for real PII detection
        and sensitivity classification.
        """
        try:
            # GAP-161: Use real classification executor
            from app.services.lifecycle_stages.execution import (
                get_classification_executor,
                IngestionBatch,
                IngestionSourceType,
            )

            executor = get_classification_executor()

            # Get ingestion batches from metadata
            # In production, these would be retrieved from storage
            ingestion_batch_data = context.metadata.get("_ingestion_batches", [])

            # Reconstruct batch objects
            ingestion_batches = []
            for batch_info in ingestion_batch_data:
                batch = IngestionBatch(
                    batch_id=batch_info.get("batch_id", f"{context.plane_id}_batch"),
                    records=batch_info.get("records", []),
                    source_type=IngestionSourceType.UNKNOWN,
                    record_count=batch_info.get("record_count", 0),
                    byte_size=batch_info.get("byte_size", 0),
                )
                ingestion_batches.append(batch)

            # If no batches from metadata, create simulated batch for testing
            if not ingestion_batches:
                ingestion_batches = [
                    IngestionBatch(
                        batch_id=f"{context.plane_id}_sim",
                        records=[
                            {"id": f"doc_{i}", "content": f"Technical document {i}"}
                            for i in range(50)
                        ],
                        source_type=IngestionSourceType.UNKNOWN,
                    )
                ]

            # Execute classification
            classification_result = await executor.execute(
                plane_id=context.plane_id,
                tenant_id=context.tenant_id,
                ingestion_batches=ingestion_batches,
                progress_callback=None,  # Orchestrator handles progress
            )

            if classification_result.success:
                return StageResult.ok(
                    message="Classification complete",
                    sensitivity_level=classification_result.sensitivity_level.value,
                    pii_detected=classification_result.pii_detected,
                    pii_count=len(classification_result.pii_detections),
                    content_categories=classification_result.content_categories,
                    schema_version=classification_result.schema_version,
                    duration_ms=classification_result.duration_ms,
                    classified_at=datetime.now(timezone.utc).isoformat(),
                )
            else:
                return StageResult.fail(
                    message=f"Classification failed: {classification_result.error}",
                    error_code=classification_result.error_code or "CLASSIFICATION_FAILED",
                    duration_ms=classification_result.duration_ms,
                )

        except Exception as e:
            logger.error(f"ClassifyHandler failed: {e}")
            return StageResult.fail(
                message=f"Classification error: {str(e)}",
                error_code="CLASSIFY_ERROR",
            )


class ActivateHandler(BaseStageHandler):
    """
    GAP-076: Activate knowledge plane.

    Final activation steps before the plane becomes operational.

    Responsibilities:
    - Validate policies are bound
    - Initialize runtime state
    - Set up access controls

    Does NOT:
    - Check policy gate (orchestrator does that via GAP-087)
    - Emit activation event (orchestrator does that)

    Note: This handler runs AFTER the policy gate check.
    The orchestrator calls GAP-087 policy gate first, then this handler.
    """

    @property
    def stage_name(self) -> str:
        return "activate"

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        return (KnowledgePlaneLifecycleState.PENDING_ACTIVATE,)

    async def validate(self, context: StageContext) -> Optional[str]:
        """Validate activation request."""
        # Note: Policy binding is checked by orchestrator's policy gate
        # This handler just validates the plane is ready
        return None

    async def execute(self, context: StageContext) -> StageResult:
        """Execute activation."""
        try:
            # In a real implementation:
            # 1. Initialize query endpoint
            # 2. Set up rate limits
            # 3. Configure access controls
            # 4. Start usage tracking

            activation_result = await self._simulate_activation(
                plane_id=context.plane_id,
            )

            if activation_result["success"]:
                return StageResult.ok(
                    message="Activation complete",
                    endpoint=activation_result.get("endpoint"),
                    activated_at=datetime.now(timezone.utc).isoformat(),
                    access_controls=activation_result.get("access_controls", {}),
                )
            else:
                return StageResult.fail(
                    message=f"Activation failed: {activation_result.get('error')}",
                    error_code="ACTIVATION_FAILED",
                )

        except Exception as e:
            logger.error(f"ActivateHandler failed: {e}")
            return StageResult.fail(
                message=f"Activation error: {str(e)}",
                error_code="ACTIVATE_ERROR",
            )

    async def _simulate_activation(self, plane_id: str) -> Dict[str, Any]:
        """Simulate activation for testing."""
        await asyncio.sleep(0.01)  # 10ms
        return {
            "success": True,
            "endpoint": f"/v1/knowledge/{plane_id}/query",
            "access_controls": {
                "rate_limit": 100,
                "max_tokens": 10000,
            },
        }


class GovernHandler(BaseStageHandler):
    """
    GAP-077: Runtime governance hooks.

    Called on every access to the knowledge plane to emit governance evidence.

    Responsibilities:
    - Emit access evidence
    - Track usage metrics
    - Validate access context

    Does NOT:
    - Enforce policies (runtime enforcer does that)
    - Block access (returns evidence, enforcer decides)

    Note: This is not a state transition handler.
    It's called at runtime when the plane is ACTIVE.
    """

    @property
    def stage_name(self) -> str:
        return "govern"

    @property
    def handles_states(self) -> tuple[KnowledgePlaneLifecycleState, ...]:
        return (KnowledgePlaneLifecycleState.ACTIVE,)

    async def validate(self, context: StageContext) -> Optional[str]:
        """Validate governance request."""
        return None

    async def execute(self, context: StageContext) -> StageResult:
        """
        Execute governance check.

        This is called on access, not on transition.
        Returns governance evidence for the access.
        """
        try:
            # Generate evidence hash for this access
            evidence_data = {
                "plane_id": context.plane_id,
                "tenant_id": context.tenant_id,
                "actor_id": context.actor_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "access_type": context.metadata.get("access_type", "query"),
            }

            evidence_hash = hashlib.sha256(
                str(sorted(evidence_data.items())).encode()
            ).hexdigest()[:16]

            return StageResult.ok(
                message="Governance evidence generated",
                evidence_hash=evidence_hash,
                access_timestamp=evidence_data["timestamp"],
                governance_version="1.0",
            )

        except Exception as e:
            logger.error(f"GovernHandler failed: {e}")
            return StageResult.fail(
                message=f"Governance error: {str(e)}",
                error_code="GOVERN_ERROR",
            )
