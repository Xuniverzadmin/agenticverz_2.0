# capability_id: CAP-012
# Layer: L4 — HOC Spine (Service)
# AUDIENCE: INTERNAL
# Role: Cross-domain gateway — L5 engines import here instead of reaching
#        into another domain's L5/L6 directly.
# Callers: analytics/L5_engines, policies/L5_engines
# Reference: ITER3.8 Phase 4 (hoc_cross_domain_validator E1 remediation)

"""
Cross-Domain Gateway (L4)

Provides hoc_spine-mediated access to functions that L5 engines from
one domain need from another domain.  L5 engines MUST import cross-domain
functions from this module (or another hoc_spine module) — never directly
from a sibling domain's L5_engines / L6_drivers.

Current re-exports:
  - Circuit breaker utilities  (controls domain)
  - Recovery rule evaluation   (incidents domain)
"""

# --- Controls domain: circuit breaker utilities ---
from app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver import (
    get_circuit_breaker,
    is_v2_disabled,
    report_drift,
)

# --- Incidents domain: recovery rule evaluation ---
from app.hoc.cus.incidents.L5_engines.recovery_rule_engine import (
    evaluate_rules,
)

__all__ = [
    "get_circuit_breaker",
    "is_v2_disabled",
    "report_drift",
    "evaluate_rules",
]
