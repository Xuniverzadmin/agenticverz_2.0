# Integrations — L5 Other (3 files)

**Domain:** integrations  
**Layer:** L5_other  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## channel_engine.py
**Path:** `backend/app/hoc/cus/integrations/L5_notifications/engines/channel_engine.py`  
**Layer:** L5_other | **Domain:** integrations | **Lines:** 1102

**Docstring:** Module: channel_engine

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `NotifyChannel` |  | Available notification channels. |
| `NotifyEventType` |  | Types of events that can trigger notifications. |
| `NotifyChannelStatus` |  | Status of a notification channel. |
| `NotifyChannelError` | __init__, to_dict | Raised when notification channel operation fails. |
| `NotifyDeliveryResult` | to_dict | Result of a notification delivery attempt. |
| `NotifyChannelConfig` | is_event_enabled, is_configured, record_success, record_failure, to_dict | Configuration for a notification channel. |
| `NotifyChannelConfigResponse` | to_dict | Response from channel configuration operations. |
| `NotificationSender` | send | Protocol for notification sender implementations. |
| `NotifyChannelService` | __init__, configure_channel, get_channel_config, get_all_configs, get_enabled_channels, enable_channel, disable_channel, set_event_filter (+10 more) | Service for managing notification channels. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_notify_service` | `() -> NotifyChannelService` | no | Get or create the notification service singleton. |
| `_reset_notify_service` | `() -> None` | no | Reset the notification service (for testing). |
| `get_channel_config` | `(tenant_id: str, channel: NotifyChannel) -> Optional[NotifyChannelConfig]` | no | Quick helper to get channel configuration. |
| `send_notification` | `(tenant_id: str, event_type: NotifyEventType, payload: Dict[str, Any], channels:` | yes | Quick helper to send notification. |
| `check_channel_health` | `(tenant_id: str) -> Dict[NotifyChannel, Dict[str, Any]]` | yes | Quick helper to check channel health. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional, Protocol (+1) | no |

---

## service.py
**Path:** `backend/app/hoc/cus/integrations/L5_vault/engines/service.py`  
**Layer:** L5_other | **Domain:** integrations | **Lines:** 551

**Docstring:** Credential Service (GAP-171)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CredentialAccessRecord` |  | Record of credential access for auditing. |
| `CredentialService` | __init__, store_credential, get_credential, get_secret_value, list_credentials, update_credential, delete_credential, rotate_credential (+7 more) | High-level credential service. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `vault` | CredentialData, CredentialMetadata, CredentialType, CredentialVault | yes |

---

## vault.py
**Path:** `backend/app/hoc/cus/integrations/L5_vault/drivers/vault.py`  
**Layer:** L5_other | **Domain:** integrations | **Lines:** 749

**Docstring:** Credential Vault Abstraction (GAP-171)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `VaultProvider` |  | Supported vault providers. |
| `CredentialType` |  | Types of credentials. |
| `CredentialMetadata` |  | Metadata about a stored credential (without secret values). |
| `CredentialData` | credential_id, tenant_id | Full credential including secret values. |
| `CredentialVault` | store_credential, get_credential, get_metadata, list_credentials, update_credential, delete_credential, rotate_credential | Abstract credential vault interface. |
| `HashiCorpVault` | __init__, store_credential, get_credential, get_metadata, list_credentials, update_credential, delete_credential, rotate_credential | HashiCorp Vault implementation. |
| `EnvCredentialVault` | __init__, store_credential, get_credential, get_metadata, list_credentials, update_credential, delete_credential, rotate_credential | Environment variable credential vault (development only). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_credential_vault` | `() -> CredentialVault` | no | Factory function to create appropriate vault based on configuration. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `abc` | ABC, abstractmethod | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, Optional | no |

---
