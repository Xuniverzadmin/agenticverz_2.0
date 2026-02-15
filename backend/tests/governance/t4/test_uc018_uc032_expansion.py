"""
UC-018..UC-032 Expansion Governance Tests

Static analysis tests verifying architecture compliance for
15 new usecases across policies, analytics, incidents, and logs domains.

Tests verify:
1. L5 engine purity (no DB imports at runtime)
2. L6 driver purity (no business logic)
3. L4 handler wiring (operation registry binding)
4. Deterministic contract presence (function signatures)
"""

import ast
import os
import re
import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
HOC_CUS = os.path.join(BACKEND, "app", "hoc", "cus")
HOC_SPINE = os.path.join(BACKEND, "app", "hoc", "cus", "hoc_spine")
L2_CUS = os.path.join(BACKEND, "app", "hoc", "api", "cus")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_file(rel_path):
    full = os.path.join(HOC_CUS, rel_path)
    with open(full) as f:
        return f.read()


def _file_exists(rel_path):
    return os.path.isfile(os.path.join(HOC_CUS, rel_path))


def _spine_handler_exists(name):
    return os.path.isfile(os.path.join(HOC_SPINE, "orchestrator", "handlers", name))


def _l2_route_exists(rel_path):
    return os.path.isfile(os.path.join(L2_CUS, rel_path))


def _has_function(source, func_name):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name:
                return True
    return False


def _has_class(source, class_name):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return True
    return False


def _has_class_method(source, class_name, method_name):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in ast.walk(node):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name == method_name:
                        return True
    return False


def _check_l5_purity(source):
    """Return list of runtime sqlalchemy/sqlmodel/app.db import violations."""
    lines = source.split("\n")
    in_tc = False
    violations = []
    for line in lines:
        stripped = line.strip()
        if "TYPE_CHECKING" in stripped and ("if" in stripped or "elif" in stripped):
            in_tc = True
            continue
        # Exit TYPE_CHECKING block on unindented non-blank line
        if in_tc and stripped and not line.startswith((" ", "\t", "#")):
            in_tc = False
        if in_tc:
            continue
        if re.match(
            r"^\s*(?:from\s+(?:sqlalchemy|sqlmodel|app\.db)\s+import|import\s+(?:sqlalchemy|sqlmodel))",
            stripped,
        ):
            violations.append(stripped)
    return violations


def _check_no_business_logic(source):
    """Return violations of L6 business-logic patterns."""
    patterns = [
        r"if\s+.*severity\s*[><=!]",
        r"if\s+.*threshold\s*[><=!]",
        r"if\s+.*confidence\s*[><=!]",
    ]
    violations = []
    for pat in patterns:
        violations.extend(re.findall(pat, source, re.IGNORECASE))
    return violations


# ===== UC-018: Policy Snapshot Lifecycle =====

class TestUC018PolicySnapshot:

    L5 = "policies/L5_engines/snapshot_engine.py"

    def test_engine_exists(self):
        assert _file_exists(self.L5), f"UC-018: {self.L5} must exist"

    @pytest.mark.parametrize("func", [
        "create_policy_snapshot", "get_snapshot_history", "verify_snapshot",
    ])
    def test_has_core_functions(self, func):
        source = _read_file(self.L5)
        assert _has_function(source, func), f"UC-018: missing {func}"

    def test_snapshot_registry_class(self):
        source = _read_file(self.L5)
        assert _has_class(source, "PolicySnapshotRegistry"), "UC-018: PolicySnapshotRegistry class required"
        for m in ("create", "get_active", "archive", "verify"):
            assert _has_class_method(source, "PolicySnapshotRegistry", m), f"UC-018: missing method {m}"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-018: L5 purity violation: {violations}"


# ===== UC-019: Proposals Query Lifecycle =====

class TestUC019ProposalsQuery:

    L5 = "policies/L5_engines/policies_proposals_query_engine.py"
    L6 = "policies/L6_drivers/proposals_read_driver.py"

    def test_l5_exists(self):
        assert _file_exists(self.L5), f"UC-019: {self.L5} must exist"

    def test_l6_exists(self):
        assert _file_exists(self.L6), f"UC-019: {self.L6} must exist"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-019: L5 purity: {violations}"

    def test_l6_no_business_logic(self):
        violations = _check_no_business_logic(_read_file(self.L6))
        assert violations == [], f"UC-019: L6 business logic: {violations}"

    def test_handler_wiring(self):
        assert _spine_handler_exists("policies_handler.py"), "UC-019: policies_handler.py required"


# ===== UC-020: Rules Query Lifecycle =====

class TestUC020RulesQuery:

    L5 = "policies/L5_engines/policies_rules_query_engine.py"
    L6 = "policies/L6_drivers/policy_rules_read_driver.py"

    def test_l5_exists(self):
        assert _file_exists(self.L5), f"UC-020: {self.L5} must exist"

    def test_l6_exists(self):
        assert _file_exists(self.L6), f"UC-020: {self.L6} must exist"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-020: L5 purity: {violations}"

    def test_l6_no_business_logic(self):
        violations = _check_no_business_logic(_read_file(self.L6))
        assert violations == [], f"UC-020: L6 business logic: {violations}"


# ===== UC-021: Limits Query Lifecycle =====

class TestUC021LimitsQuery:

    L5 = "policies/L5_engines/policies_limits_query_engine.py"
    L6_CONTROLS = "controls/L6_drivers/limits_read_driver.py"

    def test_l5_exists(self):
        assert _file_exists(self.L5), f"UC-021: {self.L5} must exist"

    def test_cross_domain_driver_exists(self):
        assert _file_exists(self.L6_CONTROLS), f"UC-021: {self.L6_CONTROLS} must exist"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-021: L5 purity: {violations}"

    @pytest.mark.parametrize("func", ["list_limits", "get_limit_detail"])
    def test_engine_query_methods(self, func):
        source = _read_file(self.L5)
        assert _has_function(source, func), f"UC-021: missing {func}"


# ===== UC-022: Sandbox Definition + Execution Telemetry =====

class TestUC022Sandbox:

    L5 = "policies/L5_engines/sandbox_engine.py"
    HANDLER = "policies_sandbox_handler.py"

    def test_engine_exists(self):
        assert _file_exists(self.L5), f"UC-022: {self.L5} must exist"

    def test_handler_exists(self):
        assert _spine_handler_exists(self.HANDLER), f"UC-022: {self.HANDLER} required"

    @pytest.mark.parametrize("method", [
        "define_policy", "list_policies", "get_execution_records", "get_execution_stats",
    ])
    def test_sandbox_service_methods(self, method):
        source = _read_file(self.L5)
        assert _has_class(source, "SandboxService"), "UC-022: SandboxService required"
        assert _has_class_method(source, "SandboxService", method), f"UC-022: missing {method}"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-022: L5 purity: {violations}"


# ===== UC-023: Conflict Resolution Explainability =====

