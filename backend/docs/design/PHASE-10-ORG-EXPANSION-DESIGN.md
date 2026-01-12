# Phase-10: Organization Expansion Design

**Status:** DESIGN ONLY (Track C)
**Author:** Claude + Human Pair
**Date:** 2026-01-12
**Reference:** PIN-401 Track C

---

## Table of Contents

1. [Overview](#overview)
2. [Org Model Concepts](#org-model-concepts)
3. [Invariants](#invariants)
4. [Scope & Non-Scope](#scope--non-scope)
5. [Data Model](#data-model)
6. [API Surface (Proposed)](#api-surface-proposed)
7. [Migration Strategy](#migration-strategy)
8. [Decision Log](#decision-log)

---

## Overview

Phase-10 introduces **Organization (Org)** as a billing and administrative unit
that groups multiple tenants. This design preserves the existing tenant-centric
auth model while adding organizational hierarchy for enterprise customers.

### Core Principle

> **Tenant is the execution boundary. Org is the billing boundary.**

### Key Constraints (From PIN-401)

- TenantMembership stays primary for access control
- Org does NOT replace tenant auth
- No auth changes in Phase-10
- Billing anchor moves to Org level

---

## Org Model Concepts

### 1. Organization

An organization represents an enterprise customer with multiple projects/tenants.

```
Organization
├── org_id: str          # "org_abc123"
├── name: str            # "Acme Corp"
├── billing_anchor: bool # TRUE (this is where billing attaches)
├── created_at: datetime
├── tenants: List[Tenant]
└── members: List[OrganizationMembership]
```

**Semantic Rules:**
- Every Org has exactly one billing anchor (the org itself)
- An Org can have 0..N tenants
- Tenants may exist without an Org (backward compatibility)

### 2. OrganizationMembership

Associates users with organizations and defines org-level roles.

```
OrganizationMembership
├── org_id: str
├── user_id: str
├── org_role: OrgRole     # OWNER | ADMIN | MEMBER
├── created_at: datetime
└── created_by: str       # founder or org_owner
```

**Semantic Rules:**
- OrgRole governs org-level actions (billing, member management)
- OrgRole does NOT grant tenant access
- Tenant access still requires TenantMembership

### 3. OrgRole Enumeration

| Role | Description | Permissions |
|------|-------------|-------------|
| OWNER | Organization owner | Full org control, billing, transfer |
| ADMIN | Organization admin | Manage members, create tenants |
| MEMBER | Organization member | View org, request tenant access |

### 4. Relationship to Existing Models

```
                    ┌──────────────────┐
                    │   Organization   │
                    │  (billing_anchor)│
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
       ┌────┴───┐       ┌────┴───┐       ┌────┴───┐
       │ Tenant │       │ Tenant │       │ Tenant │
       │   A    │       │   B    │       │   C    │
       └────┬───┘       └────┬───┘       └────┬───┘
            │                │                │
   TenantMembership  TenantMembership  TenantMembership
   (access control)  (access control)  (access control)
```

**Critical Invariant:**
```
Access to Tenant A is determined by TenantMembership, NOT OrgMembership.
Being an Org OWNER does not automatically grant access to all tenants.
```

---

## Invariants

### ORG-001: Tenant Auth Independence

> **TenantMembership is the ONLY source of tenant access.**
> OrgMembership NEVER implies TenantMembership.

**Rationale:** Prevents privilege escalation through org hierarchy.

### ORG-002: Billing Anchor Singularity

> **Every tenant has exactly one billing anchor.**
> For org-attached tenants: the org is the billing anchor.
> For standalone tenants: the tenant is its own billing anchor.

**Rationale:** Prevents billing ambiguity and double-charging.

### ORG-003: Org-Tenant Immutability

> **Once a tenant is attached to an org, it cannot be detached.**
> Org transfer requires explicit migration process.

**Rationale:** Prevents billing and audit trail fragmentation.

### ORG-004: Role Separation

> **OrgRole and TenantRole are independent.**
> An OWNER at org level may have VIEW_ONLY at tenant level.

**Rationale:** Supports enterprise compliance requirements.

### ORG-005: Standalone Tenant Backward Compatibility

> **Tenants without an org MUST continue to function.**
> No migration is forced. Org attachment is opt-in.

**Rationale:** Preserves existing customer experience.

### ORG-006: Founder Org Management

> **Only founders can create, modify, or delete organizations.**
> Org owners can manage members but not the org itself.

**Rationale:** Maintains founder authority over enterprise structure.

### ORG-007: Billing State Inheritance

> **When a tenant attaches to an org, tenant billing state becomes org billing state.**
> Org billing state propagates to all attached tenants.

**Rationale:** Single billing source of truth.

### ORG-008: No Cross-Org Tenant Sharing

> **A tenant can belong to at most one organization.**
> Multi-org access requires tenant duplication.

**Rationale:** Prevents complex permission chains.

---

## Scope & Non-Scope

### In Scope (Phase-10)

| Feature | Description |
|---------|-------------|
| Org CRUD | Create, read, update org (founder only) |
| OrgMembership CRUD | Manage org members |
| Tenant-Org Attachment | Attach tenant to org |
| Billing Anchor Redirect | Redirect billing from tenant to org |
| Org Dashboard | View org tenants and members |

### NOT in Scope (Phase-10)

| Feature | Reason |
|---------|--------|
| Auth Changes | ORG-001 - TenantMembership unchanged |
| Cross-Tenant Views | Requires Phase-11 aggregation |
| Org-Level SDK Keys | Security review needed |
| Automatic Member Inheritance | Violates ORG-001 |
| Tenant Detachment | Violates ORG-003 |

---

## Data Model

### New Tables (Proposed)

```sql
-- organizations table
CREATE TABLE organizations (
    org_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    billing_email VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(36) NOT NULL,  -- founder user_id
    CONSTRAINT chk_org_id_prefix CHECK (org_id LIKE 'org_%')
);

-- organization_memberships table
CREATE TABLE organization_memberships (
    id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
    user_id VARCHAR(36) NOT NULL,
    org_role VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(36) NOT NULL,
    UNIQUE (org_id, user_id),
    CONSTRAINT chk_org_role CHECK (org_role IN ('OWNER', 'ADMIN', 'MEMBER'))
);
```

### Modified Tables

```sql
-- Add org_id to tenants table
ALTER TABLE tenants ADD COLUMN org_id VARCHAR(36) REFERENCES organizations(org_id);

-- Index for org-tenant lookup
CREATE INDEX idx_tenants_org_id ON tenants(org_id);
```

### ID Prefixes

| Entity | Prefix | Example |
|--------|--------|---------|
| Organization | `org_` | `org_abc123xyz` |
| Tenant | `t_` | `t_def456` (unchanged) |

---

## API Surface (Proposed)

### Founder Endpoints (Org Management)

```
POST   /founder/orgs                 # Create organization
GET    /founder/orgs/{org_id}        # Get organization details
PATCH  /founder/orgs/{org_id}        # Update organization
DELETE /founder/orgs/{org_id}        # Delete organization (if empty)

POST   /founder/orgs/{org_id}/attach/{tenant_id}  # Attach tenant to org
GET    /founder/orgs/{org_id}/tenants             # List org tenants
```

### Org Owner/Admin Endpoints (Member Management)

```
GET    /api/v1/orgs/{org_id}/members             # List members
POST   /api/v1/orgs/{org_id}/members             # Add member
PATCH  /api/v1/orgs/{org_id}/members/{user_id}   # Update member role
DELETE /api/v1/orgs/{org_id}/members/{user_id}   # Remove member
```

### Permission Requirements

| Endpoint | Required Permission |
|----------|-------------------|
| Founder org endpoints | `founder:*` |
| List members | `org:members:read` + org membership |
| Add member | `org:members:write` + OWNER/ADMIN role |
| Update member | `org:members:write` + OWNER role |
| Remove member | `org:members:write` + OWNER/ADMIN role |

---

## Migration Strategy

### Phase 10.0: Schema Only

1. Create `organizations` table (empty)
2. Create `organization_memberships` table (empty)
3. Add nullable `org_id` column to `tenants`
4. No data migration required

### Phase 10.1: First Org Onboarding

1. Founder creates organization via `/founder/orgs`
2. Founder attaches existing tenants via `/founder/orgs/{org_id}/attach/{tenant_id}`
3. Billing redirect is automatic upon attachment
4. Existing TenantMemberships remain intact

### Phase 10.2: Self-Service (Future)

1. Org owners can create new tenants within their org
2. New tenants automatically attach to org
3. Still requires founder approval for first org creation

---

## Decision Log

### DEC-001: TenantMembership Unchanged

**Decision:** Keep TenantMembership as sole source of tenant access.

**Alternatives Considered:**
- A: OrgMembership implies TenantMembership (rejected: security risk)
- B: Merge OrgRole and TenantRole (rejected: complexity)
- C: Keep independent (selected: clear separation)

**Rationale:** Enterprise customers need granular access control. An org admin
managing billing should not automatically access production data.

### DEC-002: Org Attachment is One-Way

**Decision:** Tenants cannot be detached from orgs.

**Alternatives Considered:**
- A: Allow detachment with billing reconciliation (rejected: audit trail)
- B: Allow detachment with founder approval (rejected: complexity)
- C: No detachment, transfer only (selected: clean semantics)

**Rationale:** Billing history must have a clear owner. Detachment creates
ambiguity about who owns historical charges.

### DEC-003: Standalone Tenants Preserved

**Decision:** Tenants without orgs continue to work.

**Alternatives Considered:**
- A: Force all tenants to have an org (rejected: migration burden)
- B: Auto-create single-tenant orgs (rejected: complexity)
- C: Org is optional (selected: backward compatibility)

**Rationale:** Existing customers should not be disrupted. Org adoption
should be opt-in for enterprise customers.

---

## Open Questions (For Human Review)

1. **Q1:** Should org billing state override tenant billing state, or should
   they be combined? (Current proposal: org state replaces tenant state)

2. **Q2:** Should we allow org-level API keys that work across all org tenants?
   (Current proposal: out of scope for Phase-10)

3. **Q3:** What happens to tenant billing history when attached to an org?
   (Current proposal: history preserved, new charges go to org)

---

## Appendix: Layer Classification

| Component | Layer | Role |
|-----------|-------|------|
| Organization model | L4 | Domain entity |
| OrgMembership model | L4 | Domain entity |
| OrgRole enum | L4 | Domain value |
| Founder org endpoints | L3 | Boundary adapter |
| Org member endpoints | L2 | Product API |
| Billing anchor redirect | L4 | Domain rule |

---

**End of Phase-10 Design Document**

This document is DESIGN ONLY per PIN-401 Track C.
No code changes are permitted until Track A completes and this design is approved.
