"""
Mypy Autofix Macros - Mechanical transforms for type safety.

These are deterministic, no-inference transforms:
- guard_optional: Insert None guards (assert or early return)
- cast_expr: Wrap expression in typing.cast()
- return_cast: Wrap return value in cast()
- callable_fix: Fix callable type annotations
- unreachable: Add unreachable assertion

Usage:
    from tools.mypy_autofix.macros import guard_optional, cast_expr
"""

from typing import Literal


def guard_optional(var: str, mode: Literal["assert", "return"] = "assert") -> str:
    """
    Generate a None guard for an Optional variable.

    Args:
        var: Variable name to guard
        mode: "assert" for assertion, "return" for early return

    Returns:
        Guard statement string
    """
    if mode == "assert":
        return f"assert {var} is not None"
    return f"if {var} is None:\n    return"


def cast_expr(expr: str, typ: str) -> str:
    """
    Wrap an expression in typing.cast().

    Args:
        expr: Expression to cast
        typ: Target type

    Returns:
        Cast expression string
    """
    return f"cast({typ}, {expr})"


def return_cast(expr: str, typ: str) -> str:
    """
    Wrap a return expression in cast().

    Args:
        expr: Expression being returned
        typ: Expected return type

    Returns:
        Return statement with cast
    """
    return f"return cast({typ}, {expr})"


def callable_fix(name: str) -> str:
    """
    Fix a callable type annotation.

    Args:
        name: Variable/parameter name

    Returns:
        Properly typed annotation
    """
    return f"{name}: Callable[..., Any]"


def unreachable() -> str:
    """
    Generate an unreachable assertion.

    Returns:
        Assertion statement for unreachable code
    """
    return 'raise AssertionError("unreachable")'


def bool_wrap(expr: str) -> str:
    """
    Wrap expression in bool() for no-any-return on bool functions.

    Args:
        expr: Expression to wrap

    Returns:
        bool() wrapped expression
    """
    return f"bool({expr})"


def int_wrap(expr: str) -> str:
    """
    Wrap expression in int() for no-any-return on int functions.

    Args:
        expr: Expression to wrap

    Returns:
        int() wrapped expression
    """
    return f"int({expr})"


def float_wrap(expr: str) -> str:
    """
    Wrap expression in float() for no-any-return on float functions.

    Args:
        expr: Expression to wrap

    Returns:
        float() wrapped expression
    """
    return f"float({expr})"


def list_annotation(var: str, elem_type: str = "Any") -> str:
    """
    Add explicit list type annotation.

    Args:
        var: Variable name
        elem_type: Element type (default: Any)

    Returns:
        Annotated variable declaration
    """
    return f"{var}: list[{elem_type}] = []"


def dict_annotation(var: str, key_type: str = "str", val_type: str = "Any") -> str:
    """
    Add explicit dict type annotation.

    Args:
        var: Variable name
        key_type: Key type (default: str)
        val_type: Value type (default: Any)

    Returns:
        Annotated variable declaration
    """
    return f"{var}: dict[{key_type}, {val_type}] = {{}}"


def add_all_export(names: list[str]) -> str:
    """
    Generate __all__ export list.

    Args:
        names: List of names to export

    Returns:
        __all__ declaration string
    """
    items = ", ".join(f'"{n}"' for n in names)
    return f"__all__ = [{items}]"


# =============================================================================
# SQLALCHEMY MACROS
# Fix .desc(), .ilike(), .like(), .asc() false positives
# =============================================================================


def sa_expr(expr: str) -> str:
    """
    Cast SQLAlchemy expression to Any to silence attr-defined.

    Args:
        expr: SQLAlchemy expression (e.g., column.desc())

    Returns:
        Cast wrapped expression
    """
    return f"cast(Any, {expr})"


def sa_column(col: str) -> str:
    """
    Cast column/instrumented attribute to SQLAlchemy expression.

    Args:
        col: Column reference

    Returns:
        Cast wrapped column
    """
    return f"cast(Any, {col})"


# =============================================================================
# PROMETHEUS MACROS
# Fix Counter/Histogram/Gauge stub limitations
# =============================================================================


def prom_metric(name: str) -> str:
    """
    Add Any annotation to Prometheus metric.

    Args:
        name: Metric variable name

    Returns:
        Annotated declaration
    """
    return f"{name}: Any"


def prom_metric_full(name: str, value: str) -> str:
    """
    Full Prometheus metric declaration with Any annotation.

    Args:
        name: Metric variable name
        value: Metric initialization (e.g., Counter(...))

    Returns:
        Annotated assignment
    """
    return f"{name}: Any = {value}"


# =============================================================================
# FASTAPI DEPENDS MACROS
# Fix Depends() -> Optional[T] false positives
# =============================================================================


def fastapi_dep_guard(var: str) -> str:
    """
    Generate assertion for FastAPI dependency.

    Args:
        var: Dependency variable name

    Returns:
        Assertion statement
    """
    return f"assert {var} is not None"


def fastapi_dep_annotation(var: str, typ: str) -> str:
    """
    Annotate FastAPI dependency as non-Optional.

    Args:
        var: Variable name
        typ: Expected type

    Returns:
        Type annotation
    """
    return f"{var}: {typ}"


# =============================================================================
# PYDANTIC BOUNDARY MACROS
# Fix v1/v2 .dict()/.parse_obj() boundary typing
# =============================================================================


def pydantic_in(model: str, data: str) -> str:
    """
    Pydantic v2 model validation.

    Args:
        model: Model class name
        data: Data to validate

    Returns:
        model_validate call
    """
    return f"{model}.model_validate({data})"


def pydantic_out(expr: str, typ: str = "dict[str, Any]") -> str:
    """
    Cast Pydantic output at boundary.

    Args:
        expr: Pydantic expression (e.g., model.dict())
        typ: Target type

    Returns:
        Cast wrapped expression
    """
    return f"cast({typ}, {expr})"


def pydantic_dict_cast(expr: str) -> str:
    """
    Cast .dict() output to dict[str, Any].

    Args:
        expr: Expression calling .dict()

    Returns:
        Cast wrapped expression
    """
    return f"cast(dict[str, Any], {expr})"


# =============================================================================
# ASYNC NORMALIZATION MACROS
# Fix Coroutine/Awaitable return type noise
# =============================================================================


def await_cast(expr: str, typ: str) -> str:
    """
    Cast awaited expression to expected type.

    Args:
        expr: Awaited expression
        typ: Expected return type

    Returns:
        Cast wrapped await
    """
    return f"cast({typ}, await {expr})"


def async_return_cast(expr: str, typ: str) -> str:
    """
    Cast async function return.

    Args:
        expr: Return expression
        typ: Expected type

    Returns:
        Cast wrapped return
    """
    return f"return cast({typ}, {expr})"


def task_result_cast(expr: str, typ: str = "Any") -> str:
    """
    Cast task/coroutine result.

    Args:
        expr: Task result expression
        typ: Expected type

    Returns:
        Cast wrapped expression
    """
    return f"cast({typ}, {expr})"