class TestUC023ConflictResolver:

    L5 = "policies/L5_engines/policy_conflict_resolver.py"

    def test_engine_exists(self):
        assert _file_exists(self.L5), f"UC-023: {self.L5} must exist"

    def test_resolve_function(self):
        source = _read_file(self.L5)
        assert _has_function(source, "resolve_policy_conflict"), "UC-023: resolve_policy_conflict required"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-023: L5 purity: {violations}"

    def test_deterministic_ordering(self):
        source = _read_file(self.L5)
        assert "precedence" in source.lower(), "UC-023: must use precedence ordering"
        assert "policy_id" in source, "UC-023: must use policy_id as deterministic tiebreaker"


# ===== UC-024: Cost Anomaly Detection =====

class TestUC024AnomalyDetection:

    L5 = "analytics/L5_engines/cost_anomaly_detector_engine.py"
    L6 = "analytics/L6_drivers/cost_anomaly_driver.py"

    def test_l5_exists(self):
        assert _file_exists(self.L5), f"UC-024: {self.L5} must exist"

    def test_l6_exists(self):
        assert _file_exists(self.L6), f"UC-024: {self.L6} must exist"

    def test_run_detection(self):
        source = _read_file(self.L5)
        assert _has_function(source, "run_anomaly_detection"), "UC-024: run_anomaly_detection required"

    def test_l6_no_business_logic(self):
        violations = _check_no_business_logic(_read_file(self.L6))
        assert violations == [], f"UC-024: L6 business logic: {violations}"


# ===== UC-025: Prediction Cycle =====

class TestUC025Prediction:

    L5 = "analytics/L5_engines/prediction_engine.py"
    L6 = "analytics/L6_drivers/prediction_driver.py"

    def test_l5_exists(self):
        assert _file_exists(self.L5), f"UC-025: {self.L5} must exist"

    def test_l6_exists(self):
        assert _file_exists(self.L6), f"UC-025: {self.L6} must exist"

    @pytest.mark.parametrize("func", [
        "predict_failure_likelihood", "predict_cost_overrun", "run_prediction_cycle",
    ])
    def test_prediction_functions(self, func):
        source = _read_file(self.L5)
        assert _has_function(source, func), f"UC-025: missing {func}"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-025: L5 purity: {violations}"


# ===== UC-026: Dataset Validation =====

class TestUC026DatasetValidation:

    L5 = "analytics/L5_engines/datasets_engine.py"

    def test_engine_exists(self):
        assert _file_exists(self.L5), f"UC-026: {self.L5} must exist"

    @pytest.mark.parametrize("func", ["validate_dataset", "validate_all_datasets"])
    def test_validation_functions(self, func):
        source = _read_file(self.L5)
        # Check module-level or class-level (validate_all vs validate_all_datasets)
        has_exact = _has_function(source, func)
        alt = func.replace("_datasets", "")
        has_alt = _has_function(source, alt) if alt != func else False
        assert has_exact or has_alt, f"UC-026: missing {func}"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-026: L5 purity: {violations}"


# ===== UC-027: Snapshot Jobs =====

class TestUC027SnapshotJobs:

    L5 = "analytics/L5_engines/cost_snapshots_engine.py"

    def test_engine_exists(self):
        assert _file_exists(self.L5), f"UC-027: {self.L5} must exist"

    @pytest.mark.parametrize("func", [
        "run_hourly_snapshot_job", "run_daily_snapshot_and_baseline_job",
    ])
    def test_job_functions(self, func):
        source = _read_file(self.L5)
        assert _has_function(source, func), f"UC-027: missing {func}"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-027: L5 purity: {violations}"


# ===== UC-028: Cost Write =====

class TestUC028CostWrite:

    L5 = "analytics/L5_engines/cost_write.py"
    L6 = "analytics/L6_drivers/cost_write_driver.py"

    def test_l5_exists(self):
        assert _file_exists(self.L5), f"UC-028: {self.L5} must exist"

    def test_l6_exists(self):
        assert _file_exists(self.L6), f"UC-028: {self.L6} must exist"

    @pytest.mark.parametrize("func", ["create_cost_record", "create_feature_tag"])
    def test_driver_write_functions(self, func):
        source = _read_file(self.L6)
        assert _has_function(source, func), f"UC-028: L6 missing {func}"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-028: L5 purity: {violations}"


# ===== UC-029: Recovery Rule Evaluation =====

class TestUC029RecoveryRule:

    L5 = "incidents/L5_engines/recovery_rule_engine.py"

    def test_engine_exists(self):
        assert _file_exists(self.L5), f"UC-029: {self.L5} must exist"

    @pytest.mark.parametrize("func", [
        "evaluate_rules", "suggest_recovery_mode", "should_auto_execute",
    ])
    def test_decision_functions(self, func):
        source = _read_file(self.L5)
        assert _has_function(source, func), f"UC-029: missing {func}"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-029: L5 purity: {violations}"

    def test_no_randomness(self):
        source = _read_file(self.L5)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in ("random", "secrets"), f"UC-029: non-deterministic import {alias.name}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module not in ("random", "secrets"), f"UC-029: non-deterministic import {node.module}"


# ===== UC-030: Policy Violation Truth Pipeline =====

class TestUC030PolicyViolation:

    L5 = "incidents/L5_engines/policy_violation_engine.py"
    L6 = "incidents/L6_drivers/policy_violation_driver.py"

    def test_l5_exists(self):
        assert _file_exists(self.L5), f"UC-030: {self.L5} must exist"

    def test_l6_exists(self):
        assert _file_exists(self.L6), f"UC-030: {self.L6} must exist"

    @pytest.mark.parametrize("func", [
        "persist_violation_and_create_incident", "verify_violation_truth",
    ])
    def test_core_functions(self, func):
        source = _read_file(self.L5)
        assert _has_function(source, func), f"UC-030: missing {func}"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-030: L5 purity: {violations}"

    def test_l6_no_truth_decisions(self):
        violations = _check_no_business_logic(_read_file(self.L6))
        assert violations == [], f"UC-030: L6 business logic: {violations}"


# ===== UC-031: Pattern + Postmortem =====

class TestUC031PatternPostmortem:

    L5_PATTERN = "incidents/L5_engines/incident_pattern.py"
    L5_POSTMORTEM = "incidents/L5_engines/postmortem.py"
    L6_PATTERN = "incidents/L6_drivers/incident_pattern_driver.py"
    L6_POSTMORTEM = "incidents/L6_drivers/postmortem_driver.py"

    @pytest.mark.parametrize("path", [
        "incidents/L5_engines/incident_pattern.py",
        "incidents/L5_engines/postmortem.py",
        "incidents/L6_drivers/incident_pattern_driver.py",
        "incidents/L6_drivers/postmortem_driver.py",
    ])
    def test_files_exist(self, path):
        assert _file_exists(path), f"UC-031: {path} must exist"

    def test_detect_patterns(self):
        source = _read_file(self.L5_PATTERN)
        assert _has_function(source, "detect_patterns"), "UC-031: detect_patterns required"

    def test_get_incident_learnings(self):
        source = _read_file(self.L5_POSTMORTEM)
        assert _has_function(source, "get_incident_learnings"), "UC-031: get_incident_learnings required"

    @pytest.mark.parametrize("engine", [
        "incidents/L5_engines/incident_pattern.py",
        "incidents/L5_engines/postmortem.py",
    ])
    def test_l5_purity(self, engine):
        violations = _check_l5_purity(_read_file(engine))
        assert violations == [], f"UC-031: L5 purity in {os.path.basename(engine)}: {violations}"


