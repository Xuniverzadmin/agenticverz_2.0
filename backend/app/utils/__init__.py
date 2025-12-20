# NOVA Utils
# Utility modules for rate limiting, idempotency, budget tracking
# Uses lazy imports to avoid pulling in heavy dependencies (sqlmodel, redis)

from typing import TYPE_CHECKING


# Lazy imports for test compatibility (avoid sqlmodel/redis dependency)
def get_existing_run(*args, **kwargs):
    from .idempotency import get_existing_run as _get_existing_run

    return _get_existing_run(*args, **kwargs)


def check_idempotency(*args, **kwargs):
    from .idempotency import check_idempotency as _check_idempotency

    return _check_idempotency(*args, **kwargs)


def allow_request(*args, **kwargs):
    from .rate_limiter import allow_request as _allow_request

    return _allow_request(*args, **kwargs)


def get_rate_limiter():
    from .rate_limiter import get_rate_limiter as _get_rate_limiter

    return _get_rate_limiter()


def acquire_slot(*args, **kwargs):
    from .concurrent_runs import acquire_slot as _acquire_slot

    return _acquire_slot(*args, **kwargs)


def get_concurrent_limiter():
    from .concurrent_runs import get_concurrent_limiter as _get_concurrent_limiter

    return _get_concurrent_limiter()


def check_budget(*args, **kwargs):
    from .budget_tracker import check_budget as _check_budget

    return _check_budget(*args, **kwargs)


def deduct_budget(*args, **kwargs):
    from .budget_tracker import deduct_budget as _deduct_budget

    return _deduct_budget(*args, **kwargs)


def record_cost(*args, **kwargs):
    from .budget_tracker import record_cost as _record_cost

    return _record_cost(*args, **kwargs)


def get_budget_tracker():
    from .budget_tracker import get_budget_tracker as _get_budget_tracker

    return _get_budget_tracker()


# Database helpers (PIN-099: SQLModel Row Extraction Patterns)
def scalar_or_default(*args, **kwargs):
    from .db_helpers import scalar_or_default as _scalar_or_default

    return _scalar_or_default(*args, **kwargs)


def scalar_or_none(*args, **kwargs):
    from .db_helpers import scalar_or_none as _scalar_or_none

    return _scalar_or_none(*args, **kwargs)


def extract_model(*args, **kwargs):
    from .db_helpers import extract_model as _extract_model

    return _extract_model(*args, **kwargs)


def extract_models(*args, **kwargs):
    from .db_helpers import extract_models as _extract_models

    return _extract_models(*args, **kwargs)


def count_or_zero(*args, **kwargs):
    from .db_helpers import count_or_zero as _count_or_zero

    return _count_or_zero(*args, **kwargs)


def sum_or_zero(*args, **kwargs):
    from .db_helpers import sum_or_zero as _sum_or_zero

    return _sum_or_zero(*args, **kwargs)


# Type hints only (not imported at runtime)
if TYPE_CHECKING:
    pass

__all__ = [
    # Idempotency
    "get_existing_run",
    "check_idempotency",
    # Rate limiting
    "allow_request",
    "get_rate_limiter",
    # Concurrent runs
    "acquire_slot",
    "get_concurrent_limiter",
    # Budget
    "check_budget",
    "deduct_budget",
    "record_cost",
    "get_budget_tracker",
    # Database helpers (PIN-099)
    "scalar_or_default",
    "scalar_or_none",
    "extract_model",
    "extract_models",
    "count_or_zero",
    "sum_or_zero",
]
