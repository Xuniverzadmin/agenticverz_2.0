# hoc_cus_integrations_L5_engines_iam_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/iam_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

IAM engine for identity and access management

## Intent

**Role:** IAM engine for identity and access management
**Reference:** PIN-470, GAP-173 (IAM Integration)
**Callers:** Auth middleware, API routes

## Purpose

IAM Engine (GAP-173)

---

## Classes

### `IdentityProvider(str, Enum)`
- **Docstring:** Supported identity providers.

### `ActorType(str, Enum)`
- **Docstring:** Types of actors in the system.

### `Identity`
- **Docstring:** Resolved identity from any provider.
- **Methods:** has_role, has_permission, has_any_role, has_all_roles, to_dict
- **Class Variables:** identity_id: str, provider: IdentityProvider, actor_type: ActorType, email: Optional[str], name: Optional[str], tenant_id: Optional[str], account_id: Optional[str], team_ids: List[str], roles: Set[str], permissions: Set[str], provider_data: Dict[str, Any], authenticated_at: datetime, expires_at: Optional[datetime]

### `AccessDecision`
- **Docstring:** Result of an access control decision.
- **Methods:** to_dict
- **Class Variables:** allowed: bool, identity: Identity, resource: str, action: str, reason: Optional[str], matched_rule: Optional[str], denied_permissions: List[str], decided_at: datetime

### `IAMService`
- **Docstring:** IAM Service for identity and access management.
- **Methods:** __init__, _setup_default_roles, resolve_identity, _resolve_clerk_identity, _resolve_api_key_identity, _create_system_identity, _expand_role_permissions, check_access, grant_role, revoke_role, define_role, define_resource_permissions, get_access_log, list_roles, list_resources

## Attributes

- `logger` (line 38)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `jwt` |

## Callers

Auth middleware, API routes

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: IdentityProvider
      methods: []
    - name: ActorType
      methods: []
    - name: Identity
      methods: [has_role, has_permission, has_any_role, has_all_roles, to_dict]
    - name: AccessDecision
      methods: [to_dict]
    - name: IAMService
      methods: [resolve_identity, check_access, grant_role, revoke_role, define_role, define_resource_permissions, get_access_log, list_roles, list_resources]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