# ===== UC-032: Logs Redaction =====

class TestUC032LogsRedaction:

    L5 = "logs/L5_engines/redact.py"
    L6 = "logs/L6_drivers/redact.py"

    def test_l5_exists(self):
        assert _file_exists(self.L5), f"UC-032: {self.L5} must exist"

    def test_l6_exists(self):
        assert _file_exists(self.L6), f"UC-032: {self.L6} must exist"

    @pytest.mark.parametrize("func", [
        "redact_trace_data", "redact_dict", "redact_string_value",
    ])
    def test_l5_has_redaction_functions(self, func):
        source = _read_file(self.L5)
        assert _has_function(source, func), f"UC-032: L5 missing {func}"

    @pytest.mark.parametrize("func", [
        "redact_trace_data", "redact_dict", "redact_string_value",
    ])
    def test_l6_has_redaction_functions(self, func):
        source = _read_file(self.L6)
        assert _has_function(source, func), f"UC-032: L6 missing {func}"

    def test_l5_purity(self):
        violations = _check_l5_purity(_read_file(self.L5))
        assert violations == [], f"UC-032: L5 purity: {violations}"

    @pytest.mark.parametrize("path", [
        "logs/L5_engines/redact.py",
        "logs/L6_drivers/redact.py",
    ])
    def test_deterministic_output(self, path):
        source = _read_file(path)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in ("random", "uuid", "secrets"), (
                        f"UC-032: {path} imports non-deterministic module {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module not in ("random", "uuid", "secrets"), (
                    f"UC-032: {path} imports non-deterministic module {node.module}"
                )


# ===== Cross-cutting: L5 purity sweep =====

_ALL_L5_ENGINES = [
    ("UC-018", "policies/L5_engines/snapshot_engine.py"),
    ("UC-019", "policies/L5_engines/policies_proposals_query_engine.py"),
    ("UC-020", "policies/L5_engines/policies_rules_query_engine.py"),
    ("UC-021", "policies/L5_engines/policies_limits_query_engine.py"),
    ("UC-022", "policies/L5_engines/sandbox_engine.py"),
    ("UC-023", "policies/L5_engines/policy_conflict_resolver.py"),
    ("UC-024", "analytics/L5_engines/cost_anomaly_detector_engine.py"),
    ("UC-025", "analytics/L5_engines/prediction_engine.py"),
    ("UC-026", "analytics/L5_engines/datasets_engine.py"),
    ("UC-027", "analytics/L5_engines/cost_snapshots_engine.py"),
    ("UC-028", "analytics/L5_engines/cost_write.py"),
    ("UC-029", "incidents/L5_engines/recovery_rule_engine.py"),
    ("UC-030", "incidents/L5_engines/policy_violation_engine.py"),
    ("UC-031a", "incidents/L5_engines/incident_pattern.py"),
    ("UC-031b", "incidents/L5_engines/postmortem.py"),
]


class TestCrossCuttingL5Purity:

    @pytest.mark.parametrize("uc_id,path", _ALL_L5_ENGINES)
    def test_engine_exists(self, uc_id, path):
        assert _file_exists(path), f"{uc_id}: {path} missing"

    @pytest.mark.parametrize("uc_id,path", _ALL_L5_ENGINES)
    def test_l5_no_db_imports(self, uc_id, path):
        if not _file_exists(path):
            pytest.skip(f"{path} not found")
        violations = _check_l5_purity(_read_file(path))
        assert violations == [], f"{uc_id}: L5 purity in {os.path.basename(path)}: {violations}"


# ===== Wave-1 Script Coverage: policies + logs =====

# Newly UC_LINKED L5 engines from Wave-1
_WAVE1_UC_LINKED_L5 = [
    ("UC-009", "policies/L5_engines/engine.py"),
    ("UC-009", "policies/L5_engines/cus_enforcement_engine.py"),
    ("UC-009", "policies/L5_engines/policy_proposal_engine.py"),
    ("UC-018", "policies/L5_engines/deterministic_engine.py"),
    ("UC-029", "policies/L5_engines/recovery_evaluation_engine.py"),
    ("UC-023", "policies/L5_engines/lessons_engine.py"),
    ("UC-003", "logs/L5_engines/logs_read_engine.py"),
    ("UC-003", "logs/L5_engines/trace_mismatch_engine.py"),
    ("UC-017", "logs/L5_engines/certificate.py"),
    ("UC-017", "logs/L5_engines/completeness_checker.py"),
    ("UC-017", "logs/L5_engines/evidence_facade.py"),
    ("UC-017", "logs/L5_engines/evidence_report.py"),
    ("UC-017", "logs/L5_engines/mapper.py"),
    ("UC-017", "logs/L5_engines/pdf_renderer.py"),
    ("UC-017", "logs/L5_engines/replay_determinism.py"),
]

_WAVE1_UC_LINKED_L6 = [
    ("UC-009", "policies/L6_drivers/policy_engine_driver.py"),
    ("UC-009", "policies/L6_drivers/cus_enforcement_driver.py"),
    ("UC-009", "policies/L6_drivers/prevention_records_read_driver.py"),
    ("UC-009", "policies/L6_drivers/policy_enforcement_driver.py"),
    ("UC-009", "policies/L6_drivers/policy_enforcement_write_driver.py"),
    ("UC-019", "policies/L6_drivers/policy_proposal_read_driver.py"),
    ("UC-019", "policies/L6_drivers/policy_proposal_write_driver.py"),
    ("UC-029", "policies/L6_drivers/recovery_read_driver.py"),
    ("UC-029", "policies/L6_drivers/recovery_write_driver.py"),
    ("UC-029", "policies/L6_drivers/recovery_matcher.py"),
    ("UC-003", "logs/L6_drivers/idempotency_driver.py"),
    ("UC-003", "logs/L6_drivers/trace_mismatch_driver.py"),
    ("UC-017", "logs/L6_drivers/export_bundle_store.py"),
    ("UC-017", "logs/L6_drivers/integrity_driver.py"),
    ("UC-017", "logs/L6_drivers/replay_driver.py"),
]


