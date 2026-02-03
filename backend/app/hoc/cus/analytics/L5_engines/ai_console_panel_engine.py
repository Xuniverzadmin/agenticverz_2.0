# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (via L6 drivers)
#   Writes: none
# Role: Main orchestration engine for panel evaluation
# Callers: L2 APIs (ai-console)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, L2_1_PANEL_ADAPTER_SPEC.yaml


"""
AI Console Panel Engine — Main orchestration for panel evaluation

Orchestrates the complete panel evaluation pipeline:
1. Load spec → resolve dependencies → collect signals
2. Verify inputs → evaluate slots → check consistency
3. Assemble response → emit metrics

This is Option A: Spec Interpreter pattern.
"""

import logging
import time
from typing import Any, Dict, List, Optional

# Panel modules in app/hoc/int/agent/ (wired via absolute imports)
from app.hoc.int.agent.drivers.panel_consistency_checker import (
    PanelConsistencyChecker,
    create_consistency_checker,
)
from app.hoc.int.agent.drivers.panel_types import (
    PanelSlotResult,
    SlotState,
    VerificationSignals,
)
from app.hoc.int.agent.engines.panel_dependency_resolver import PanelDependencyResolver
from app.hoc.int.agent.engines.panel_metrics_emitter import (
    PanelMetricsEmitter,
    get_panel_metrics_emitter,
)
from app.hoc.int.agent.engines.panel_response_assembler import (
    PanelResponseAssembler,
    create_response_assembler,
)
from app.hoc.int.agent.engines.panel_signal_collector import (
    PanelSignalCollector,
    create_signal_collector,
)
from app.hoc.int.agent.engines.panel_slot_evaluator import PanelSlotEvaluator
from app.hoc.int.agent.engines.panel_spec_loader import (
    PanelSpecLoader,
    get_panel_spec_loader,
)
from app.hoc.int.agent.engines.panel_verification_engine import PanelVerificationEngine

logger = logging.getLogger("nova.panel_adapter.engine")


