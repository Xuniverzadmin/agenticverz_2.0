# hoc_cus_account_L5_engines_notifications_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/account/L5_engines/notifications_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | account |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Notifications Facade - Centralized access to notification operations

## Intent

**Role:** Notifications Facade - Centralized access to notification operations
**Reference:** PIN-470, GAP-109, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
**Callers:** L2 notifications.py API, SDK, Worker

## Purpose

Notifications Facade (L5 Domain Engine)

---

## Functions

### `get_notifications_facade() -> NotificationsFacade`
- **Async:** No
- **Docstring:** Get the notifications facade instance.  This is the recommended way to access notification operations
- **Calls:** NotificationsFacade

## Classes

### `NotificationChannel(str, Enum)`
- **Docstring:** Notification channels.

### `NotificationPriority(str, Enum)`
- **Docstring:** Notification priorities.

### `NotificationStatus(str, Enum)`
- **Docstring:** Notification delivery status.

### `NotificationInfo`
- **Docstring:** Notification information.
- **Methods:** to_dict
- **Class Variables:** id: str, tenant_id: str, channel: str, recipient: str, subject: Optional[str], message: str, priority: str, status: str, created_at: str, sent_at: Optional[str], read_at: Optional[str], metadata: Dict[str, Any]

### `ChannelInfo`
- **Docstring:** Notification channel information.
- **Methods:** to_dict
- **Class Variables:** id: str, name: str, enabled: bool, configured: bool, config_required: List[str]

### `NotificationPreferences`
- **Docstring:** User notification preferences.
- **Methods:** to_dict
- **Class Variables:** tenant_id: str, user_id: str, channels: Dict[str, bool], priorities: Dict[str, List[str]]

### `NotificationsFacade`
- **Docstring:** Facade for notification operations.
- **Methods:** __init__, send_notification, list_notifications, get_notification, mark_as_read, list_channels, get_channel, get_preferences, update_preferences

## Attributes

- `logger` (line 64)
- `_facade_instance: Optional[NotificationsFacade]` (line 464)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

L2 notifications.py API, SDK, Worker

## Export Contract

```yaml
exports:
  functions:
    - name: get_notifications_facade
      signature: "get_notifications_facade() -> NotificationsFacade"
  classes:
    - name: NotificationChannel
      methods: []
    - name: NotificationPriority
      methods: []
    - name: NotificationStatus
      methods: []
    - name: NotificationInfo
      methods: [to_dict]
    - name: ChannelInfo
      methods: [to_dict]
    - name: NotificationPreferences
      methods: [to_dict]
    - name: NotificationsFacade
      methods: [send_notification, list_notifications, get_notification, mark_as_read, list_channels, get_channel, get_preferences, update_preferences]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