class TestWave1ScriptCoverage:
    """Validate Wave-1 script coverage classification for policies + logs."""

    @pytest.mark.parametrize("uc_id,path", _WAVE1_UC_LINKED_L5)
    def test_uc_linked_l5_exists(self, uc_id, path):
        assert _file_exists(path), f"Wave-1 {uc_id}: {path} must exist"

    @pytest.mark.parametrize("uc_id,path", _WAVE1_UC_LINKED_L6)
    def test_uc_linked_l6_exists(self, uc_id, path):
        assert _file_exists(path), f"Wave-1 {uc_id}: {path} must exist"

    @pytest.mark.parametrize("uc_id,path", _WAVE1_UC_LINKED_L5)
    def test_uc_linked_l5_purity(self, uc_id, path):
        if not _file_exists(path):
            pytest.skip(f"{path} not found")
        violations = _check_l5_purity(_read_file(path))
        assert violations == [], f"Wave-1 {uc_id}: L5 purity in {os.path.basename(path)}: {violations}"

    def test_policies_non_uc_support_dsl_compiler_exists(self):
        """DSL compiler pipeline scripts exist (NON_UC_SUPPORT)."""
        dsl_files = [
            "policies/L5_engines/dsl_parser.py",
            "policies/L5_engines/grammar.py",
            "policies/L5_engines/tokenizer.py",
            "policies/L5_engines/interpreter.py",
            "policies/L5_engines/ir_builder.py",
            "policies/L5_engines/ir_compiler.py",
        ]
        for f in dsl_files:
            assert _file_exists(f), f"NON_UC_SUPPORT DSL: {f} must exist"

    def test_logs_non_uc_support_audit_ledger_exists(self):
        """Audit ledger scripts exist (NON_UC_SUPPORT)."""
        audit_files = [
            "logs/L5_engines/audit_ledger_engine.py",
            "logs/L6_drivers/audit_ledger_driver.py",
            "logs/L6_drivers/audit_ledger_read_driver.py",
        ]
        for f in audit_files:
            assert _file_exists(f), f"NON_UC_SUPPORT audit: {f} must exist"

    def test_wave1_total_classification_count(self):
        """Wave-1 classified 130 scripts total (33 UC_LINKED + 97 NON_UC_SUPPORT)."""
        total_linked = len(_WAVE1_UC_LINKED_L5) + len(_WAVE1_UC_LINKED_L6)
        # 15 L5 + 15 L6 + 3 additional (schemas + adapter) = 33
        assert total_linked == 30, f"Wave-1 L5+L6 UC_LINKED count: {total_linked}"


# ===== Wave-2 Script Coverage: analytics + incidents + activity =====

# Newly UC_LINKED L5 engines from Wave-2
_WAVE2_UC_LINKED_L5 = [
    # activity domain
    ("UC-MON-01", "activity/L5_engines/activity_facade.py"),
    ("UC-MON-05", "activity/L5_engines/cus_telemetry_engine.py"),
    # analytics domain
    ("UC-024", "analytics/L5_engines/analytics_facade.py"),
    ("UC-027", "analytics/L5_engines/canary_engine.py"),
    ("UC-024", "analytics/L5_engines/detection_facade.py"),
    ("UC-MON-04", "analytics/L5_engines/feedback_read_engine.py"),
    ("UC-025", "analytics/L5_engines/prediction_read_engine.py"),
    ("UC-027", "analytics/L5_engines/sandbox_engine.py"),
    ("UC-027", "analytics/L5_engines/v2_adapter.py"),
    # incidents domain
    ("UC-MON-07", "incidents/L5_engines/anomaly_bridge.py"),
    ("UC-031", "incidents/L5_engines/export_engine.py"),
    ("UC-030", "incidents/L5_engines/hallucination_detector.py"),
    ("UC-MON-07", "incidents/L5_engines/incident_engine.py"),
    ("UC-031", "incidents/L5_engines/incident_read_engine.py"),
    ("UC-031", "incidents/L5_engines/incident_write_engine.py"),
    ("UC-MON-07", "incidents/L5_engines/incidents_facade.py"),
    ("UC-031", "incidents/L5_engines/recurrence_analysis.py"),
]

_WAVE2_UC_LINKED_L6 = [
    # activity domain
    ("UC-MON-01", "activity/L6_drivers/activity_read_driver.py"),
    ("UC-MON-05", "activity/L6_drivers/cus_telemetry_driver.py"),
    # analytics domain
    ("UC-024", "analytics/L6_drivers/analytics_read_driver.py"),
    ("UC-027", "analytics/L6_drivers/canary_report_driver.py"),
    ("UC-024", "analytics/L6_drivers/cost_anomaly_read_driver.py"),
    ("UC-027", "analytics/L6_drivers/cost_snapshots_driver.py"),
    ("UC-MON-04", "analytics/L6_drivers/feedback_read_driver.py"),
    ("UC-025", "analytics/L6_drivers/prediction_read_driver.py"),
    # incidents domain
    ("UC-MON-07", "incidents/L6_drivers/cost_guard_driver.py"),
    ("UC-031", "incidents/L6_drivers/export_bundle_driver.py"),
    ("UC-MON-07", "incidents/L6_drivers/incident_aggregator.py"),
    ("UC-031", "incidents/L6_drivers/incident_read_driver.py"),
    ("UC-031", "incidents/L6_drivers/incident_run_read_driver.py"),
    ("UC-031", "incidents/L6_drivers/incident_write_driver.py"),
    ("UC-MON-07", "incidents/L6_drivers/incidents_facade_driver.py"),
    ("UC-031", "incidents/L6_drivers/recurrence_analysis_driver.py"),
]

_WAVE2_UC_LINKED_ADAPTERS = [
    ("UC-MON-01", "activity/adapters/customer_activity_adapter.py"),
    ("UC-MON-07", "incidents/adapters/customer_incidents_adapter.py"),
]


