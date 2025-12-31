# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Plan structure inspection
# Callers: runtime API
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Plan System

# Plan Safety Inspector
# Validates plans before execution to prevent dangerous operations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

logger = logging.getLogger("nova.utils.plan_inspector")

# Configuration from environment
MAX_PLAN_STEPS = int(os.getenv("MAX_PLAN_STEPS", "25"))
MAX_LOOP_ITERATIONS = int(os.getenv("MAX_LOOP_ITERATIONS", "10"))
MAX_ESTIMATED_COST_CENTS = int(os.getenv("MAX_ESTIMATED_COST_CENTS", "10000"))  # $100 default

# Forbidden domains (extend via config or DB)
FORBIDDEN_DOMAINS: Set[str] = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "169.254.169.254",  # AWS metadata
    "metadata.google.internal",  # GCP metadata
    "internal",
    "local",
}

# Additional forbidden patterns from environment
_extra_forbidden = os.getenv("FORBIDDEN_DOMAINS", "")
if _extra_forbidden:
    FORBIDDEN_DOMAINS.update(d.strip() for d in _extra_forbidden.split(",") if d.strip())

# Allowed skills (whitelist approach)
ALLOWED_SKILLS: Set[str] = {
    "http_call",
    "calendar_write",
    "llm_invoke",
    "json_transform",
    "postgres_query",
}


@dataclass
class PlanValidationError:
    """A single validation error."""

    code: str
    message: str
    step_id: Optional[str] = None
    severity: str = "error"  # error, warning


@dataclass
class PlanValidationResult:
    """Result of plan validation."""

    valid: bool
    errors: List[PlanValidationError] = field(default_factory=list)
    warnings: List[PlanValidationError] = field(default_factory=list)

    def add_error(self, code: str, message: str, step_id: Optional[str] = None):
        self.errors.append(PlanValidationError(code, message, step_id, "error"))
        self.valid = False

    def add_warning(self, code: str, message: str, step_id: Optional[str] = None):
        self.warnings.append(PlanValidationError(code, message, step_id, "warning"))


