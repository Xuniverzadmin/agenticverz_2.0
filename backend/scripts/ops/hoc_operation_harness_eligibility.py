#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: hoc/cus
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Generate operation→harness eligibility map from hoc_spine handler registry.
# Allowed Imports: stdlib only
# Forbidden Imports: app.*
# artifact_class: CODE

"""
HOC Operation Harness Eligibility Generator (Heuristic v2)

Builds a YAML map of every registered hoc_spine operation:
  operation -> handler -> recommended harnesses (+ confidence + evidence)

Heuristic v2 is static-evidence based:
- parses handler registry registrations (AST)
- extracts evidence from handler source (AST + line regexes)
- applies conservative rules (prefer low confidence over guessing)

Output:
  docs/architecture/hoc/OPERATION_HARNESS_ELIGIBILITY_V1.yaml
"""

from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


RE_REGISTER = re.compile(r"\bregistry\.register\b")

# Evidence patterns (regex, harness_tag, label)
# These are intentionally conservative; avoid turning generic identifiers into harness requirements.
EVIDENCE_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    # Governance job / contract lifecycle
    (re.compile(r"\bcontract_engine\b|\bContract(State|Service|StateMachine)\b"), "governance_job", "contract_engine"),
    (re.compile(r"\bgovernance_orchestrator\b|\bJobStateMachine\b"), "governance_job", "governance_orchestrator"),
    # Lifecycle stages (onboarding/offboarding/migration authority)
    (
        re.compile(r"\borchestrator\.lifecycle\b|\blifecycle_stages\b|\bonboarding_engine\b|\boffboarding_engine\b"),
        "lifecycle_stages",
        "lifecycle_stage",
    ),
    # RAC (run audit contract)
    (re.compile(r"\bget_audit_store\b|\bAuditExpectation\b|\bDomainAck\b|\bcreate_run_expectations\b"), "rac", "rac_models/store"),
    (re.compile(r"\badd_ack\b|\badd_expectations\b|\breconcile\b"), "rac", "rac_calls"),
    (re.compile(r"\brun_id\b"), "rac", "run_id"),
    # Workflow (staged/async execution)
    (re.compile(r"\benqueue\b|\benqueue_|\bjob_queue\b|\bscheduler\b|\bworkers?\b|\bworker_|\bworkers_"), "workflow", "job/worker wording"),
    # Control plane
    (re.compile(r"\bkillswitch\b|\bkillswitch_"), "control_plane", "killswitch"),
    (re.compile(r"\bcircuit_breaker\b|\bcircuit_breaker_"), "control_plane", "circuit_breaker"),
]


@dataclass(frozen=True)
class OperationRegistration:
    operation: str
    handler_expr: str
    file: Path
    line: int


@dataclass
class EvidenceHit:
    harness: str
    label: str
    line: int
    text: str


def _module_to_path(module: str) -> Path | None:
    """
    Convert an import module like `app.hoc.cus.foo.bar` into a repo path.

    This generator is scoped to the monorepo layout where `app.*` lives under `backend/app/`.
    """
    mod = module.strip()
    if not mod:
        return None
    if mod.startswith("app."):
        mod = mod[len("app.") :]
        return Path("backend") / "app" / Path(mod.replace(".", "/") + ".py")
    return None