class AIConsolePanelEngine:
    """
    Main orchestration engine for AI Console panel evaluation.

    Usage:
        engine = AIConsolePanelEngine()
        response = await engine.evaluate_panel("OVR-SUM-HL", params)
    """

    def __init__(
        self,
        spec_loader: Optional[PanelSpecLoader] = None,
        signal_collector: Optional[PanelSignalCollector] = None,
        metrics_emitter: Optional[PanelMetricsEmitter] = None,
        api_base_url: Optional[str] = None,
    ):
        # Load spec
        self.spec_loader = spec_loader or get_panel_spec_loader()
        self.spec = self.spec_loader.load()

        # Initialize components
        self.signal_collector = signal_collector or create_signal_collector(api_base_url)
        self.verification_engine = PanelVerificationEngine()
        self.slot_evaluator = PanelSlotEvaluator(self.spec["adapter_version"])
        self.consistency_checker = create_consistency_checker(
            self.spec.get("consistency_rules")
        )
        self.response_assembler = create_response_assembler(
            adapter_version=self.spec["adapter_version"],
            schema_version=self.spec["schema_version"],
        )
        self.dependency_resolver = PanelDependencyResolver(self.spec["dependencies"])
        self.metrics = metrics_emitter or get_panel_metrics_emitter()

        logger.info(
            f"AIConsolePanelEngine initialized: "
            f"version={self.spec['adapter_version']}, "
            f"panels={len(self.spec['panels'])}"
        )

    async def evaluate_panel(
        self,
        panel_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a panel and return spec-compliant response.

        Args:
            panel_id: The panel ID to evaluate (e.g., "OVR-SUM-HL")
            params: Optional parameters (tenant_id, project_id, time_range, etc.)

        Returns:
            Spec-compliant panel response envelope
        """
        start_time = time.perf_counter()
        params = params or {}

        try:
            with self.metrics.measure_evaluation(panel_id):
                # 1. Get panel spec
                panel_spec = self.spec["panels"].get(panel_id)
                if not panel_spec:
                    return self.response_assembler.assemble_error(
                        panel_id=panel_id,
                        error=f"Panel not found: {panel_id}",
                        request_params=params,
                    )

                # 2. Resolve dependencies and get evaluation order
                eval_order = self.dependency_resolver.resolve_order(panel_id)
                logger.debug(f"Evaluation order for {panel_id}: {eval_order}")

                # 3. Evaluate upstream panels first (if any)
                upstream_results: Dict[str, List[PanelSlotResult]] = {}
                for upstream_id in eval_order[:-1]:  # All except last (target)
                    upstream_spec = self.spec["panels"].get(upstream_id)
                    if upstream_spec:
                        upstream_results[upstream_id] = await self._evaluate_panel_slots(
                            upstream_spec, params
                        )

                # 4. Check if we can short-circuit
                if self.dependency_resolver.can_short_circuit(panel_id):
                    for upstream_id, results in upstream_results.items():
                        if any(r.truth_metadata.state == SlotState.MISSING for r in results):
                            logger.info(
                                f"Short-circuiting {panel_id}: "
                                f"upstream {upstream_id} has MISSING state"
                            )
                            return self._create_short_circuit_response(
                                panel_id, panel_spec, upstream_id, params, start_time
                            )

                # 5. Evaluate target panel slots
                slot_results = await self._evaluate_panel_slots(panel_spec, params)

                # 6. Check consistency across slots
                consistency = self.consistency_checker.check(panel_id, slot_results)

                # 7. Record metrics
                self.metrics.record_evaluation_complete(panel_id, slot_results, consistency)

                # 8. Assemble response
                evaluation_time_ms = (time.perf_counter() - start_time) * 1000
                return self.response_assembler.assemble(
                    panel_id=panel_id,
                    panel_contract_id=panel_spec.panel_contract_id,
                    slot_results=slot_results,
                    consistency=consistency,
                    evaluation_time_ms=evaluation_time_ms,
                    request_params=params,
                )

        except Exception as e:
            logger.error(f"Panel evaluation failed: {panel_id}: {e}", exc_info=True)
            self.metrics.record_error(panel_id, type(e).__name__)
            return self.response_assembler.assemble_error(
                panel_id=panel_id,
                error=str(e),
                request_params=params,
            )

    async def _evaluate_panel_slots(
        self,
        panel_spec,
        params: Dict[str, Any],
    ) -> List[PanelSlotResult]:
        """Evaluate all slots in a panel."""
        results: List[PanelSlotResult] = []

        for slot_id, slot_spec in panel_spec.slots.items():
            try:
                # Collect signals for this slot
                collected = await self.signal_collector.collect_for_slot(slot_spec, params)

                if collected.errors:
                    # API errors → missing state
                    logger.warning(
                        f"Slot {slot_id} has API errors: {collected.errors}"
                    )
                    result = self.slot_evaluator.evaluate_missing(
                        slot_spec, f"API errors: {collected.errors}"
                    )
                else:
                    # Verify inputs
                    verification = self.verification_engine.verify_inputs(
                        slot_spec.required_inputs,
                        collected.signals,
                    )

                    # Determine state and authority
                    state = self.verification_engine.determine_state(verification)
                    authority, negative_value = self.verification_engine.determine_authority(
                        verification,
                        collected.signals,
                    )

                    # Check determinism rule if available
                    det_rule = self.spec["determinism_rules"].get(slot_id)
                    if det_rule:
                        violations = self.verification_engine.check_determinism_rule(
                            det_rule, verification, state, authority
                        )
                        if violations:
                            logger.error(
                                f"Determinism violations in {slot_id}: {violations}"
                            )
                            # Determinism violation → error state
                            result = self.slot_evaluator.evaluate_missing(
                                slot_spec, f"Determinism violation: {violations}"
                            )
                            results.append(result)
                            continue

                    # Evaluate slot
                    result = self.slot_evaluator.evaluate(
                        slot_spec=slot_spec,
                        signals=collected.signals,
                        verification=verification,
                        state=state,
                        authority=authority,
                        negative_value=negative_value,
                    )

                results.append(result)

            except Exception as e:
                logger.error(f"Slot evaluation failed: {slot_id}: {e}", exc_info=True)
                result = self.slot_evaluator.evaluate_missing(slot_spec, str(e))
                results.append(result)

        return results

    def _create_short_circuit_response(
        self,
        panel_id: str,
        panel_spec,
        blocking_upstream: str,
        params: Dict[str, Any],
        start_time: float,
    ) -> Dict[str, Any]:
        """Create response when short-circuiting due to upstream failure."""
        # Create missing results for all slots
        slot_results = [
            self.slot_evaluator.evaluate_missing(
                slot_spec,
                f"Short-circuited: upstream panel {blocking_upstream} unavailable"
            )
            for slot_spec in panel_spec.slots.values()
        ]

        # Empty consistency (no real evaluation)
        consistency = self.consistency_checker.check(panel_id, slot_results)

        evaluation_time_ms = (time.perf_counter() - start_time) * 1000
        return self.response_assembler.assemble(
            panel_id=panel_id,
            panel_contract_id=panel_spec.panel_contract_id,
            slot_results=slot_results,
            consistency=consistency,
            evaluation_time_ms=evaluation_time_ms,
            request_params=params,
        )

    async def evaluate_all_panels(
        self,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evaluate all panels in dependency order.

        Returns dict of panel_id -> response.
        """
        params = params or {}
        results: Dict[str, Dict[str, Any]] = {}

        # Get evaluation tiers
        tiers = self.dependency_resolver.get_all_tiers()

        for tier in tiers:
            # Panels in same tier can be evaluated in parallel
            # For simplicity, we evaluate sequentially here
            for panel_id in tier:
                results[panel_id] = await self.evaluate_panel(panel_id, params)

        return results

    async def get_panel_ids(self) -> List[str]:
        """Get all registered panel IDs."""
        return list(self.spec["panels"].keys())

    async def get_panel_spec(self, panel_id: str) -> Optional[Dict[str, Any]]:
        """Get spec for a specific panel."""
        panel = self.spec["panels"].get(panel_id)
        if not panel:
            return None

        return {
            "panel_id": panel.panel_id,
            "panel_contract_id": panel.panel_contract_id,
            "domain": panel.domain,
            "subdomain": panel.subdomain,
            "topic": panel.topic,
            "description": panel.description,
            "slot_count": len(panel.slots),
            "slots": list(panel.slots.keys()),
        }

    async def close(self):
        """Clean up resources."""
        await self.signal_collector.close()


# Factory
async def create_panel_engine(
    api_base_url: Optional[str] = None,
) -> AIConsolePanelEngine:
    """Create and initialize panel engine."""
    return AIConsolePanelEngine(api_base_url=api_base_url)


# Singleton
_engine: Optional[AIConsolePanelEngine] = None


async def get_panel_engine() -> AIConsolePanelEngine:
    """Get singleton panel engine."""
    global _engine
    if _engine is None:
        _engine = await create_panel_engine()
    return _engine
