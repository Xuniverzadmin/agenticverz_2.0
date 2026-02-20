# capability_id: CAP-018
# Layer: L5 — Domain Engines
# AUDIENCE: CUSTOMER
# Role: Credential vault engines package
# Reference: PIN-517 (cus_vault Authority Refactor)

"""
Vault Engines Package

Contains:
- service.py: High-level credential service with audit
- vault_rule_check.py: Credential access rule checker protocol
"""

from .service import CredentialService
from .vault_rule_check import (
    CredentialAccessResult,
    CredentialAccessRuleChecker,
    DefaultCredentialAccessRuleChecker,
    DenyAllRuleChecker,
)

__all__ = [
    "CredentialService",
    "CredentialAccessResult",
    "CredentialAccessRuleChecker",
    "DefaultCredentialAccessRuleChecker",
    "DenyAllRuleChecker",
]