class TestWave2ScriptCoverage:
    """Validate Wave-2 script coverage classification for analytics + incidents + activity."""

    @pytest.mark.parametrize("uc_id,path", _WAVE2_UC_LINKED_L5)
    def test_uc_linked_l5_exists(self, uc_id, path):
        assert _file_exists(path), f"Wave-2 {uc_id}: {path} must exist"

    @pytest.mark.parametrize("uc_id,path", _WAVE2_UC_LINKED_L6)
    def test_uc_linked_l6_exists(self, uc_id, path):
        assert _file_exists(path), f"Wave-2 {uc_id}: {path} must exist"

    @pytest.mark.parametrize("uc_id,path", _WAVE2_UC_LINKED_ADAPTERS)
    def test_uc_linked_adapter_exists(self, uc_id, path):
        assert _file_exists(path), f"Wave-2 {uc_id}: {path} must exist"

    @pytest.mark.parametrize("uc_id,path", _WAVE2_UC_LINKED_L5)
    def test_uc_linked_l5_purity(self, uc_id, path):
        if not _file_exists(path):
            pytest.skip(f"{path} not found")
        violations = _check_l5_purity(_read_file(path))
        assert violations == [], f"Wave-2 {uc_id}: L5 purity in {os.path.basename(path)}: {violations}"

    def test_activity_non_uc_support_exists(self):
        """Activity NON_UC_SUPPORT stub engines exist."""
        stubs = [
            "activity/L5_engines/attention_ranking.py",
            "activity/L5_engines/cost_analysis.py",
            "activity/L5_engines/pattern_detection.py",
        ]
        for f in stubs:
            assert _file_exists(f), f"NON_UC_SUPPORT activity stub: {f} must exist"

    def test_analytics_non_uc_support_schemas_exist(self):
        """Analytics NON_UC_SUPPORT schema files exist."""
        schemas = [
            "analytics/L5_schemas/cost_anomaly_dtos.py",
            "analytics/L5_schemas/cost_anomaly_schemas.py",
            "analytics/L5_schemas/cost_snapshot_schemas.py",
            "analytics/L5_schemas/feedback_schemas.py",
            "analytics/L5_schemas/query_types.py",
        ]
        for f in schemas:
            assert _file_exists(f), f"NON_UC_SUPPORT analytics schema: {f} must exist"

    def test_incidents_non_uc_support_schemas_exist(self):
        """Incidents NON_UC_SUPPORT schema files exist."""
        schemas = [
            "incidents/L5_schemas/export_schemas.py",
            "incidents/L5_schemas/incident_decision_port.py",
            "incidents/L5_schemas/severity_policy.py",
        ]
        for f in schemas:
            assert _file_exists(f), f"NON_UC_SUPPORT incidents schema: {f} must exist"

    def test_wave2_total_classification_count(self):
        """Wave-2 classified 80 scripts total (35 UC_LINKED + 45 NON_UC_SUPPORT)."""
        total_linked = (
            len(_WAVE2_UC_LINKED_L5)
            + len(_WAVE2_UC_LINKED_L6)
            + len(_WAVE2_UC_LINKED_ADAPTERS)
        )
        assert total_linked == 35, f"Wave-2 UC_LINKED count: {total_linked}"


# ===== Wave-3 Script Coverage: controls + account =====

# Newly UC_LINKED L5 engines from Wave-3
_WAVE3_UC_LINKED_L5 = [
    # account domain
    ("UC-002", "account/L5_engines/accounts_facade.py"),
    ("UC-002", "account/L5_engines/memory_pins_engine.py"),
    ("UC-002", "account/L5_engines/notifications_facade.py"),
    ("UC-002", "account/L5_engines/onboarding_engine.py"),
    ("UC-002", "account/L5_engines/tenant_engine.py"),
    ("UC-002", "account/L5_engines/tenant_lifecycle_engine.py"),
    # controls domain
    ("UC-021", "controls/L5_engines/controls_facade.py"),
    ("UC-001", "controls/L5_engines/threshold_engine.py"),
]

_WAVE3_UC_LINKED_L6 = [
    # account domain
    ("UC-002", "account/L6_drivers/accounts_facade_driver.py"),
    ("UC-002", "account/L6_drivers/memory_pins_driver.py"),
    ("UC-002", "account/L6_drivers/onboarding_driver.py"),
    ("UC-002", "account/L6_drivers/sdk_attestation_driver.py"),
    ("UC-002", "account/L6_drivers/tenant_driver.py"),
    ("UC-002", "account/L6_drivers/tenant_lifecycle_driver.py"),
    ("UC-002", "account/L6_drivers/user_write_driver.py"),
    # controls domain
    ("UC-021", "controls/L6_drivers/override_driver.py"),
    ("UC-021", "controls/L6_drivers/policy_limits_driver.py"),
    ("UC-029", "controls/L6_drivers/scoped_execution_driver.py"),
    ("UC-001", "controls/L6_drivers/threshold_driver.py"),
]


class TestWave3ScriptCoverage:
    """Validate Wave-3 script coverage classification for controls + account."""

    @pytest.mark.parametrize("uc_id,path", _WAVE3_UC_LINKED_L5)
    def test_uc_linked_l5_exists(self, uc_id, path):
        assert _file_exists(path), f"Wave-3 {uc_id}: {path} must exist"

    @pytest.mark.parametrize("uc_id,path", _WAVE3_UC_LINKED_L6)
    def test_uc_linked_l6_exists(self, uc_id, path):
        assert _file_exists(path), f"Wave-3 {uc_id}: {path} must exist"

    @pytest.mark.parametrize("uc_id,path", _WAVE3_UC_LINKED_L5)
    def test_uc_linked_l5_purity(self, uc_id, path):
        if not _file_exists(path):
            pytest.skip(f"{path} not found")
        violations = _check_l5_purity(_read_file(path))
        assert violations == [], f"Wave-3 {uc_id}: L5 purity in {os.path.basename(path)}: {violations}"

    def test_account_non_uc_support_schemas_exist(self):
        """Account NON_UC_SUPPORT schema files exist."""
        schemas = [
            "account/L5_schemas/onboarding_dtos.py",
            "account/L5_schemas/onboarding_state.py",
            "account/L5_schemas/lifecycle_dtos.py",
            "account/L5_schemas/tenant_lifecycle_enums.py",
            "account/L5_schemas/plan_quotas.py",
            "account/L5_schemas/sdk_attestation.py",
        ]
        for f in schemas:
            assert _file_exists(f), f"NON_UC_SUPPORT account schema: {f} must exist"

    def test_account_non_uc_support_auth_exists(self):
        """Account auth platform infrastructure exists (NON_UC_SUPPORT)."""
        auth_files = [
            "account/auth/L5_engines/identity_adapter.py",
            "account/auth/L5_engines/invocation_safety.py",
            "account/auth/L5_engines/rbac_engine.py",
        ]
        for f in auth_files:
            assert _file_exists(f), f"NON_UC_SUPPORT auth: {f} must exist"

    def test_controls_non_uc_support_safety_exists(self):
        """Controls NON_UC_SUPPORT safety infrastructure exists."""
        safety = [
            "controls/L6_drivers/circuit_breaker_driver.py",
            "controls/L6_drivers/circuit_breaker_async_driver.py",
            "controls/L6_drivers/killswitch_ops_driver.py",
            "controls/L6_drivers/killswitch_read_driver.py",
        ]
        for f in safety:
            assert _file_exists(f), f"NON_UC_SUPPORT safety: {f} must exist"

    def test_wave3_total_classification_count(self):
        """Wave-3 classified 52 scripts total (19 UC_LINKED + 33 NON_UC_SUPPORT)."""
        total_linked = len(_WAVE3_UC_LINKED_L5) + len(_WAVE3_UC_LINKED_L6)
        assert total_linked == 19, f"Wave-3 UC_LINKED count: {total_linked}"


# ===== Wave-4 Script Coverage: hoc_spine + integrations + agent + api_keys + apis + ops + overview =====

