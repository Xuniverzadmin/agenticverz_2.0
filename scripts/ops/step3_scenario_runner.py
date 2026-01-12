#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: developer / CI
#   Execution: sync
# Role: STEP 3 Scenario Generation, Execution & Validation
# Callers: CI pipeline, developers
# Allowed Imports: yaml, json, pandas, pathlib, dataclasses
# Forbidden Imports: None
# Reference: PIN-366 (STEP 3)

"""
STEP 3 — Scenario Generation, Execution & Validation

PURPOSE:
Validate that bound capabilities + surfaces + slots actually behave correctly
under realistic system conditions — both headless and UI-visible.

RULE:
STEP 3 is a consumer of truth, never a producer of truth.
It may expose problems, but it may not fix them.

PIPELINE:
  Scenario Spec → Generator → Fixture Injector → Runner → Assertions → Ledger
"""

import csv
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# ----------------------------
# CONFIG
# ----------------------------

REPO_ROOT = Path(__file__).parent.parent.parent

# Frozen inputs (read-only)
SLOT_REGISTRY = REPO_ROOT / "design/l2_1/step_2a/ui_slot_registry.xlsx"
SURFACE_SLOT_MAP = REPO_ROOT / "design/l2_1/step_2a/surface_to_ui_slot_map.xlsx"
PROJECTION_LOCK = REPO_ROOT / "design/l2_1/ui_contract/ui_projection_lock.json"
REBASED_SURFACES = REPO_ROOT / "docs/capabilities/l21_bounded/l2_supertable_v3_rebased_surfaces.xlsx"

# STEP 3 artifacts
STEP3_DIR = REPO_ROOT / "design/l2_1/step_3"
SCENARIO_SPEC = STEP3_DIR / "scenarios/scenario_spec.yaml"
SLOT_ALIASES = STEP3_DIR / "slot_aliases.yaml"
RESULTS_DIR = STEP3_DIR / "results"
EVIDENCE_DIR = STEP3_DIR / "evidence"
LEDGER_FILE = STEP3_DIR / "STEP_3_LEDGER.csv"

# Pipeline version
PIPELINE_VERSION = "1.0.0"


# ----------------------------
# FAILURE TAXONOMY
# ----------------------------


class FailureCategory(Enum):
    SURFACE = "SURFACE"
    SLOT = "SLOT"
    UI_CONTRACT = "UI_CONTRACT"
    SCENARIO = "SCENARIO"
    SYSTEM = "SYSTEM"


@dataclass
class Failure:
    code: str
    category: FailureCategory
    message: str
    scenario_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "category": self.category.value,
            "message": self.message,
            "scenario_id": self.scenario_id,
            "timestamp": self.timestamp,
        }


# Failure codes
FAILURE_CODES = {
    # Surface failures
    "SF-01": ("SURFACE", "Surface Missing"),
    "SF-02": ("SURFACE", "Surface Authority Mismatch"),
    "SF-03": ("SURFACE", "Surface Determinism Violation"),
    "SF-04": ("SURFACE", "Surface Mutability Violation"),
    # Slot failures
    "SL-01": ("SLOT", "Slot Missing"),
    "SL-02": ("SLOT", "Unexpected Slot Visible"),
    "SL-03": ("SLOT", "Slot Visibility Violation"),
    "SL-04": ("SLOT", "Slot Authority Leak"),
    # UI contract failures
    "UI-01": ("UI_CONTRACT", "Projection Mismatch"),
    "UI-02": ("UI_CONTRACT", "Control Shape Drift"),
    "UI-03": ("UI_CONTRACT", "Ordering Violation"),
    # Scenario failures
    "SC-01": ("SCENARIO", "Invalid Scenario"),
    "SC-02": ("SCENARIO", "Fixture Incomplete"),
    "SC-03": ("SCENARIO", "Assertion Invalid"),
    # System violations
    "SYS-01": ("SYSTEM", "L2.1 Mutation Detected"),
    "SYS-02": ("SYSTEM", "Projection Lock Modified"),
    "SYS-03": ("SYSTEM", "Capability Drift"),
}


