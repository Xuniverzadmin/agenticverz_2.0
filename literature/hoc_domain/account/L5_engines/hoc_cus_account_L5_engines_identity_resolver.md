# hoc_cus_account_L5_engines_identity_resolver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/account/L5_engines/identity_resolver.py` |
| Layer | L5 — Domain Engine |
| Domain | account |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Identity resolution from various providers

## Intent

**Role:** Identity resolution from various providers
**Reference:** PIN-470, GAP-173 (IAM Integration)
**Callers:** IAMService, Auth middleware

## Purpose

Identity Resolver (GAP-173)

---

## Functions

### `create_default_identity_chain() -> IdentityChain`
- **Async:** No
- **Docstring:** Create the default identity resolver chain.
- **Calls:** APIKeyIdentityResolver, ClerkIdentityResolver, IdentityChain, SystemIdentityResolver

## Classes

### `IdentityResolver(ABC)`
- **Docstring:** Abstract identity resolver.
- **Methods:** resolve, provider

### `ClerkIdentityResolver(IdentityResolver)`
- **Docstring:** Resolver for Clerk JWT tokens.
- **Methods:** __init__, provider, resolve

### `APIKeyIdentityResolver(IdentityResolver)`
- **Docstring:** Resolver for API keys.
- **Methods:** provider, resolve

### `SystemIdentityResolver(IdentityResolver)`
- **Docstring:** Resolver for internal system identities.
- **Methods:** provider, resolve

### `IdentityChain`
- **Docstring:** Chain of identity resolvers.
- **Methods:** resolve
- **Class Variables:** resolvers: list[IdentityResolver]

## Attributes

- `logger` (line 38)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.hoc.int.platform.iam.engines.iam_service`, `jwt` |

## Callers

IAMService, Auth middleware

## Export Contract

```yaml
exports:
  functions:
    - name: create_default_identity_chain
      signature: "create_default_identity_chain() -> IdentityChain"
  classes:
    - name: IdentityResolver
      methods: [resolve, provider]
    - name: ClerkIdentityResolver
      methods: [provider, resolve]
    - name: APIKeyIdentityResolver
      methods: [provider, resolve]
    - name: SystemIdentityResolver
      methods: [provider, resolve]
    - name: IdentityChain
      methods: [resolve]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