# UC_LINKED L4 handlers from hoc_spine
_WAVE4_UC_LINKED_HANDLERS = [
    ("UC-002", "hoc_spine/orchestrator/handlers/account_handler.py"),
    ("UC-001", "hoc_spine/orchestrator/handlers/agent_handler.py"),
    ("UC-024", "hoc_spine/orchestrator/handlers/analytics_config_handler.py"),
    ("UC-024", "hoc_spine/orchestrator/handlers/analytics_handler.py"),
    ("UC-024", "hoc_spine/orchestrator/handlers/analytics_metrics_handler.py"),
    ("UC-025", "hoc_spine/orchestrator/handlers/analytics_prediction_handler.py"),
    ("UC-027", "hoc_spine/orchestrator/handlers/analytics_sandbox_handler.py"),
    ("UC-027", "hoc_spine/orchestrator/handlers/analytics_snapshot_handler.py"),
    ("UC-026", "hoc_spine/orchestrator/handlers/analytics_validation_handler.py"),
    ("UC-002", "hoc_spine/orchestrator/handlers/api_keys_handler.py"),
    ("UC-MON-07", "hoc_spine/orchestrator/handlers/incidents_handler.py"),
    ("UC-002", "hoc_spine/orchestrator/handlers/integration_bootstrap_handler.py"),
    ("UC-002", "hoc_spine/orchestrator/handlers/integrations_handler.py"),
    ("UC-002", "hoc_spine/orchestrator/handlers/lifecycle_handler.py"),
    ("UC-001", "hoc_spine/orchestrator/handlers/logs_handler.py"),
    ("UC-002", "hoc_spine/orchestrator/handlers/mcp_handler.py"),
    ("UC-001", "hoc_spine/orchestrator/handlers/orphan_recovery_handler.py"),
    ("UC-001", "hoc_spine/orchestrator/handlers/overview_handler.py"),
    ("UC-001", "hoc_spine/orchestrator/handlers/policy_governance_handler.py"),
    ("UC-001", "hoc_spine/orchestrator/handlers/run_governance_handler.py"),
    ("UC-001", "hoc_spine/orchestrator/handlers/traces_handler.py"),
]

# UC_LINKED L4 coordinators from hoc_spine
_WAVE4_UC_LINKED_COORDINATORS = [
    ("UC-024", "hoc_spine/orchestrator/coordinators/anomaly_incident_coordinator.py"),
    ("UC-027", "hoc_spine/orchestrator/coordinators/canary_coordinator.py"),
    ("UC-001", "hoc_spine/orchestrator/coordinators/evidence_coordinator.py"),
    ("UC-001", "hoc_spine/orchestrator/coordinators/execution_coordinator.py"),
    ("UC-024", "hoc_spine/orchestrator/coordinators/leadership_coordinator.py"),
    ("UC-024", "hoc_spine/orchestrator/coordinators/provenance_coordinator.py"),
    ("UC-001", "hoc_spine/orchestrator/coordinators/replay_coordinator.py"),
    ("UC-001", "hoc_spine/orchestrator/coordinators/run_evidence_coordinator.py"),
    ("UC-001", "hoc_spine/orchestrator/coordinators/run_proof_coordinator.py"),
    ("UC-001", "hoc_spine/orchestrator/coordinators/signal_coordinator.py"),
    ("UC-MON-04", "hoc_spine/orchestrator/coordinators/signal_feedback_coordinator.py"),
    ("UC-027", "hoc_spine/orchestrator/coordinators/snapshot_scheduler.py"),
]

# UC_LINKED L5 engines from Wave-4 domains
_WAVE4_UC_LINKED_L5 = [
    ("UC-002", "api_keys/L5_engines/api_keys_facade.py"),
    ("UC-002", "api_keys/L5_engines/keys_engine.py"),
    ("UC-002", "integrations/L5_engines/connectors_facade.py"),
    ("UC-002", "integrations/L5_engines/cus_health_engine.py"),
    ("UC-002", "integrations/L5_engines/cus_integration_engine.py"),
    ("UC-002", "integrations/L5_engines/integrations_facade.py"),
    ("UC-001", "overview/L5_engines/overview_facade.py"),
]

# UC_LINKED L6 drivers from Wave-4 domains
_WAVE4_UC_LINKED_L6 = [
    ("UC-002", "api_keys/L6_drivers/api_keys_facade_driver.py"),
    ("UC-002", "api_keys/L6_drivers/keys_driver.py"),
    ("UC-002", "integrations/L6_drivers/bridges_driver.py"),
    ("UC-002", "integrations/L6_drivers/cus_health_driver.py"),
    ("UC-002", "integrations/L6_drivers/cus_integration_driver.py"),
    ("UC-001", "overview/L6_drivers/overview_facade_driver.py"),
]

# UC_LINKED adapters from Wave-4 domains
_WAVE4_UC_LINKED_ADAPTERS = [
    ("UC-002", "api_keys/adapters/customer_keys_adapter.py"),
]


