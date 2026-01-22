# Layer: L4 — Domain Services
# AUDIENCE: CUSTOMER
# Role: policies/drivers - Reserved for L3 adapters
# Reference: HOC_policies_analysis_v1.md

"""
policies/drivers

EMPTY - Reserved for L3 adapters.

NOTE: policy_driver.py was moved to internal/platform/policy/engines/
because it declares AUDIENCE: INTERNAL.

For INTERNAL policy operations, use:
    from app.houseofcards.internal.platform.policy.engines import get_policy_driver

For CUSTOMER policy operations, use:
    from app.houseofcards.customer.policies.facades import get_policies_facade
"""
