# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Load and parse L2.1 Panel Adapter YAML spec
# Reference: L2_1_PANEL_ADAPTER_SPEC.yaml

"""
Panel Spec Loader — Load YAML specification for AI Console panels

Loads:
- L2_1_PANEL_ADAPTER_SPEC.yaml — panel definitions
- L2_1_PANEL_DEPENDENCY_GRAPH.yaml — evaluation order
- L2_1_SLOT_DETERMINISM_MATRIX.csv — determinism rules
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .panel_types import (
    APISpec,
    ConsumedCapabilitySpec,
    DependencySpec,
    DeterminismRule,
    InputSignalSpec,
    InputSignalsSpec,
    OutputSignalSpec,
    PanelSpec,
    SlotSpec,
    TruthClass,
    TruthLens,
)

logger = logging.getLogger("nova.panel_adapter.spec_loader")

# Spec paths
SPEC_BASE = Path(__file__).parent.parent.parent.parent.parent / "design" / "l2_1"
SPEC_FILE = SPEC_BASE / "L2_1_PANEL_ADAPTER_SPEC.yaml"
DEPENDENCY_FILE = SPEC_BASE / "L2_1_PANEL_DEPENDENCY_GRAPH.yaml"
DETERMINISM_FILE = SPEC_BASE / "L2_1_SLOT_DETERMINISM_MATRIX.csv"


class PanelSpecLoader:
    """
    Loads panel adapter specification from YAML.

    Usage:
        loader = PanelSpecLoader()
        spec = loader.load()
        panel = spec["panels"]["OVR-SUM-HL"]
    """

    def __init__(
        self,
        spec_path: Optional[Path] = None,
        dependency_path: Optional[Path] = None,
        determinism_path: Optional[Path] = None,
    ):
        self.spec_path = spec_path or SPEC_FILE
        self.dependency_path = dependency_path or DEPENDENCY_FILE
        self.determinism_path = determinism_path or DETERMINISM_FILE
        self._cache: Optional[dict] = None

    def load(self, force_reload: bool = False) -> dict:
        """Load complete spec. Returns cached if available."""
        if self._cache and not force_reload:
            return self._cache

        logger.info(f"Loading panel spec from {self.spec_path}")

        # Load YAML files
        spec_data = self._load_yaml(self.spec_path)
        dep_data = self._load_yaml(self.dependency_path)

        # Load CSV
        det_rules = self._load_determinism_csv()

        # Parse into typed structures
        panels = self._parse_panels(spec_data)
        dependencies = self._parse_dependencies(dep_data)
        evaluation_order = self._parse_evaluation_order(dep_data)

        self._cache = {
            "adapter_version": spec_data.get("adapter_metadata", {}).get("adapter_version", "1.0.0"),
            "schema_version": spec_data.get("adapter_metadata", {}).get("schema_version", "2026-01-16"),
            "panels": panels,
            "dependencies": dependencies,
            "evaluation_order": evaluation_order,
            "determinism_rules": det_rules,
            "negative_authority_values": spec_data.get("negative_authority_values", []),
            "consistency_rules": spec_data.get("cross_slot_consistency_rules", []),
            "loaded_at": datetime.utcnow(),
        }

        logger.info(f"Loaded {len(panels)} panels, {len(det_rules)} determinism rules")
        return self._cache

    def _load_yaml(self, path: Path) -> dict:
        """Load YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Spec file not found: {path}")
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _load_determinism_csv(self) -> Dict[str, DeterminismRule]:
        """Load determinism matrix from CSV."""
        rules = {}
        if not self.determinism_path.exists():
            logger.warning(f"Determinism matrix not found: {self.determinism_path}")
            return rules

        with open(self.determinism_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                slot_id = row.get("Slot_ID", "")
                if not slot_id:
                    continue
                rules[slot_id] = DeterminismRule(
                    slot_id=slot_id,
                    panel_id=row.get("Panel_ID", ""),
                    required_input=row.get("Required_Input", ""),
                    missing_effect_state=row.get("Missing_Input_Effect_State", ""),
                    missing_effect_authority=row.get("Missing_Input_Effect_Authority", ""),
                    stale_effect_state=row.get("Stale_Input_Effect_State", ""),
                    contradictory_rule=row.get("Contradictory_Signal_Rule", "N/A"),
                    expected_negative=row.get("Expected_Negative_Authority", "N/A"),
                    test_id=row.get("Determinism_Test_ID", ""),
                )
        return rules

    def _parse_panels(self, spec_data: dict) -> Dict[str, PanelSpec]:
        """Parse panel specifications."""
        panels = {}
        for panel_id, data in spec_data.get("panels", {}).items():
            slots = self._parse_slots(panel_id, data.get("slots", {}))
            panels[panel_id] = PanelSpec(
                panel_id=panel_id,
                panel_contract_id=data.get("panel_contract_id", f"{panel_id}-v1.0.0"),
                domain=data.get("domain", ""),
                subdomain=data.get("subdomain", ""),
                topic=data.get("topic", ""),
                description=data.get("description", ""),
                slots=slots,
            )
        return panels

    def _parse_slots(self, panel_id: str, slots_data: dict) -> Dict[str, SlotSpec]:
        """Parse slot specifications.

        V2.0: Now supports capability-bound model with consumed_capabilities.
        Falls back to consumed_apis for V1 compatibility.
        """
        slots = {}
        for slot_id, data in slots_data.items():
            # V2: Parse consumed_capabilities (capability-bound model)
            consumed_capabilities = [
                ConsumedCapabilitySpec(
                    capability_id=cap.get("capability_id", ""),
                    signals=cap.get("signals", []),
                    required=cap.get("required", True),
                )
                for cap in data.get("consumed_capabilities", [])
            ]

            # V1 legacy: Parse APIs (fallback for backward compatibility)
            apis = [
                APISpec(
                    path=api.get("path", ""),
                    method=api.get("method", "GET"),
                    domain=api.get("domain", ""),
                    signals_used=api.get("signals_used", []),
                )
                for api in data.get("consumed_apis", [])
            ]

            # V2: Parse input_signals structure
            input_signals_data = data.get("input_signals", {})
            input_signals_spec = InputSignalsSpec(
                raw=input_signals_data.get("raw", [])
            ) if input_signals_data else None

            # Parse required inputs from V2 input_signals or derive from consumed_capabilities
            # Note: raw signals conform to InputSignalSpec schema
            required: List[str] = []
            raw_signals: List[InputSignalSpec] = input_signals_spec.raw if input_signals_spec else []
            if raw_signals:
                required = [
                    sig.get("signal_id", "")
                    for sig in raw_signals
                    if sig.get("required", False) and sig.get("signal_id")
                ]
            elif consumed_capabilities:
                # Derive from capability signals if input_signals not specified
                for cap in consumed_capabilities:
                    if cap.required:
                        required.extend(cap.signals)

            # Parse output signals
            outputs = [
                OutputSignalSpec(
                    signal_id=sig.get("signal_id", ""),
                    type=sig.get("type", "string"),
                    customer_facing=sig.get("customer_facing", True),
                    deterministic=sig.get("deterministic", True),
                    values=sig.get("values"),
                )
                for sig in data.get("output_signals", {}).get("derived", [])
            ]

            # Truth metadata
            tm = data.get("truth_metadata", {})
            ts = data.get("time_semantics", {})

            # V2: Get capability_binding if single capability
            capability_binding = None
            if len(consumed_capabilities) == 1:
                capability_binding = consumed_capabilities[0].capability_id

            slots[slot_id] = SlotSpec(
                slot_id=slot_id,
                slot_contract_id=data.get("slot_contract_id", f"{panel_id}-{slot_id}-v1.0.0"),
                slot_question=data.get("slot_question", ""),
                truth_class=TruthClass(tm.get("class", "interpretation")),
                lens=TruthLens(tm.get("lens", "operational")),
                capability=tm.get("capability", ""),
                state_binding=data.get("state", "DRAFT"),
                apis=apis,
                required_inputs=required,
                output_signals=outputs,
                evaluation_window=ts.get("evaluation_window", "PT15M"),
                staleness_threshold=ts.get("staleness_threshold", "PT5M"),
                # V2 fields
                consumed_capabilities=consumed_capabilities,
                input_signals=input_signals_spec,
                capability_binding=capability_binding,
            )
        return slots

    def _parse_dependencies(self, dep_data: dict) -> Dict[str, DependencySpec]:
        """Parse panel dependencies."""
        deps = {}
        for panel_id, data in dep_data.get("dependencies", {}).items():
            depends_on = [d.get("panel_id", "") for d in data.get("depends_on", [])]
            deps[panel_id] = DependencySpec(
                panel_id=panel_id,
                depends_on=depends_on,
                evaluation_order=data.get("evaluation_order", 99),
                can_short_circuit=data.get("can_short_circuit", False),
            )
        return deps

    def _parse_evaluation_order(self, dep_data: dict) -> List[List[str]]:
        """Parse evaluation order tiers."""
        order = []
        eval_data = dep_data.get("evaluation_order", {})
        for tier in sorted(eval_data.keys()):
            panels = eval_data[tier].get("panels", [])
            order.append(panels)
        return order

    def get_panel(self, panel_id: str) -> Optional[PanelSpec]:
        """Get panel by ID."""
        spec = self.load()
        return spec["panels"].get(panel_id)

    def get_slot(self, panel_id: str, slot_id: str) -> Optional[SlotSpec]:
        """Get slot by panel and slot ID."""
        panel = self.get_panel(panel_id)
        return panel.slots.get(slot_id) if panel else None

    def get_determinism_rule(self, slot_id: str) -> Optional[DeterminismRule]:
        """Get determinism rule for slot."""
        spec = self.load()
        return spec["determinism_rules"].get(slot_id)


# Singleton
_loader: Optional[PanelSpecLoader] = None


def get_panel_spec_loader() -> PanelSpecLoader:
    """Get singleton spec loader."""
    global _loader
    if _loader is None:
        _loader = PanelSpecLoader()
    return _loader