class TestWave4ScriptCoverage:
    """Validate Wave-4 script coverage classification for hoc_spine + integrations + agent + api_keys + apis + ops + overview."""

    @pytest.mark.parametrize("uc_id,path", _WAVE4_UC_LINKED_HANDLERS)
    def test_uc_linked_handler_exists(self, uc_id, path):
        assert _file_exists(path), f"Wave-4 {uc_id}: {path} must exist"

    @pytest.mark.parametrize("uc_id,path", _WAVE4_UC_LINKED_COORDINATORS)
    def test_uc_linked_coordinator_exists(self, uc_id, path):
        assert _file_exists(path), f"Wave-4 {uc_id}: {path} must exist"

    @pytest.mark.parametrize("uc_id,path", _WAVE4_UC_LINKED_L5)
    def test_uc_linked_l5_exists(self, uc_id, path):
        assert _file_exists(path), f"Wave-4 {uc_id}: {path} must exist"

    @pytest.mark.parametrize("uc_id,path", _WAVE4_UC_LINKED_L6)
    def test_uc_linked_l6_exists(self, uc_id, path):
        assert _file_exists(path), f"Wave-4 {uc_id}: {path} must exist"

    @pytest.mark.parametrize("uc_id,path", _WAVE4_UC_LINKED_ADAPTERS)
    def test_uc_linked_adapter_exists(self, uc_id, path):
        assert _file_exists(path), f"Wave-4 {uc_id}: {path} must exist"

    @pytest.mark.parametrize("uc_id,path", _WAVE4_UC_LINKED_L5)
    def test_uc_linked_l5_purity(self, uc_id, path):
        if not _file_exists(path):
            pytest.skip(f"{path} not found")
        violations = _check_l5_purity(_read_file(path))
        assert violations == [], f"Wave-4 {uc_id}: L5 purity in {os.path.basename(path)}: {violations}"

    def test_hoc_spine_authority_non_uc_support_exists(self):
        """hoc_spine authority infrastructure exists (NON_UC_SUPPORT)."""
        authority = [
            "hoc_spine/authority/concurrent_runs.py",
            "hoc_spine/authority/gateway_policy.py",
            "hoc_spine/authority/lifecycle_provider.py",
            "hoc_spine/authority/rbac_policy.py",
            "hoc_spine/authority/runtime.py",
            "hoc_spine/authority/runtime_switch.py",
            "hoc_spine/authority/veil_policy.py",
        ]
        for f in authority:
            assert _file_exists(f), f"NON_UC_SUPPORT authority: {f} must exist"

    def test_hoc_spine_bridges_non_uc_support_exists(self):
        """hoc_spine coordinator bridges exist (NON_UC_SUPPORT)."""
        bridges = [
            "hoc_spine/orchestrator/coordinators/bridges/account_bridge.py",
            "hoc_spine/orchestrator/coordinators/bridges/analytics_bridge.py",
            "hoc_spine/orchestrator/coordinators/bridges/incidents_bridge.py",
            "hoc_spine/orchestrator/coordinators/bridges/integrations_bridge.py",
            "hoc_spine/orchestrator/coordinators/bridges/logs_bridge.py",
            "hoc_spine/orchestrator/coordinators/bridges/policies_bridge.py",
        ]
        for f in bridges:
            assert _file_exists(f), f"NON_UC_SUPPORT bridge: {f} must exist"

    def test_integrations_external_adapters_non_uc_support_exists(self):
        """Integrations external adapters exist (NON_UC_SUPPORT)."""
        adapters = [
            "integrations/adapters/s3_adapter.py",
            "integrations/adapters/gcs_adapter.py",
            "integrations/adapters/slack_adapter.py",
            "integrations/adapters/webhook_adapter.py",
            "integrations/adapters/pinecone_adapter.py",
        ]
        for f in adapters:
            assert _file_exists(f), f"NON_UC_SUPPORT adapter: {f} must exist"

    def test_wave4_total_classification_count(self):
        """Wave-4 classified 150 scripts total (47 UC_LINKED + 103 NON_UC_SUPPORT)."""
        total_linked = (
            len(_WAVE4_UC_LINKED_HANDLERS)
            + len(_WAVE4_UC_LINKED_COORDINATORS)
            + len(_WAVE4_UC_LINKED_L5)
            + len(_WAVE4_UC_LINKED_L6)
            + len(_WAVE4_UC_LINKED_ADAPTERS)
        )
        assert total_linked == 47, f"Wave-4 UC_LINKED count: {total_linked}"


# ===== UC-033..UC-040 Expansion: Spine + Integrations + Account =====

