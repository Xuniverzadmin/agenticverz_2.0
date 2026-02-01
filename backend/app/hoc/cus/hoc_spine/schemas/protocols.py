# Layer: L4 — HOC Spine (Schemas)
# AUDIENCE: INTERNAL
# Role: Protocol interfaces for L1 re-wiring — dependency inversion contracts
# Reference: PIN-513 Phase 3
# artifact_class: CODE

"""
L1 Re-wiring Protocol Interfaces (PIN-513)

These Protocols define the behavioral contracts that L4 hoc_spine uses
to interact with L5 domain engines WITHOUT direct cross-domain imports.

Each Protocol is implemented by the target L5 engine and injected via
constructor or bridge at L4 wiring time.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class LessonsEnginePort(Protocol):
    """Behavioral contract for lessons learned engine.

    Implemented by: LessonsLearnedEngine (policies/L5_engines)
    Consumed by: RunGovernanceFacade (L4)
    Wired by: L4 orchestrator context
    """

    def emit_near_threshold(
        self,
        tenant_id: str,
        metric: str,
        utilization: float,
        threshold_value: float,
        current_value: float,
        source_event_id: UUID,
        window: str = "24h",
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[UUID]: ...

    def emit_critical_success(
        self,
        tenant_id: str,
        success_type: str,
        metrics: Dict[str, Any],
        source_event_id: UUID,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[UUID]: ...


@runtime_checkable
class PolicyEvaluationPort(Protocol):
    """Behavioral contract for policy evaluation service.

    Implemented by: create_policy_evaluation_sync (incidents/L5_engines)
    Consumed by: RunGovernanceFacade (L4)
    Wired by: L4 orchestrator context
    """

    def __call__(
        self,
        run_id: str,
        tenant_id: str,
        run_status: str,
        policies_checked: int = 0,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[str]: ...


@runtime_checkable
class TraceFacadePort(Protocol):
    """Behavioral contract for trace facade.

    Implemented by: TraceFacade (logs/L5_engines)
    Consumed by: TransactionCoordinator (L4)
    Wired by: L4 orchestrator context
    """

    def complete_trace_sync(
        self,
        run_id: str,
        trace_id: str,
        run_status: str,
    ) -> bool: ...


@runtime_checkable
class ConnectorLookupPort(Protocol):
    """Behavioral contract for connector registry lookup.

    Implemented by: ConnectorRegistry (integrations/L6_drivers)
    Consumed by: DataIngestionExecutor, IndexingExecutor (L4)
    Wired by: L4 orchestrator execution context
    """

    def get_connector(
        self,
        connector_id: str,
        tenant_id: str,
    ) -> Optional[Any]: ...


@runtime_checkable
class ValidatorVerdictPort(Protocol):
    """Behavioral contract for CRM validator verdict type.

    Implemented by: ValidatorVerdict (account/L5_engines)
    Consumed by: ContractEngine (L4)
    Wired by: Caller passes typed object
    """

    @property
    def issue_type(self) -> Any: ...

    @property
    def severity(self) -> Any: ...

    @property
    def affected_capabilities(self) -> Any: ...

    @property
    def recommended_action(self) -> Any: ...

    @property
    def confidence_score(self) -> float: ...

    @property
    def reason(self) -> str: ...

    @property
    def analyzed_at(self) -> Any: ...


@runtime_checkable
class EligibilityVerdictPort(Protocol):
    """Behavioral contract for eligibility verdict type.

    Implemented by: EligibilityVerdict (policies/L5_engines)
    Consumed by: ContractEngine (L4)
    Wired by: Caller passes typed object
    """

    @property
    def decision(self) -> Any: ...

    @property
    def reason(self) -> str: ...

    @property
    def decided_at(self) -> Any: ...

    @property
    def rule_results(self) -> Any: ...


__all__ = [
    "LessonsEnginePort",
    "PolicyEvaluationPort",
    "TraceFacadePort",
    "ConnectorLookupPort",
    "ValidatorVerdictPort",
    "EligibilityVerdictPort",
]