def extract_urls_from_params(params: Dict[str, Any]) -> List[str]:
    """Extract all URLs from skill parameters."""
    urls = []

    def _extract(obj, depth=0):
        if depth > 10:  # Prevent infinite recursion
            return
        if isinstance(obj, str):
            if obj.startswith("http://") or obj.startswith("https://"):
                urls.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                _extract(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                _extract(item, depth + 1)

    _extract(params)
    return urls


def is_domain_forbidden(url: str) -> tuple[bool, str]:
    """Check if a URL targets a forbidden domain.

    Returns:
        Tuple of (is_forbidden: bool, domain: str)
    """
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        host_lower = host.lower()

        # Check exact matches
        if host_lower in FORBIDDEN_DOMAINS:
            return True, host

        # Check if it's a private IP range
        if host_lower.startswith("10.") or host_lower.startswith("192.168."):
            return True, host

        # Check 172.16-31.x.x range
        if host_lower.startswith("172."):
            try:
                second_octet = int(host_lower.split(".")[1])
                if 16 <= second_octet <= 31:
                    return True, host
            except (ValueError, IndexError):
                pass

        # Check for internal domain patterns
        for forbidden in FORBIDDEN_DOMAINS:
            if host_lower.endswith(f".{forbidden}"):
                return True, host

        return False, host

    except Exception:
        return False, url


def validate_step(step: Dict[str, Any], result: PlanValidationResult):
    """Validate a single plan step."""
    step_id = step.get("step_id", "unknown")
    skill = step.get("skill", "")
    params = step.get("params", {})

    # Check skill is allowed
    if skill and skill not in ALLOWED_SKILLS:
        result.add_error("UNKNOWN_SKILL", f"Skill '{skill}' is not in the allowed list", step_id)

    # Check for forbidden URLs in http_call
    if skill == "http_call":
        urls = extract_urls_from_params(params)
        for url in urls:
            is_forbidden, domain = is_domain_forbidden(url)
            if is_forbidden:
                result.add_error("FORBIDDEN_TARGET", f"URL targets forbidden domain: {domain}", step_id)

    # Check for dangerous LLM prompts
    if skill == "llm_invoke":
        messages = params.get("messages", [])
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                # Check for prompt injection patterns
                if "ignore previous instructions" in content.lower():
                    result.add_warning("SUSPICIOUS_PROMPT", "LLM prompt contains suspicious pattern", step_id)

    # Check for loop configurations
    loop_config = step.get("loop", {})
    if loop_config:
        max_iter = loop_config.get("max_iterations", 1)
        if max_iter > MAX_LOOP_ITERATIONS:
            result.add_error(
                "EXCESSIVE_LOOP", f"Loop max_iterations ({max_iter}) exceeds limit ({MAX_LOOP_ITERATIONS})", step_id
            )


def validate_plan(plan: Dict[str, Any], agent_budget_cents: int = 0) -> PlanValidationResult:
    """Validate a complete plan before execution.

    Args:
        plan: The plan dictionary from the planner
        agent_budget_cents: The agent's remaining budget (0 = unlimited)

    Returns:
        PlanValidationResult with errors and warnings
    """
    result = PlanValidationResult(valid=True)

    # Check plan structure
    if not isinstance(plan, dict):
        result.add_error("INVALID_PLAN", "Plan must be a dictionary")
        return result

    steps = plan.get("steps", [])

    # Check step count
    if len(steps) > MAX_PLAN_STEPS:
        result.add_error("TOO_MANY_STEPS", f"Plan has {len(steps)} steps, maximum is {MAX_PLAN_STEPS}")

    if len(steps) == 0:
        result.add_warning("EMPTY_PLAN", "Plan has no steps")

    # Check estimated cost
    metadata = plan.get("metadata", {})
    estimated_cost = metadata.get("estimated_cost_cents", 0)

    # If planner provided token counts, estimate cost
    if not estimated_cost:
        input_tokens = metadata.get("input_tokens", 0)
        output_tokens = metadata.get("output_tokens", 0)
        if input_tokens or output_tokens:
            # Rough estimate: assume each step might use similar tokens
            step_count = max(1, len(steps))
            estimated_cost = int((input_tokens * 0.003 + output_tokens * 0.015) * step_count)

    if estimated_cost > MAX_ESTIMATED_COST_CENTS:
        result.add_error(
            "COST_EXCEEDS_LIMIT",
            f"Estimated cost ({estimated_cost} cents) exceeds limit ({MAX_ESTIMATED_COST_CENTS} cents)",
        )

    # Check against agent budget if set
    if agent_budget_cents > 0 and estimated_cost > agent_budget_cents:
        result.add_error(
            "INSUFFICIENT_BUDGET",
            f"Estimated cost ({estimated_cost} cents) exceeds agent budget ({agent_budget_cents} cents)",
        )

    # Validate each step
    seen_step_ids = set()
    for step in steps:
        step_id = step.get("step_id", "")

        # Check for duplicate step IDs
        if step_id and step_id in seen_step_ids:
            result.add_warning("DUPLICATE_STEP_ID", f"Duplicate step_id: {step_id}", step_id)
        seen_step_ids.add(step_id)

        validate_step(step, result)

    # Check for circular dependencies
    dependencies = {}
    for step in steps:
        step_id = step.get("step_id", "")
        deps = step.get("depends_on", [])
        dependencies[step_id] = set(deps) if isinstance(deps, list) else set()

    # Simple cycle detection
    for step_id, deps in dependencies.items():
        visited = set()
        to_visit = list(deps)
        while to_visit:
            current = to_visit.pop()
            if current == step_id:
                result.add_error(
                    "CIRCULAR_DEPENDENCY", f"Circular dependency detected involving step {step_id}", step_id
                )
                break
            if current not in visited:
                visited.add(current)
                to_visit.extend(dependencies.get(current, []))

    return result


def inspect_plan(plan: Dict[str, Any], agent_budget_cents: int = 0) -> Dict[str, Any]:
    """Inspect a plan and return validation results.

    Args:
        plan: The plan dictionary
        agent_budget_cents: Agent's remaining budget

    Returns:
        Dict with 'valid', 'errors', and 'warnings' keys

    Raises:
        Exception if plan has critical errors and should be rejected
    """
    result = validate_plan(plan, agent_budget_cents)

    if result.errors:
        logger.warning(
            "plan_validation_failed",
            extra={
                "plan_id": plan.get("plan_id", "unknown"),
                "error_count": len(result.errors),
                "errors": [{"code": e.code, "message": e.message} for e in result.errors],
            },
        )
    elif result.warnings:
        logger.info(
            "plan_validation_warnings",
            extra={
                "plan_id": plan.get("plan_id", "unknown"),
                "warning_count": len(result.warnings),
            },
        )

    return {
        "valid": result.valid,
        "errors": [{"code": e.code, "message": e.message, "step_id": e.step_id} for e in result.errors],
        "warnings": [{"code": w.code, "message": w.message, "step_id": w.step_id} for w in result.warnings],
    }