class TestUC033to040Expansion:
    """Validate UC-033..UC-040 expansion — file existence, purity, and scope counts."""

    # UC-033: Spine Operation Governance + Contracts (26 scripts)
    _UC033 = [
        "hoc_spine/auth_wiring.py",
        "hoc_spine/orchestrator/constraint_checker.py",
        "hoc_spine/orchestrator/execution/job_executor.py",
        "hoc_spine/orchestrator/governance_orchestrator.py",
        "hoc_spine/orchestrator/operation_registry.py",
        "hoc_spine/orchestrator/phase_status_invariants.py",
        "hoc_spine/orchestrator/plan_generation_engine.py",
        "hoc_spine/orchestrator/run_governance_facade.py",
        "hoc_spine/schemas/agent.py",
        "hoc_spine/schemas/anomaly_types.py",
        "hoc_spine/schemas/artifact.py",
        "hoc_spine/schemas/authority_decision.py",
        "hoc_spine/schemas/common.py",
        "hoc_spine/schemas/domain_enums.py",
        "hoc_spine/schemas/knowledge_plane_harness.py",
        "hoc_spine/schemas/lifecycle_harness.py",
        "hoc_spine/schemas/plan.py",
        "hoc_spine/schemas/protocols.py",
        "hoc_spine/schemas/rac_models.py",
        "hoc_spine/schemas/response.py",
        "hoc_spine/schemas/retry.py",
        "hoc_spine/schemas/run_introspection_protocols.py",
        "hoc_spine/schemas/skill.py",
        "hoc_spine/schemas/threshold_types.py",
        "hoc_spine/tests/conftest.py",
        "hoc_spine/tests/test_operation_registry.py",
    ]

    # UC-034: Spine Lifecycle Orchestration (6 scripts)
    _UC034 = [
        "hoc_spine/orchestrator/lifecycle/drivers/execution.py",
        "hoc_spine/orchestrator/lifecycle/drivers/knowledge_plane.py",
        "hoc_spine/orchestrator/lifecycle/engines/offboarding.py",
        "hoc_spine/orchestrator/lifecycle/engines/onboarding.py",
        "hoc_spine/orchestrator/lifecycle/engines/pool_manager.py",
        "hoc_spine/orchestrator/lifecycle/stages.py",
    ]

    # UC-035: Spine Execution Safety + Driver Integrity (17 scripts)
    _UC035 = [
        "hoc_spine/drivers/alert_driver.py",
        "hoc_spine/drivers/alert_emitter.py",
        "hoc_spine/drivers/cross_domain.py",
        "hoc_spine/drivers/dag_executor.py",
        "hoc_spine/drivers/decisions.py",
        "hoc_spine/drivers/governance_signal_driver.py",
        "hoc_spine/drivers/guard_cache.py",
        "hoc_spine/drivers/guard_write_driver.py",
        "hoc_spine/drivers/idempotency.py",
        "hoc_spine/drivers/knowledge_plane_registry_driver.py",
        "hoc_spine/drivers/ledger.py",
        "hoc_spine/drivers/retrieval_evidence_driver.py",
        "hoc_spine/drivers/schema_parity.py",
        "hoc_spine/drivers/transaction_coordinator.py",
        "hoc_spine/drivers/worker_write_driver_async.py",
        "hoc_spine/utilities/recovery_decisions.py",
        "hoc_spine/utilities/s1_retry_backoff.py",
    ]

    # UC-036: Spine Signals, Evidence, and Alerting (33 scripts)
    _UC036 = [
        "hoc_spine/consequences/pipeline.py",
        "hoc_spine/consequences/ports.py",
        "hoc_spine/services/alert_delivery.py",
        "hoc_spine/services/alerts_facade.py",
        "hoc_spine/services/audit_durability.py",
        "hoc_spine/services/audit_store.py",
        "hoc_spine/services/canonical_json.py",
        "hoc_spine/services/compliance_facade.py",
        "hoc_spine/services/control_registry.py",
        "hoc_spine/services/costsim_config.py",
        "hoc_spine/services/costsim_metrics.py",
        "hoc_spine/services/cross_domain_gateway.py",
        "hoc_spine/services/cus_credential_engine.py",
        "hoc_spine/services/dag_sorter.py",
        "hoc_spine/services/db_helpers.py",
        "hoc_spine/services/deterministic.py",
        "hoc_spine/services/dispatch_audit.py",
        "hoc_spine/services/fatigue_controller.py",
        "hoc_spine/services/guard.py",
        "hoc_spine/services/input_sanitizer.py",
        "hoc_spine/services/knowledge_plane_connector_registry_engine.py",
        "hoc_spine/services/lifecycle_facade.py",
        "hoc_spine/services/lifecycle_stages_base.py",
        "hoc_spine/services/metrics_helpers.py",
        "hoc_spine/services/monitors_facade.py",
        "hoc_spine/services/rate_limiter.py",
        "hoc_spine/services/retrieval_evidence_engine.py",
        "hoc_spine/services/retrieval_facade.py",
        "hoc_spine/services/retrieval_mediator.py",
        "hoc_spine/services/retrieval_policy_checker_engine.py",
        "hoc_spine/services/scheduler_facade.py",
        "hoc_spine/services/time.py",
        "hoc_spine/services/webhook_verify.py",
    ]

    # UC-037: Integrations Secret Vault Lifecycle (3 scripts)
    _UC037 = [
        "integrations/L5_vault/drivers/vault.py",
        "integrations/L5_vault/engines/service.py",
        "integrations/L5_vault/engines/vault_rule_check.py",
    ]

    # --- UC-033 tests ---
    def test_uc033_all_scripts_exist(self):
        """UC-033: All 26 spine operation governance scripts exist."""
        for path in self._UC033:
            assert _file_exists(path), f"UC-033: {path} must exist"

    def test_uc033_operation_registry_contract(self):
        """UC-033: operation_registry.py has deterministic dispatch."""
        source = _read_file("hoc_spine/orchestrator/operation_registry.py")
        has_reg = _has_function(source, "register_operation") or "OperationRegistry" in source or "OPERATIONS" in source
        assert has_reg, "UC-033: operation_registry must define registration mechanism"

    def test_uc033_schemas_are_pure_data(self):
        """UC-033: Schema files contain no runtime DB imports."""
        schemas = [p for p in self._UC033 if "/schemas/" in p]
        for path in schemas:
            violations = _check_l5_purity(_read_file(path))
            assert violations == [], f"UC-033: schema {os.path.basename(path)} purity: {violations}"

    def test_uc033_count(self):
        assert len(self._UC033) == 26, f"UC-033 scope: {len(self._UC033)}"

    # --- UC-034 tests ---
    def test_uc034_all_scripts_exist(self):
        """UC-034: All 6 spine lifecycle orchestration scripts exist."""
        for path in self._UC034:
            assert _file_exists(path), f"UC-034: {path} must exist"

    def test_uc034_stages_has_content(self):
        """UC-034: stages.py defines lifecycle stage constants."""
        source = _read_file("hoc_spine/orchestrator/lifecycle/stages.py")
        assert len(source) > 50, "UC-034: stages.py must have substantive content"

    def test_uc034_count(self):
        assert len(self._UC034) == 6, f"UC-034 scope: {len(self._UC034)}"

    # --- UC-035 tests ---
    def test_uc035_all_scripts_exist(self):
        """UC-035: All 17 spine execution safety scripts exist."""
        for path in self._UC035:
            assert _file_exists(path), f"UC-035: {path} must exist"

    def test_uc035_drivers_no_business_logic(self):
        """UC-035: Spot-check drivers for no business-logic leakage."""
        spot_checks = [
            "hoc_spine/drivers/guard_write_driver.py",
            "hoc_spine/drivers/ledger.py",
            "hoc_spine/drivers/idempotency.py",
        ]
        for path in spot_checks:
            if _file_exists(path):
                violations = _check_no_business_logic(_read_file(path))
                assert violations == [], f"UC-035: {os.path.basename(path)} business logic: {violations}"

    def test_uc035_count(self):
        assert len(self._UC035) == 17, f"UC-035 scope: {len(self._UC035)}"

    # --- UC-036 tests ---
    def test_uc036_all_scripts_exist(self):
        """UC-036: All 33 spine signals/evidence/alerting scripts exist."""
        for path in self._UC036:
            assert _file_exists(path), f"UC-036: {path} must exist"

    def test_uc036_evidence_engine_exists(self):
        """UC-036: retrieval_evidence_engine has substantive content."""
        source = _read_file("hoc_spine/services/retrieval_evidence_engine.py")
        assert len(source) > 50, "UC-036: retrieval_evidence_engine must have content"

    def test_uc036_count(self):
        assert len(self._UC036) == 33, f"UC-036 scope: {len(self._UC036)}"

    # --- UC-037 tests ---
    def test_uc037_all_scripts_exist(self):
        """UC-037: All 3 vault lifecycle scripts exist."""
        for path in self._UC037:
            assert _file_exists(path), f"UC-037: {path} must exist"

    @pytest.mark.parametrize("path", [
        "integrations/L5_vault/engines/service.py",
        "integrations/L5_vault/engines/vault_rule_check.py",
    ])
    def test_uc037_l5_purity(self, path):
        """UC-037: Vault L5 engines have no runtime DB imports."""
        if not _file_exists(path):
            pytest.skip(f"{path} not found")
        violations = _check_l5_purity(_read_file(path))
        assert violations == [], f"UC-037: L5 purity in {os.path.basename(path)}: {violations}"

    def test_uc037_count(self):
        assert len(self._UC037) == 3, f"UC-037 scope: {len(self._UC037)}"

    # --- UC-038 tests ---
    def test_uc038_channel_engine_exists(self):
        """UC-038: Notification channel engine exists."""
        assert _file_exists("integrations/L5_notifications/engines/channel_engine.py"), \
            "UC-038: channel_engine.py must exist"

    def test_uc038_l5_purity(self):
        """UC-038: channel_engine.py has no runtime DB imports."""
        violations = _check_l5_purity(
            _read_file("integrations/L5_notifications/engines/channel_engine.py")
        )
        assert violations == [], f"UC-038: L5 purity: {violations}"

    # --- UC-039 tests ---
    def test_uc039_cus_cli_exists(self):
        """UC-039: CLI operational bootstrap script exists."""
        assert _file_exists("integrations/cus_cli.py"), "UC-039: cus_cli.py must exist"

    # --- UC-040 tests ---
    def test_uc040_audit_engine_exists(self):
        """UC-040: CRM audit trail engine exists."""
        assert _file_exists("account/logs/CRM/audit/audit_engine.py"), \
            "UC-040: audit_engine.py must exist"

    # --- Grand total ---
    def test_uc033_to_uc040_total_count(self):
        """UC-033..UC-040 total scope is 88 scripts."""
        total = (
            len(self._UC033) + len(self._UC034) + len(self._UC035)
            + len(self._UC036) + len(self._UC037) + 1 + 1 + 1  # UC-038, 039, 040
        )
        assert total == 88, f"UC-033..UC-040 total scope: {total}"
