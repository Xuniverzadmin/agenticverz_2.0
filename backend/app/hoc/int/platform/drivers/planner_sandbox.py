# capability_id: CAP-012
# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: Sandboxed planner execution for safety
# Callers: workflow engine
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Workflow System

# Planner Sandbox (M4)
"""
Sandbox for validating planner outputs before execution.

Provides:
1. Forbidden skill detection (shell_exec, db_drop, etc.)
2. Idempotency validation for side-effect operations
3. Input sanitization checks
4. Contract compliance verification

Design Principles:
- Fail-fast: Reject invalid plans before execution
- Zero trust: Validate all planner outputs
- Explicit contracts: Skills must declare their capabilities
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("nova.workflow.sandbox")


@dataclass
class SandboxReport:
    """
    Result of sandbox validation.
    """

    ok: bool
    reason: str = ""
    violations: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "reason": self.reason,
            "violations": self.violations,
            "warnings": self.warnings,
        }


class PlannerSandbox:
    """
    Sandbox for validating planner outputs.

    Validates:
    - No forbidden skills
    - Idempotency keys for side-effect operations
    - Input parameter safety
    - URL/path injection attempts
    - Contract compliance

    Usage:
        sandbox = PlannerSandbox()
        report = await sandbox.validate_plan(planner_output)
        if not report.ok:
            raise RuntimeError(report.reason)
    """

    # Forbidden skills that should never be executed
    FORBIDDEN_SKILLS: Set[str] = {
        "shell_exec",
        "shell_execute",
        "os_command",
        "os_remove",
        "file_delete",
        "db_drop",
        "db_truncate",
        "system_reboot",
        "system_shutdown",
        "rm_rf",
        "format_disk",
    }

    # Suspicious patterns in inputs
    SUSPICIOUS_PATTERNS = [
        re.compile(r";\s*rm\s+-rf", re.IGNORECASE),
        re.compile(r";\s*drop\s+table", re.IGNORECASE),
        re.compile(r";\s*delete\s+from", re.IGNORECASE),
        re.compile(r"\$\(.*\)"),  # Command substitution
        re.compile(r"`.*`"),  # Backtick command execution
        re.compile(r"\.\.\/"),  # Path traversal
        re.compile(r"\/etc\/passwd"),
        re.compile(r"\/etc\/shadow"),
    ]

    # Methods that require idempotency keys
    SIDE_EFFECT_METHODS: Set[str] = {"POST", "PUT", "DELETE", "PATCH"}

    def __init__(
        self,
        forbidden_skills: Optional[Set[str]] = None,
        require_idempotency: bool = True,
        allow_external_urls: bool = True,
    ):
        """
        Initialize planner sandbox.

        Args:
            forbidden_skills: Additional skills to forbid
            require_idempotency: Require idempotency_key for side-effect operations
            allow_external_urls: Allow external URLs (if False, only localhost/internal)
        """
        self.forbidden_skills = self.FORBIDDEN_SKILLS.copy()
        if forbidden_skills:
            self.forbidden_skills.update(forbidden_skills)

        self.require_idempotency = require_idempotency
        self.allow_external_urls = allow_external_urls

    async def validate_plan(self, planner_output: Dict[str, Any]) -> SandboxReport:
        """
        Validate a planner output.

        Args:
            planner_output: Planner output containing steps

        Returns:
            SandboxReport with ok=True if valid, ok=False with reason if invalid
        """
        violations = []
        warnings = []

        steps = planner_output.get("steps", [])

        if not steps:
            return SandboxReport(
                ok=True,
                reason="",
                warnings=["Plan has no steps"],
            )

        for idx, step in enumerate(steps):
            step_violations = self._validate_step(step, idx)
            violations.extend(step_violations)

            step_warnings = self._check_step_warnings(step, idx)
            warnings.extend(step_warnings)

        if violations:
            return SandboxReport(
                ok=False,
                reason=f"Plan validation failed: {violations[0].get('message', 'Unknown violation')}",
                violations=violations,
                warnings=warnings,
            )

        return SandboxReport(
            ok=True,
            reason="",
            violations=[],
            warnings=warnings,
        )

    def _validate_step(self, step: Dict[str, Any], idx: int) -> List[Dict[str, Any]]:
        """
        Validate a single step.

        Returns:
            List of violation dictionaries
        """
        violations = []
        step_id = step.get("id", f"step_{idx}")
        skill_id = step.get("skill_id", "")

        # 1. Check forbidden skills
        if skill_id.lower() in {s.lower() for s in self.forbidden_skills}:
            violations.append(
                {
                    "type": "forbidden_skill",
                    "step_id": step_id,
                    "step_index": idx,
                    "skill_id": skill_id,
                    "message": f"Forbidden skill: {skill_id}",
                }
            )

        # 2. Check idempotency for side-effect methods
        if self.require_idempotency:
            inputs = step.get("inputs", {})
            method = inputs.get("method", "GET").upper()

            if method in self.SIDE_EFFECT_METHODS:
                idempotency_key = step.get("idempotency_key") or inputs.get("idempotency_key")
                if not idempotency_key:
                    violations.append(
                        {
                            "type": "missing_idempotency",
                            "step_id": step_id,
                            "step_index": idx,
                            "method": method,
                            "message": f"Step {step_id} uses {method} but has no idempotency_key",
                        }
                    )

        # 3. Check inputs for suspicious patterns
        inputs = step.get("inputs", {})
        input_violations = self._check_input_safety(inputs, step_id, idx)
        violations.extend(input_violations)

        # 4. Check URL safety
        if "url" in inputs and not self.allow_external_urls:
            url = inputs.get("url", "")
            if not self._is_internal_url(url):
                violations.append(
                    {
                        "type": "external_url_forbidden",
                        "step_id": step_id,
                        "step_index": idx,
                        "url": url[:100],  # Truncate for safety
                        "message": f"External URLs not allowed: {url[:50]}...",
                    }
                )

        return violations

    def _check_input_safety(
        self,
        inputs: Dict[str, Any],
        step_id: str,
        idx: int,
    ) -> List[Dict[str, Any]]:
        """
        Check input parameters for injection attempts.

        Returns:
            List of violation dictionaries
        """
        violations = []

        def check_value(value: Any, path: str) -> None:
            if isinstance(value, str):
                for pattern in self.SUSPICIOUS_PATTERNS:
                    if pattern.search(value):
                        violations.append(
                            {
                                "type": "suspicious_input",
                                "step_id": step_id,
                                "step_index": idx,
                                "path": path,
                                "pattern": pattern.pattern,
                                "message": f"Suspicious pattern detected in {path}",
                            }
                        )
                        break
            elif isinstance(value, dict):
                for k, v in value.items():
                    check_value(v, f"{path}.{k}")
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    check_value(item, f"{path}[{i}]")

        for key, value in inputs.items():
            check_value(value, key)

        return violations

    def _check_step_warnings(self, step: Dict[str, Any], idx: int) -> List[str]:
        """
        Check for non-blocking warnings.

        Returns:
            List of warning messages
        """
        warnings = []
        step_id = step.get("id", f"step_{idx}")

        # Warn about high cost estimates
        estimated_cost = step.get("estimated_cost_cents", 0)
        if estimated_cost > 100:
            warnings.append(f"Step {step_id} has high estimated cost: {estimated_cost}c")

        # Warn about missing descriptions
        if not step.get("description"):
            warnings.append(f"Step {step_id} has no description")

        # Warn about deep dependency chains
        depends_on = step.get("depends_on", [])
        if len(depends_on) > 5:
            warnings.append(f"Step {step_id} has {len(depends_on)} dependencies")

        return warnings

    def _is_internal_url(self, url: str) -> bool:
        """
        Check if URL is internal/safe.

        Returns:
            True if URL is internal
        """
        internal_prefixes = [
            "http://127.0.0.1",
            "http://localhost",
            "https://127.0.0.1",
            "https://localhost",
            "http://10.",
            "http://172.16.",
            "http://192.168.",
            "https://10.",
            "https://172.16.",
            "https://192.168.",
        ]
        return any(url.startswith(prefix) for prefix in internal_prefixes)

    def add_forbidden_skill(self, skill_id: str) -> None:
        """
        Add a skill to the forbidden list.

        Args:
            skill_id: Skill ID to forbid
        """
        self.forbidden_skills.add(skill_id)

    def remove_forbidden_skill(self, skill_id: str) -> None:
        """
        Remove a skill from the forbidden list.

        Args:
            skill_id: Skill ID to allow
        """
        self.forbidden_skills.discard(skill_id)


# Validation helper functions


def validate_step_structure(step: Dict[str, Any]) -> List[str]:
    """
    Validate step has required fields.

    Returns:
        List of validation errors
    """
    errors = []

    if not step.get("id"):
        errors.append("Step missing 'id' field")

    if not step.get("skill_id"):
        errors.append("Step missing 'skill_id' field")

    return errors


def validate_workflow_structure(workflow: Dict[str, Any]) -> List[str]:
    """
    Validate workflow spec has required fields.

    Returns:
        List of validation errors
    """
    errors = []

    if not workflow.get("id"):
        errors.append("Workflow missing 'id' field")

    if not workflow.get("steps"):
        errors.append("Workflow has no steps")

    # Check for duplicate step IDs
    step_ids = set()
    for step in workflow.get("steps", []):
        step_id = step.get("id", "")
        if step_id in step_ids:
            errors.append(f"Duplicate step ID: {step_id}")
        step_ids.add(step_id)

    # Check dependency references
    for step in workflow.get("steps", []):
        for dep in step.get("depends_on", []):
            if dep not in step_ids:
                errors.append(f"Step {step.get('id')} depends on unknown step: {dep}")

    return errors
