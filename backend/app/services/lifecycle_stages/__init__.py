# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync/async
# Role: T4 Lifecycle Stage Handlers (GAP-071 to GAP-082, GAP-159 to GAP-161)
# Callers: KnowledgeLifecycleManager
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-071-082, GAP-159-161, GAP_IMPLEMENTATION_PLAN_V1.md

"""
T4 Lifecycle Stage Handlers

This package contains "dumb plugin" stage handlers for the Knowledge Plane lifecycle.

Design Discipline:
- Stage handlers do NOT manage state directly
- Stage handlers do NOT emit audit events
- Stage handlers do NOT check policies
- Stage handlers ONLY perform their specific operation and return success/failure

The orchestrator (KnowledgeLifecycleManager) handles:
- State management
- Audit event emission
- Policy gate checks
- Error recovery

Onboarding Stages (GAP-071 to GAP-077):
- RegisterHandler: Create knowledge plane record (DRAFT)
- VerifyHandler: Verify connectivity/credentials (PENDING_VERIFY → VERIFIED)
- IngestHandler: Ingest data from source (INGESTING → INDEXED) [GAP-159]
- IndexHandler: Create vector embeddings/indexes [GAP-160]
- ClassifyHandler: Classify data sensitivity and schema (CLASSIFIED) [GAP-161]
- ActivateHandler: Final activation steps (PENDING_ACTIVATE → ACTIVE)
- GovernHandler: Runtime governance hooks (called on access)

Offboarding Stages (GAP-078 to GAP-082):
- DeregisterHandler: Start offboarding (PENDING_DEACTIVATE)
- VerifyDeactivateHandler: Verify no active references
- DeactivateHandler: Soft-delete, preserve data (DEACTIVATED)
- ArchiveHandler: Export to cold storage (ARCHIVED)
- PurgeHandler: Delete data, keep audit trail (PURGED)

Real Execution (GAP-159 to GAP-161):
- DataIngestionExecutor: Real data source reads via ConnectorRegistry
- IndexingExecutor: Real embedding generation and vector storage
- ClassificationExecutor: Real PII detection and sensitivity classification
"""

from .base import (
    StageContext,
    StageResult,
    StageHandler,
    StageRegistry,
)
from .onboarding import (
    RegisterHandler,
    VerifyHandler,
    IngestHandler,
    IndexHandler,
    ClassifyHandler,
    ActivateHandler,
    GovernHandler,
)
from .offboarding import (
    DeregisterHandler,
    VerifyDeactivateHandler,
    DeactivateHandler,
    ArchiveHandler,
    PurgeHandler,
)
from .execution import (
    # GAP-159: Ingestion
    DataIngestionExecutor,
    IngestionBatch,
    IngestionResult,
    IngestionSourceType,
    get_ingestion_executor,
    # GAP-160: Indexing
    IndexingExecutor,
    IndexingResult,
    get_indexing_executor,
    # GAP-161: Classification
    ClassificationExecutor,
    ClassificationResult,
    SensitivityLevel,
    PIIType,
    PIIDetection,
    get_classification_executor,
    # Reset for testing
    reset_executors,
)

__all__ = [
    # Base
    "StageContext",
    "StageResult",
    "StageHandler",
    "StageRegistry",
    # Onboarding
    "RegisterHandler",
    "VerifyHandler",
    "IngestHandler",
    "IndexHandler",
    "ClassifyHandler",
    "ActivateHandler",
    "GovernHandler",
    # Offboarding
    "DeregisterHandler",
    "VerifyDeactivateHandler",
    "DeactivateHandler",
    "ArchiveHandler",
    "PurgeHandler",
    # GAP-159: Ingestion
    "DataIngestionExecutor",
    "IngestionBatch",
    "IngestionResult",
    "IngestionSourceType",
    "get_ingestion_executor",
    # GAP-160: Indexing
    "IndexingExecutor",
    "IndexingResult",
    "get_indexing_executor",
    # GAP-161: Classification
    "ClassificationExecutor",
    "ClassificationResult",
    "SensitivityLevel",
    "PIIType",
    "PIIDetection",
    "get_classification_executor",
    # Reset
    "reset_executors",
]