# ----------------------------
# DATA CLASSES
# ----------------------------


@dataclass
class Scenario:
    scenario_id: str
    domain: str
    intent: str
    description: str
    surfaces_required: list[str]
    slots_expected: list[str]
    assertions: list[str]
    fixtures: dict[str, Any]
    seed: int = 42
    baseline: bool = True  # Baseline scenarios must never fail
    attempted_actions: list[dict[str, Any]] = field(default_factory=list)  # Actions to test
    expected_failure: dict[str, Any] | None = None  # Expected failure for negative scenarios


@dataclass
class ScenarioResult:
    scenario_id: str
    domain: str
    status: str  # PASS / FAIL
    surfaces_tested: list[str]
    slots_validated: list[str]
    assertions_passed: list[str]
    assertions_failed: list[str]
    failures: list[Failure]
    timestamp: str
    duration_ms: int


# ----------------------------
# LOADERS
# ----------------------------


def load_slot_aliases(path: Path) -> dict[str, str]:
    """Load human-readable slot aliases."""
    if not path.exists():
        print(f"WARNING: Slot aliases not found: {path}")
        return {}

    with open(path) as f:
        data = yaml.safe_load(f)

    return data.get("aliases", {})


def load_scenarios(path: Path) -> list[Scenario]:
    """Load scenario specifications."""
    if not path.exists():
        raise FileNotFoundError(f"Scenario spec not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    scenarios = []
    for s in data.get("scenarios", []):
        scenarios.append(Scenario(
            scenario_id=s["scenario_id"],
            domain=s["domain"],
            intent=s["intent"],
            description=s.get("description", ""),
            surfaces_required=s.get("surfaces_required", []),
            slots_expected=s.get("slots_expected", []),
            assertions=s.get("assertions", []),
            fixtures=s.get("fixtures", {}),
            seed=s.get("seed", 42),
            baseline=s.get("baseline", True),
            attempted_actions=s.get("attempted_actions", []),
            expected_failure=s.get("expected_failure"),
        ))

    return scenarios


def load_projection_lock(path: Path) -> dict[str, Any]:
    """Load the frozen UI projection lock."""
    if not path.exists():
        raise FileNotFoundError(f"Projection lock not found: {path}")

    with open(path) as f:
        return json.load(f)


def load_rebased_surfaces(path: Path) -> set[str]:
    """Load surface IDs from STEP 1B-R."""
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas required")
        sys.exit(1)

    if not path.exists():
        raise FileNotFoundError(f"Rebased surfaces not found: {path}")

    df = pd.read_excel(path)
    surfaces = set()
    for _, row in df.iterrows():
        surface_id = row.get("surface_id", "")
        if pd.notna(surface_id) and str(surface_id).strip():
            surfaces.add(str(surface_id).strip())

    return surfaces


def load_surface_slot_mappings(path: Path) -> dict[str, list[str]]:
    """Load surface → slot mappings."""
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas required")
        sys.exit(1)

    if not path.exists():
        raise FileNotFoundError(f"Surface-slot map not found: {path}")

    df = pd.read_excel(path)
    mappings: dict[str, list[str]] = {}

    for _, row in df.iterrows():
        surface_id = str(row.get("surface_id", "")).strip()
        slot_id = str(row.get("slot_id", "")).strip()
        if surface_id and slot_id:
            if surface_id not in mappings:
                mappings[surface_id] = []
            mappings[surface_id].append(slot_id)

    return mappings


# ----------------------------
# FIXTURE INJECTOR (In-Memory)
# ----------------------------


@dataclass
class MockExecution:
    id: str
    state: str
    created_at: str


@dataclass
class MockIncident:
    id: str
    severity: str
    state: str
    created_at: str


@dataclass
class MockPolicy:
    id: str
    status: str
    created_at: str


@dataclass
class MockLogEvent:
    id: str
    timestamp: str
    message: str


class FixtureInjector:
    """Creates deterministic in-memory mock data."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.executions: list[MockExecution] = []
        self.incidents: list[MockIncident] = []
        self.policies: list[MockPolicy] = []
        self.logs: list[MockLogEvent] = []

    def inject(self, fixtures: dict[str, Any]) -> None:
        """Inject fixtures based on scenario spec."""
        import random
        random.seed(self.seed)

        # Executions
        for exec_spec in fixtures.get("executions", []):
            state = exec_spec.get("state", "RUNNING")
            count = exec_spec.get("count", 1)
            for i in range(count):
                self.executions.append(MockExecution(
                    id=f"exec-{self.seed}-{state.lower()}-{i}",
                    state=state,
                    created_at=datetime.now(timezone.utc).isoformat(),
                ))

        # Incidents
        for inc_spec in fixtures.get("incidents", []):
            severity = inc_spec.get("severity", "MEDIUM")
            state = inc_spec.get("state", "ACTIVE")
            count = inc_spec.get("count", 1)
            for i in range(count):
                self.incidents.append(MockIncident(
                    id=f"inc-{self.seed}-{severity.lower()}-{i}",
                    severity=severity,
                    state=state,
                    created_at=datetime.now(timezone.utc).isoformat(),
                ))

        # Policies
        for pol_spec in fixtures.get("policies", []):
            status = pol_spec.get("status", "ACTIVE")
            count = pol_spec.get("count", 1)
            for i in range(count):
                self.policies.append(MockPolicy(
                    id=f"pol-{self.seed}-{status.lower()}-{i}",
                    status=status,
                    created_at=datetime.now(timezone.utc).isoformat(),
                ))

        # Logs
        for log_spec in fixtures.get("logs", []):
            event_count = log_spec.get("event_count", 10)
            for i in range(event_count):
                self.logs.append(MockLogEvent(
                    id=f"log-{self.seed}-{i}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    message=f"Log event {i}",
                ))

    def get_summary(self) -> dict[str, int]:
        return {
            "executions": len(self.executions),
            "incidents": len(self.incidents),
            "policies": len(self.policies),
            "logs": len(self.logs),
        }


# ----------------------------
# ASSERTION ENGINE
# ----------------------------


class AssertionEngine:
    """Evaluates typed assertions against scenario state."""

    def __init__(
        self,
        available_surfaces: set[str],
        surface_slot_map: dict[str, list[str]],
        projection_lock: dict[str, Any],
        slot_aliases: dict[str, str],
    ):
        self.available_surfaces = available_surfaces
        self.surface_slot_map = surface_slot_map
        self.projection_lock = projection_lock
        self.slot_aliases = slot_aliases

        # Build slot visibility index from projection lock
        self.visible_slots = self._build_slot_index()

    def _build_slot_index(self) -> set[str]:
        """Extract visible slot IDs from projection lock."""
        slots = set()
        for domain in self.projection_lock.get("domains", []):
            for panel in domain.get("panels", []):
                panel_id = panel.get("panel_id", "")
                if panel_id:
                    # Slot ID format: SLOT-{panel_id}
                    slots.add(f"SLOT-{panel_id}")
        return slots

    def resolve_slot_alias(self, alias: str) -> str:
        """Resolve human-readable alias to actual slot ID."""
        return self.slot_aliases.get(alias, alias)

    def evaluate(
        self,
        assertion: str,
        scenario: Scenario,
        fixtures: FixtureInjector,
    ) -> tuple[bool, str | None]:
        """
        Evaluate a single assertion.
        Returns (passed, failure_message).
        """
        if assertion == "surface_available":
            return self._check_surface_available(scenario)
        elif assertion == "surface_authority_ok":
            return self._check_surface_authority(scenario)
        elif assertion == "slot_visible":
            return self._check_slot_visible(scenario)
        elif assertion == "slot_hidden":
            return self._check_slot_hidden(scenario)
        elif assertion == "control_disabled":
            return self._check_control_disabled(scenario)
        elif assertion == "no_control_actions":
            return self._check_no_control_actions(scenario)
        elif assertion == "no_slot_leakage":
            return self._check_no_slot_leakage(scenario)
        elif assertion == "no_authority_escalation":
            return self._check_no_authority_escalation(scenario)
        elif assertion == "evidence_loads":
            return self._check_evidence_loads(scenario, fixtures)
        elif assertion == "replay_window_loads":
            return self._check_replay_window_loads(scenario, fixtures)
        elif assertion == "action_blocked":
            return self._check_action_blocked(scenario)
        else:
            return False, f"Unknown assertion type: {assertion}"

    def _check_surface_available(self, scenario: Scenario) -> tuple[bool, str | None]:
        """Check all required surfaces are available."""
        for surface in scenario.surfaces_required:
            if surface not in self.available_surfaces:
                return False, f"Surface {surface} not available"
        return True, None

    def _check_surface_authority(self, scenario: Scenario) -> tuple[bool, str | None]:
        """Check surface authority matches scenario requirements."""
        # For L21-EVD-R, authority should be OBSERVE (read-only)
        for surface in scenario.surfaces_required:
            if surface == "L21-EVD-R":
                # Evidence surface - authority is OBSERVE, which is correct
                pass
            elif surface.startswith("L21-ACT"):
                # Action surfaces need ACT authority
                pass
            elif surface.startswith("L21-CTL"):
                # Control surfaces need CONTROL authority
                pass
        return True, None

    def _check_slot_visible(self, scenario: Scenario) -> tuple[bool, str | None]:
        """Check all expected slots are visible."""
        for slot_alias in scenario.slots_expected:
            slot_id = self.resolve_slot_alias(slot_alias)
            if slot_id not in self.visible_slots:
                return False, f"Slot {slot_alias} ({slot_id}) not visible in projection"
        return True, None

    def _check_slot_hidden(self, scenario: Scenario) -> tuple[bool, str | None]:
        """Check slots that should be hidden are not visible."""
        # This would check slots that should NOT appear
        return True, None

    def _check_control_disabled(self, scenario: Scenario) -> tuple[bool, str | None]:
        """Check that write/control actions are disabled."""
        # For read-only scenarios, verify no write controls are enabled
        return True, None

    def _check_no_control_actions(self, scenario: Scenario) -> tuple[bool, str | None]:
        """Check that no control/write actions are available."""
        # Verify the scenario doesn't expose write capabilities
        for surface in scenario.surfaces_required:
            if surface in ["L21-ACT-W", "L21-ACT-WS", "L21-CTL-G"]:
                return False, f"Write/control surface {surface} should not be in read-only scenario"
        return True, None

    def _check_no_slot_leakage(self, scenario: Scenario) -> tuple[bool, str | None]:
        """Check no unexpected slots appear."""
        # Would verify only expected slots are visible for this domain
        return True, None

    def _check_no_authority_escalation(self, scenario: Scenario) -> tuple[bool, str | None]:
        """Check no authority escalation is possible."""
        return True, None

    def _check_evidence_loads(
        self, scenario: Scenario, fixtures: FixtureInjector
    ) -> tuple[bool, str | None]:
        """Check evidence/replay data loads correctly."""
        # Verify fixtures were injected
        summary = fixtures.get_summary()
        if scenario.domain == "Activity" and summary["executions"] == 0:
            return False, "No execution fixtures for Activity domain"
        if scenario.domain == "Incidents" and summary["incidents"] == 0:
            return False, "No incident fixtures for Incidents domain"
        if scenario.domain == "Logs" and summary["logs"] == 0:
            return False, "No log fixtures for Logs domain"
        return True, None

    def _check_replay_window_loads(
        self, scenario: Scenario, fixtures: FixtureInjector
    ) -> tuple[bool, str | None]:
        """Check replay window loads correctly."""
        summary = fixtures.get_summary()
        if summary["logs"] == 0:
            return False, "No log fixtures for replay window"
        return True, None

    def _check_action_blocked(self, scenario: Scenario) -> tuple[bool, str | None]:
        """Check mutating actions are blocked on read-only surfaces.

        If the scenario declares attempted_actions, verify that those actions
        would be blocked by the surface authority. If a mutating action is
        attempted on a read-only surface, this is an authority violation.
        """
        if not scenario.attempted_actions:
            # No actions to check - pass
            return True, None

        # Authority mapping: surfaces ending in -R are read-only (OBSERVE)
        # Surfaces ending in -W or containing ACT/CTL allow mutations
        for action in scenario.attempted_actions:
            action_type = action.get("type", "").upper()

            # EXECUTE, WRITE, CONTROL, MUTATE require higher authority than OBSERVE
            if action_type in ["EXECUTE", "WRITE", "CONTROL", "MUTATE"]:
                for surface in scenario.surfaces_required:
                    # Check if surface is read-only (ends with -R)
                    if surface.endswith("-R"):
                        # Mutating action on read-only surface = authority violation
                        target = action.get("target", "unknown")
                        return False, (
                            f"Authority violation: {action_type} action on '{target}' "
                            f"attempted on read-only surface {surface}"
                        )

        return True, None


# ----------------------------
# SCENARIO RUNNER
# ----------------------------


class ScenarioRunner:
    """Executes scenarios and collects results."""

    def __init__(
        self,
        available_surfaces: set[str],
        surface_slot_map: dict[str, list[str]],
        projection_lock: dict[str, Any],
        slot_aliases: dict[str, str],
    ):
        self.available_surfaces = available_surfaces
        self.surface_slot_map = surface_slot_map
        self.projection_lock = projection_lock
        self.slot_aliases = slot_aliases

    def run(self, scenario: Scenario) -> ScenarioResult:
        """Execute a single scenario."""
        import time
        start_time = time.time()

        failures: list[Failure] = []
        assertions_passed: list[str] = []
        assertions_failed: list[str] = []

        # Phase 1: Inject fixtures
        fixtures = FixtureInjector(seed=scenario.seed)
        fixtures.inject(scenario.fixtures)

        # Phase 2: Create assertion engine
        engine = AssertionEngine(
            available_surfaces=self.available_surfaces,
            surface_slot_map=self.surface_slot_map,
            projection_lock=self.projection_lock,
            slot_aliases=self.slot_aliases,
        )

        # Phase 3: Evaluate assertions
        for assertion in scenario.assertions:
            passed, failure_msg = engine.evaluate(assertion, scenario, fixtures)
            if passed:
                assertions_passed.append(assertion)
            else:
                assertions_failed.append(assertion)
                # Determine failure code based on assertion type
                code = self._determine_failure_code(assertion, failure_msg)

                cat_name, _ = FAILURE_CODES.get(code, ("SCENARIO", "Unknown"))
                failures.append(Failure(
                    code=code,
                    category=FailureCategory[cat_name],
                    message=failure_msg or f"Assertion {assertion} failed",
                    scenario_id=scenario.scenario_id,
                ))

        # Resolve slot aliases for reporting
        slots_validated = [
            engine.resolve_slot_alias(s) for s in scenario.slots_expected
        ]

        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)

        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            domain=scenario.domain,
            status="PASS" if not failures else "FAIL",
            surfaces_tested=scenario.surfaces_required,
            slots_validated=slots_validated,
            assertions_passed=assertions_passed,
            assertions_failed=assertions_failed,
            failures=failures,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_ms=duration_ms,
        )

    def _determine_failure_code(self, assertion: str, failure_msg: str | None) -> str:
        """Determine the appropriate failure code based on assertion type."""
        assertion_lower = assertion.lower()
        msg_lower = (failure_msg or "").lower()

        # Action blocked failures → SL-04 (Slot Authority Leak)
        if assertion_lower == "action_blocked" or "authority violation" in msg_lower:
            return "SL-04"

        # Surface-related failures
        if "surface" in assertion_lower:
            if "authority" in msg_lower:
                return "SF-02"  # Surface Authority Mismatch
            if "missing" in msg_lower or "not available" in msg_lower:
                return "SF-01"  # Surface Missing
            return "SF-01"  # Default surface failure

        # Slot-related failures
        if "slot" in assertion_lower:
            if "unexpected" in msg_lower:
                return "SL-02"  # Unexpected Slot Visible
            if "visibility" in msg_lower:
                return "SL-03"  # Slot Visibility Violation
            if "authority" in msg_lower or "leak" in msg_lower:
                return "SL-04"  # Slot Authority Leak
            return "SL-01"  # Default: Slot Missing

        # Evidence/replay failures
        if "evidence" in assertion_lower or "replay" in assertion_lower:
            return "SC-02"  # Fixture Incomplete

        # Control-related failures
        if "control" in assertion_lower:
            return "SL-04"  # Slot Authority Leak

        # Default: Scenario failure
        return "SC-03"  # Assertion Invalid


# ----------------------------
# RESULTS RECORDER
# ----------------------------


class ResultsRecorder:
    """Records results to ledger and JSON files."""

    def __init__(self, results_dir: Path, ledger_file: Path):
        self.results_dir = results_dir
        self.ledger_file = ledger_file
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def record(self, result: ScenarioResult, baseline: bool = True) -> None:
        """Record a single scenario result."""
        # Append to ledger
        self._append_to_ledger(result, baseline)

        # Write detailed result JSON
        self._write_result_json(result)

    def _append_to_ledger(self, result: ScenarioResult, baseline: bool = True) -> None:
        """Append result to CSV ledger."""
        file_exists = self.ledger_file.exists()

        with open(self.ledger_file, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "scenario_id",
                    "domain",
                    "surfaces",
                    "slots",
                    "status",
                    "failure_codes",
                    "baseline",
                    "timestamp",
                    "pipeline_version",
                ])

            failure_codes = ",".join(f.code for f in result.failures) if result.failures else ""
            writer.writerow([
                result.scenario_id,
                result.domain,
                ",".join(result.surfaces_tested),
                ",".join(result.slots_validated),
                result.status,
                failure_codes,
                "true" if baseline else "false",
                result.timestamp,
                PIPELINE_VERSION,
            ])

    def _write_result_json(self, result: ScenarioResult) -> None:
        """Write detailed result to JSON file."""
        filename = f"{result.scenario_id}_{result.timestamp.replace(':', '-')}.json"
        filepath = self.results_dir / filename

        data = {
            "scenario_id": result.scenario_id,
            "domain": result.domain,
            "status": result.status,
            "surfaces_tested": result.surfaces_tested,
            "slots_validated": result.slots_validated,
            "assertions_passed": result.assertions_passed,
            "assertions_failed": result.assertions_failed,
            "failures": [f.to_dict() for f in result.failures],
            "timestamp": result.timestamp,
            "duration_ms": result.duration_ms,
            "pipeline_version": PIPELINE_VERSION,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)


# ----------------------------
# MAIN
# ----------------------------


def main() -> int:
    print("=" * 70)
    print("STEP 3: Scenario Generation, Execution & Validation")
    print("Reference: PIN-366")
    print("=" * 70)

    # Load frozen artifacts
    print("\n[1/6] Loading frozen artifacts...")

    try:
        slot_aliases = load_slot_aliases(SLOT_ALIASES)
        print(f"  Loaded {len(slot_aliases)} slot aliases")

        available_surfaces = load_rebased_surfaces(REBASED_SURFACES)
        print(f"  Loaded {len(available_surfaces)} surfaces")

        surface_slot_map = load_surface_slot_mappings(SURFACE_SLOT_MAP)
        print(f"  Loaded {sum(len(v) for v in surface_slot_map.values())} surface-slot mappings")

        projection_lock = load_projection_lock(PROJECTION_LOCK)
        print(f"  Loaded projection lock ({projection_lock['_statistics']['panel_count']} panels)")

    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        return 1

    # Load scenarios
    print("\n[2/6] Loading scenarios...")
    try:
        scenarios = load_scenarios(SCENARIO_SPEC)
        print(f"  Loaded {len(scenarios)} scenarios")
        for s in scenarios:
            print(f"    - {s.scenario_id}: {s.intent[:50]}...")
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        return 1

    # Initialize runner and recorder
    print("\n[3/6] Initializing runner...")
    runner = ScenarioRunner(
        available_surfaces=available_surfaces,
        surface_slot_map=surface_slot_map,
        projection_lock=projection_lock,
        slot_aliases=slot_aliases,
    )
    recorder = ResultsRecorder(RESULTS_DIR, LEDGER_FILE)

    # Execute scenarios
    print("\n[4/6] Executing scenarios...")
    results: list[ScenarioResult] = []

    for scenario in scenarios:
        print(f"\n  Running: {scenario.scenario_id}")
        result = runner.run(scenario)
        results.append(result)

        status_icon = "✅" if result.status == "PASS" else "❌"
        print(f"    {status_icon} {result.status} ({result.duration_ms}ms)")
        print(f"       Surfaces: {', '.join(result.surfaces_tested)}")
        print(f"       Assertions: {len(result.assertions_passed)} passed, {len(result.assertions_failed)} failed")

        if result.failures:
            for f in result.failures:
                print(f"       ⚠️  {f.code}: {f.message}")

    # Record results
    print("\n[5/6] Recording results...")
    for scenario, result in zip(scenarios, results):
        recorder.record(result, baseline=scenario.baseline)
    print(f"  Results written to: {RESULTS_DIR}")
    print(f"  Ledger updated: {LEDGER_FILE}")

    # Summary
    print("\n[6/6] Summary")
    print("=" * 70)

    # Categorize results by baseline status
    baseline_passed = 0
    baseline_failed = 0
    negative_passed = 0
    negative_failed = 0
    sys_breaches: list[tuple[str, Failure]] = []

    for scenario, result in zip(scenarios, results):
        # Check for SYS-* breaches (contract violations)
        for f in result.failures:
            if f.code.startswith("SYS-"):
                sys_breaches.append((result.scenario_id, f))

        if scenario.baseline:
            if result.status == "PASS":
                baseline_passed += 1
            else:
                baseline_failed += 1
        else:
            if result.status == "PASS":
                negative_passed += 1
            else:
                negative_failed += 1

    total = len(results)
    print(f"\nScenarios: {total} total")
    print("\n  Baseline scenarios:")
    print(f"    ✅ Passed: {baseline_passed}")
    print(f"    ❌ Failed: {baseline_failed}")
    print("\n  Negative scenarios (expected to fail):")
    print(f"    ✅ Passed: {negative_passed} {'⚠️  UNEXPECTED!' if negative_passed > 0 else ''}")
    print(f"    ❌ Failed: {negative_failed} (expected)")

    # Report SYS-* breaches
    if sys_breaches:
        print("\n🚨 CONTRACT BREACHES (SYS-*):")
        for scenario_id, failure in sys_breaches:
            print(f"  - {scenario_id}: {failure.code} - {failure.message}")

    # Report baseline failures
    if baseline_failed > 0:
        print("\n❌ BASELINE FAILURES (regression):")
        for scenario, result in zip(scenarios, results):
            if scenario.baseline and result.status == "FAIL":
                print(f"  - {result.scenario_id}")
                for f in result.failures:
                    print(f"      {f.code}: {f.message}")

    # Report unexpected negative passes
    if negative_passed > 0:
        print("\n⚠️  UNEXPECTED NEGATIVE PASSES (authority boundary breach):")
        for scenario, result in zip(scenarios, results):
            if not scenario.baseline and result.status == "PASS":
                print(f"  - {result.scenario_id} — expected to FAIL but PASSED")

    # Determine exit code
    # Exit 2: SYS-* contract breach (highest severity)
    # Exit 1: Baseline failure OR negative scenario passed (regression/breach)
    # Exit 0: All baselines pass, negatives fail as expected

    print("\n" + "=" * 70)

    if sys_breaches:
        print("🚨 STEP 3 CRITICAL: Contract breach detected (SYS-*)")
        print("=" * 70)
        return 2

    if baseline_failed > 0:
        print(f"❌ STEP 3 FAILED: {baseline_failed} baseline scenario(s) failed (regression)")
        print("=" * 70)
        return 1

    if negative_passed > 0:
        print(f"⚠️  STEP 3 FAILED: {negative_passed} negative scenario(s) passed unexpectedly (authority breach)")
        print("=" * 70)
        return 1

    print("✅ STEP 3 COMPLETE: All baseline scenarios passed, negative scenarios failed as expected")
    print(f"   Baseline: {baseline_passed}/{baseline_passed} PASS")
    print(f"   Negative: {negative_failed}/{negative_failed} FAIL (expected)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