def _imported_from_module(tree: ast.AST, symbol: str) -> str | None:
    """
    Best-effort: locate `from <module> import <symbol>` anywhere in the file (including inside functions).

    Returns the module string if found.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if not node.module:
            continue
        for alias in node.names:
            bound = alias.asname or alias.name
            if bound == symbol:
                return node.module
    return None


def _iter_py_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        yield path


def _safe_parse(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return None


def collect_registrations(handlers_root: Path) -> list[OperationRegistration]:
    regs: list[OperationRegistration] = []
    for path in _iter_py_files(handlers_root):
        src = path.read_text(encoding="utf-8")
        if not RE_REGISTER.search(src):
            continue
        tree = _safe_parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "register":
                continue
            if not node.args:
                continue
            arg0 = node.args[0]
            if not isinstance(arg0, ast.Constant) or not isinstance(arg0.value, str):
                continue
            operation = arg0.value
            handler_expr = "<?>"
            if len(node.args) >= 2:
                handler_expr = ast.unparse(node.args[1])
            regs.append(OperationRegistration(operation=operation, handler_expr=handler_expr, file=path, line=node.lineno))
    return regs


def _extract_handler_class_name(handler_expr: str) -> str | None:
    """
    Extract handler class name from an expression like `FooHandler()` or `pkg.FooHandler()`.

    Returns None for non-trivial expressions (variables, calls, subscripts).
    """
    # Simple `Name()` call.
    m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\(\)", handler_expr.strip())
    if m:
        return m.group(1)
    # Qualified `pkg.Name()` call.
    m = re.fullmatch(r"(?:[A-Za-z_][A-Za-z0-9_]*\.)+([A-Za-z_][A-Za-z0-9_]*)\(\)", handler_expr.strip())
    if m:
        return m.group(1)
    return None


def _resolve_alias_to_handler_class(tree: ast.AST, alias_name: str, before_line: int) -> str | None:
    """
    Resolve a registration like `registry.register("op", handler)` where earlier in register():
      handler = FooHandler()

    Only supports simple Name assignments inside a `def register(...)` function.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "register":
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign):
                continue
            if getattr(stmt, "lineno", 10**9) >= before_line:
                continue
            if len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            if not isinstance(target, ast.Name) or target.id != alias_name:
                continue
            if not isinstance(stmt.value, ast.Call):
                continue
            try:
                expr = ast.unparse(stmt.value)
            except Exception:
                continue
            resolved = _extract_handler_class_name(expr)
            if resolved:
                return resolved
    return None


