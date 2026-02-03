# Layer: TEST
# AUDIENCE: INTERNAL
# Role: SDK contract tests for cus_vault (PIN-517)
# Reference: PIN-517 (cus_vault Authority Refactor), GAP-6

"""
SDK Contract Tests for cus_vault (PIN-517, GAP-6)

These tests lock the SDK-facing contract:
1. Customer vault fails-closed without proper configuration
2. cus-vault:// requires async resolution
3. env:// forbidden for customer scope
4. Legacy vault:// format rejected
"""

import os
import pytest
from unittest.mock import patch


class TestCusCredentialServiceContract:
    """SDK-level contract tests for CusCredentialService."""

    def test_cus_vault_requires_async_resolution(self):
        """cus-vault:// references require async method."""
        from app.hoc.cus.hoc_spine.services.cus_credential_engine import CusCredentialService

        service = CusCredentialService()

        with pytest.raises(ValueError, match="require async resolution"):
            service.resolve_credential(
                tenant_id="t1",
                credential_ref="cus-vault://t1/key1",
            )

    def test_legacy_vault_format_rejected(self):
        """Legacy vault:// format is rejected with guidance."""
        from app.hoc.cus.hoc_spine.services.cus_credential_engine import CusCredentialService

        service = CusCredentialService()

        with pytest.raises(ValueError, match="Use cus-vault://"):
            service.resolve_credential(
                tenant_id="t1",
                credential_ref="vault://secret/data/key",
            )

    def test_plaintext_credentials_rejected(self):
        """Raw API keys are rejected."""
        from app.hoc.cus.hoc_spine.services.cus_credential_engine import CusCredentialService

        service = CusCredentialService()

        # OpenAI key pattern - validate_credential_format returns (is_valid, error_msg)
        is_valid, error_msg = service.validate_credential_format("sk-1234567890")
        assert not is_valid
        assert "Raw" in error_msg and "API key" in error_msg

        # Anthropic key pattern
        is_valid, error_msg = service.validate_credential_format("sk-ant-1234567890")
        assert not is_valid
        assert "Raw" in error_msg and "API key" in error_msg


class TestVaultFactoryContract:
    """SDK-level contract tests for vault factory."""

    def test_customer_scope_rejects_env_vault(self):
        """Customer scope forbids env vault provider."""
        from app.hoc.cus.integrations.L5_vault.drivers.vault import create_credential_vault

        with patch.dict(os.environ, {"CREDENTIAL_VAULT_PROVIDER": "env"}):
            with pytest.raises(ValueError, match="env vault forbidden"):
                create_credential_vault(scope="customer")

    def test_customer_scope_requires_vault_token(self):
        """Customer scope with hashicorp requires VAULT_TOKEN."""
        from app.hoc.cus.integrations.L5_vault.drivers.vault import create_credential_vault

        with patch.dict(os.environ, {"CREDENTIAL_VAULT_PROVIDER": "hashicorp", "VAULT_TOKEN": ""}):
            with pytest.raises(ValueError, match="VAULT_TOKEN required"):
                create_credential_vault(scope="customer")

    def test_system_scope_allows_env_vault(self):
        """System scope permits env vault (development)."""
        from app.hoc.cus.integrations.L5_vault.drivers.vault import (
            create_credential_vault,
            EnvCredentialVault,
        )

        with patch.dict(os.environ, {"CREDENTIAL_VAULT_PROVIDER": "env"}):
            vault = create_credential_vault(scope="system")
            assert isinstance(vault, EnvCredentialVault)


class TestCredentialAccessRuleContract:
    """SDK-level contract tests for credential access rules."""

    @pytest.mark.asyncio
    async def test_default_rule_checker_allows_access(self):
        """Default rule checker permits access (system scope)."""
        from app.hoc.cus.integrations.L5_vault.engines.vault_rule_check import (
            DefaultCredentialAccessRuleChecker,
        )

        checker = DefaultCredentialAccessRuleChecker()
        result = await checker.check_credential_access(
            tenant_id="t1",
            credential_ref="cus-vault://t1/key1",
            accessor_id="test",
            accessor_type="machine",
        )

        assert result.allowed is True
        assert result.rule_id == "default-permissive"

    @pytest.mark.asyncio
    async def test_deny_all_rule_checker_blocks_access(self):
        """DenyAll rule checker blocks all access (fail-closed)."""
        from app.hoc.cus.integrations.L5_vault.engines.vault_rule_check import (
            DenyAllRuleChecker,
        )

        checker = DenyAllRuleChecker()
        result = await checker.check_credential_access(
            tenant_id="t1",
            credential_ref="cus-vault://t1/key1",
            accessor_id="test",
            accessor_type="machine",
        )

        assert result.allowed is False
        assert "fail-closed" in result.rule_id


class TestCredentialReferenceFormat:
    """Tests for credential reference format validation."""

    def test_cus_vault_format_parsing(self):
        """cus-vault:// format must be tenant_id/credential_id."""
        from app.hoc.cus.hoc_spine.services.cus_credential_engine import CusCredentialService

        service = CusCredentialService()

        # Valid format should not raise in sync method (just redirect to async)
        with pytest.raises(ValueError, match="require async"):
            service.resolve_credential("t1", "cus-vault://t1/cred1")

    def test_encrypted_format_works(self):
        """encrypted:// format works synchronously."""
        from app.hoc.cus.hoc_spine.services.cus_credential_engine import CusCredentialService

        service = CusCredentialService()

        # Encrypt then decrypt
        tenant_id = "test_tenant"
        plaintext = "my-secret-api-key"
        encrypted_ref = service.encrypt_credential(tenant_id, plaintext)

        assert encrypted_ref.startswith("encrypted://")

        # Decrypt should work
        decrypted = service.resolve_credential(tenant_id, encrypted_ref)
        assert decrypted == plaintext
