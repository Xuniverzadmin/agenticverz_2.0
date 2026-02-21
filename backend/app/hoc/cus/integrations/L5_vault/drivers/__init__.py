# capability_id: CAP-018
# Layer: L6 — Domain Drivers
# AUDIENCE: INTERNAL
# Role: Credential vault drivers package
# Reference: PIN-517 (cus_vault Authority Refactor)

"""
Vault Drivers Package

Contains:
- vault.py: Credential vault implementations (HashiCorp, AWS, Env)
"""

from .vault import (
    CredentialVault,
    CredentialType,
    CredentialMetadata,
    CredentialData,
    HashiCorpVault,
    EnvCredentialVault,
    AwsSecretsManagerVault,
    create_credential_vault,
)

__all__ = [
    "CredentialVault",
    "CredentialType",
    "CredentialMetadata",
    "CredentialData",
    "HashiCorpVault",
    "EnvCredentialVault",
    "AwsSecretsManagerVault",
    "create_credential_vault",
]