def _class_execute_span(tree: ast.AST, class_name: str) -> tuple[int, int] | None:
    """Return (start_line, end_line) for the handler's execute() method if available."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == "execute":
                    if getattr(stmt, "lineno", None) and getattr(stmt, "end_lineno", None):
                        return int(stmt.lineno), int(stmt.end_lineno)  # type: ignore[arg-type]
                    # Fallback if end_lineno missing.
                    return int(stmt.lineno), int(stmt.lineno)
    return None


def extract_evidence(path: Path, start_line: int | None = None, end_line: int | None = None) -> list[EvidenceHit]:
    hits: list[EvidenceHit] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    start = 1 if start_line is None else max(1, start_line)
    end = len(lines) if end_line is None else min(len(lines), end_line)
    for idx in range(start, end + 1):
        line = lines[idx - 1]
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for pattern, harness, label in EVIDENCE_PATTERNS:
            if pattern.search(line):
                hits.append(EvidenceHit(harness=harness, label=label, line=idx, text=line.strip()))
    return hits


def _op_read_only(operation: str) -> bool:
    return (
        operation.endswith(".query")
        or operation.endswith(".health")
        or operation.endswith(".status")
        or operation.endswith("_query")
        or operation.startswith("system.health")
    )


def recommend_harnesses(operation: str, evidence: list[EvidenceHit]) -> tuple[list[str], str, str, list[dict]]:
    """Return (harnesses, confidence, reason, evidence_list)."""
    harnesses: list[str] = []
    evidence_out: list[dict] = []

    # Always collect evidence metadata for transparency (but cap it).
    for h in evidence[:12]:
        evidence_out.append(
            {
                "harness": h.harness,
                "label": h.label,
                "line": h.line,
                "text": h.text[:160],
            }
        )

    # Strong name-based signals.
    if operation.startswith("governance.") or ".approval" in operation or operation.endswith(".approval"):
        harnesses.append("governance_job")
    if "killswitch" in operation or operation.startswith("controls.killswitch") or operation.startswith("killswitch."):
        harnesses.append("control_plane")
    if "circuit_breaker" in operation:
        harnesses.append("control_plane")
    if operation.endswith(".workers") or ".workers" in operation or operation.endswith(".sandbox_execute") or operation.endswith(".simulate"):
        harnesses.append("workflow")

    # Evidence-based signals (prefer these).
    for hit in evidence:
        if hit.harness == "governance_job" and "governance_job" not in harnesses:
            harnesses.append("governance_job")
        if hit.harness == "control_plane" and "control_plane" not in harnesses:
            harnesses.append("control_plane")
        if hit.harness == "workflow" and "workflow" not in harnesses:
            harnesses.append("workflow")

    # RAC is special: only recommend when there is explicit audit_store/rac usage,
    # or the operation is the capture entrypoint.
    has_rac_evidence = any(h.harness == "rac" and h.label in ("rac_models/store", "rac_calls") for h in evidence)
    if operation == "logs.capture" or has_rac_evidence:
        harnesses.append("rac")

    # Normalize ordering for stability.
    order = ["governance_job", "lifecycle_stages", "workflow", "control_plane", "rac"]
    harnesses = [h for h in order if h in set(harnesses)]

    read_only = _op_read_only(operation)
    if not harnesses:
        conf = "medium" if read_only else "low"
        reason = "read-only operation" if read_only else "write/side-effects unclear; requires manual classification"
        return [], conf, reason, evidence_out

    # Confidence:
    # - high: harness implied by operation name and corroborated by evidence (or control-plane by name alone)
    # - medium: implied by name OR evidence
    # - low: only weak evidence (e.g. run_id mention) or mixed signals
    has_governance_evidence = any(
        h.harness == "governance_job" and h.label in ("contract_engine", "governance_orchestrator") for h in evidence
    )
    has_workflow_evidence = any(h.harness == "workflow" for h in evidence)
    has_control_evidence = any(h.harness == "control_plane" for h in evidence)
    has_control_name = "control_plane" in harnesses and ("killswitch" in operation or "circuit_breaker" in operation)

    if "governance_job" in harnesses and (operation.startswith("governance.") or ".approval" in operation) and has_governance_evidence:
        return harnesses, "high", "governance operation corroborated by contract/job evidence", evidence_out
    if "governance_job" in harnesses and (operation.startswith("governance.") or ".approval" in operation):
        return harnesses, "medium", "governance-like operation (name-based)", evidence_out
    if "lifecycle_stages" in harnesses:
        return harnesses, "medium", "lifecycle stage authority appears in handler code", evidence_out
    if has_control_name:
        return harnesses, "high", "control-plane operation (name-based)", evidence_out
    if "workflow" in harnesses and (operation.endswith(".workers") or operation.endswith(".sandbox_execute") or operation.endswith(".simulate")):
        return harnesses, "medium", "workflow-like operation (name-based)", evidence_out
    if has_control_evidence and "control_plane" in harnesses:
        return harnesses, "medium", "static evidence suggests control-plane usage", evidence_out
    if has_governance_evidence or has_workflow_evidence or has_rac_evidence:
        return harnesses, "medium", "static evidence suggests harness usage", evidence_out

    return harnesses, "low", "weak signal only; manual review required", evidence_out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--handlers-root",
        default="backend/app/hoc/cus/hoc_spine/orchestrator/handlers",
        help="Root directory containing hoc_spine handlers.",
    )
    parser.add_argument(
        "--out",
        default="docs/architecture/hoc/OPERATION_HARNESS_ELIGIBILITY_V1.yaml",
        help="Output YAML path.",
    )
    args = parser.parse_args()

    handlers_root = Path(args.handlers_root)
    out_path = Path(args.out)

    regs = collect_registrations(handlers_root)
    by_prefix: dict[str, list[dict]] = {}

    for reg in regs:
        prefix = reg.operation.split(".", 1)[0]

        tree = _safe_parse(reg.file)
        class_name = _extract_handler_class_name(reg.handler_expr)
        if class_name is None and tree is not None:
            # Handle: handler = FooHandler(); registry.register("op", handler)
            m = re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", reg.handler_expr.strip())
            if m:
                class_name = _resolve_alias_to_handler_class(tree, m.group(0), reg.line)

        evidence_path = reg.file
        evidence_tree = tree

        span = _class_execute_span(evidence_tree, class_name) if (evidence_tree is not None and class_name) else None
        if span is None and evidence_tree is not None and class_name:
            # The handler might be imported inside the register() function (or module-level). Resolve and re-scan.
            imported_module = _imported_from_module(evidence_tree, class_name)
            imported_path = _module_to_path(imported_module) if imported_module else None
            if imported_path and imported_path.exists():
                resolved_tree = _safe_parse(imported_path)
                resolved_span = _class_execute_span(resolved_tree, class_name) if resolved_tree is not None else None
                if resolved_span is not None:
                    evidence_path = imported_path
                    evidence_tree = resolved_tree
                    span = resolved_span

        if span:
            ev_hits = extract_evidence(evidence_path, start_line=span[0], end_line=span[1])
            evidence_scope = "handler_execute"
        else:
            # Fallback: file-scoped evidence is noisy, so treat it as low-trust.
            ev_hits = []
            evidence_scope = "none"

        harnesses, confidence, reason, evidence_out = recommend_harnesses(reg.operation, ev_hits)
        if evidence_scope != "handler_execute" and confidence in ("high", "medium") and harnesses:
            # If we couldn't scope evidence to the handler itself, do not claim confidence.
            confidence = "low"
            reason = f"{reason} (no handler-level evidence; requires manual review)"

        by_prefix.setdefault(prefix, []).append(
            {
                "operation": reg.operation,
                "handler": f"{reg.file.as_posix()}:{reg.line}",
                "handler_expr": reg.handler_expr,
                "handler_class": class_name or None,
                "handler_impl": evidence_path.as_posix(),
                "evidence_scope": evidence_scope,
                "read_only": _op_read_only(reg.operation),
                "recommended_harnesses": harnesses,
                "confidence": confidence,
                "reason": reason,
                "evidence": evidence_out,
            }
        )

    # Stable ordering.
    for prefix in by_prefix:
        by_prefix[prefix] = sorted(by_prefix[prefix], key=lambda d: d["operation"])

    generated_at = datetime.now(timezone.utc).isoformat()

    # Hand-roll YAML to avoid non-stdlib dependencies (CI-friendly).
    lines: list[str] = []
    lines.append("# Generated file — do not hand-edit without regenerating.")
    lines.append(f"# Generated by: {Path(__file__).as_posix()}")
    lines.append(f"# Generated at: {generated_at}")
    lines.append("# Source scan: backend/app/hoc/cus/hoc_spine/orchestrator/handlers/**")
    lines.append("# Match: registry.register(\"<operation>\", <handler>)")
    lines.append("#")
    lines.append("# Baseline invariants (always true in HOC topology):")
    lines.append("# - L4 owns tx boundary (session/commit authority)")
    lines.append("# - operation_registry dispatch audit exists (system traceability)")
    lines.append("")
    lines.append("version: 2")
    lines.append(f"generated_at: \"{generated_at}\"")
    lines.append("source:")
    lines.append(f"  handlers_root: \"{handlers_root.as_posix()}\"")
    lines.append("  match: \"registry.register(<operation>, <handler>)\"")
    lines.append("baseline:")
    lines.append("  always: [l4_tx_boundary, dispatch_audit]")
    lines.append("harnesses:")
    lines.append("  l4_tx_boundary: \"L4 owns transaction/session/commit boundary\"")
    lines.append("  dispatch_audit: \"operation_registry dispatch record (system traceability)\"")
    lines.append("  governance_job: \"contract-backed, evidence-carrying state transition\"")
    lines.append("  lifecycle_stages: \"onboarding/offboarding/migration stage authority\"")
    lines.append("  workflow: \"long-running staged execution (job-like)\"")
    lines.append("  control_plane: \"killswitch/circuit breaker style immediate controls\"")
    lines.append("  rac: \"RAC expectations/acks (correlation-id audit contract)\"")
    lines.append("criteria:")
    lines.append("  heuristic: \"v2\"")
    lines.append("  note: \"Static-evidence is scoped to handler.execute() when possible; low-confidence items require manual review.\"")
    lines.append("domains:")

    def esc(s: str) -> str:
        return s.replace("\\\\", "/").replace("\"", "\\\"")

    for prefix in sorted(by_prefix):
        lines.append(f"  {prefix}:")
        for item in by_prefix[prefix]:
            lines.append(f"    - operation: \"{esc(item['operation'])}\"")
            lines.append(f"      handler: \"{esc(item['handler'])}\"")
            lines.append(f"      handler_expr: \"{esc(item['handler_expr'])}\"")
            if item.get("handler_class"):
                lines.append(f"      handler_class: \"{esc(item['handler_class'])}\"")
            lines.append(f"      handler_impl: \"{esc(item['handler_impl'])}\"")
            lines.append(f"      evidence_scope: \"{esc(item['evidence_scope'])}\"")
            lines.append(f"      read_only: {str(bool(item['read_only'])).lower()}")
            hs = item["recommended_harnesses"]
            if hs:
                lines.append("      recommended_harnesses: [%s]" % (", ".join(hs)))
            else:
                lines.append("      recommended_harnesses: []")
            lines.append(f"      confidence: {item['confidence']}")
            lines.append(f"      reason: \"{esc(item['reason'])}\"")
            ev = item["evidence"]
            if not ev:
                lines.append("      evidence: []")
            else:
                lines.append("      evidence:")
                for e in ev:
                    lines.append("        - harness: \"%s\"" % esc(e["harness"]))
                    lines.append("          label: \"%s\"" % esc(e["label"]))
                    lines.append("          line: %d" % int(e["line"]))
                    lines.append("          text: \"%s\"" % esc(e["text"]))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
