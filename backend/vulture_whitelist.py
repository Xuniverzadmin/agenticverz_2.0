# Vulture Whitelist — PIN-520 Dead Code Audit
# These items are intentionally used but vulture cannot detect their usage.
#
# Categories:
# 1. TYPE_CHECKING imports used in string literal type hints
# 2. Forward reference imports for circular import avoidance
# 3. Protocol method parameters (required by interface contract)

# =============================================================================
# TYPE_CHECKING Imports (used in quoted type hints)
# =============================================================================

# threshold_engine.py: Used in type hints for __init__ and method signatures
ThresholdDriver  # type: ignore
ThresholdDriverSync  # type: ignore
LimitSnapshot  # type: ignore

# =============================================================================
# Forward Reference Imports (circular import avoidance pattern)
# =============================================================================

# engine.py: Imported at end of file, used in quoted type hints throughout
CheckpointStore  # type: ignore
GoldenRecorder  # type: ignore
PlannerSandbox  # type: ignore

# =============================================================================
# Protocol Method Parameters (required by interface contract)
# =============================================================================

# McpPolicyChecker.check_tool_invocation: Protocol defines required signature
# The parameter is part of the interface even if default impl doesn't use it
# (Handled in code by adding logging for high-risk tools)
