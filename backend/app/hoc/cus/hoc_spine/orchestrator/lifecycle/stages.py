# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Canonical import surface for knowledge plane lifecycle stages
# Callers: tests (t4), SDK facade, worker orchestration
# Allowed Imports: hoc_spine lifecycle engines + drivers, hoc_spine base types
# Forbidden Imports: app.services.*
# artifact_class: CODE

"""
Canonical stage surface for the knowledge plane lifecycle.

This module exists to prevent split-brain imports between:
- app.services.lifecycle_stages (legacy surface)
- hoc_spine lifecycle engines/drivers (runtime surface)

All stage handlers and base types should be imported from here going forward.
"""

from app.hoc.cus.hoc_spine.services.lifecycle_stages_base import (
    BaseStageHandler,
    StageContext,
    StageHandler,
    StageRegistry,
    StageResult,
    StageStatus,
)

from app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.onboarding import (
    ActivateHandler,
    ClassifyHandler,
    GovernHandler,
    IndexHandler,
    IngestHandler,
    RegisterHandler,
    VerifyHandler,
)
from app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.offboarding import (
    ArchiveHandler,
    DeactivateHandler,
    DeregisterHandler,
    PurgeHandler,
    VerifyDeactivateHandler,
)
from app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.execution import (
    ClassificationExecutor,
    ClassificationResult,
    DataIngestionExecutor,
    IndexingExecutor,
    IndexingResult,
    IngestionBatch,
    IngestionResult,
    IngestionSourceType,
    PIIDetection,
    PIIType,
    SensitivityLevel,
    get_classification_executor,
    get_indexing_executor,
    get_ingestion_executor,
    reset_executors,
)

__all__ = [
    # Base
    "BaseStageHandler",
    "StageContext",
    "StageHandler",
    "StageRegistry",
    "StageResult",
    "StageStatus",
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
    # Execution
    "DataIngestionExecutor",
    "IngestionBatch",
    "IngestionResult",
    "IngestionSourceType",
    "get_ingestion_executor",
    "IndexingExecutor",
    "IndexingResult",
    "get_indexing_executor",
    "ClassificationExecutor",
    "ClassificationResult",
    "SensitivityLevel",
    "PIIType",
    "PIIDetection",
    "get_classification_executor",
    "reset_executors",
]

