# PIN-236: Code Purpose & Authority Registry

**Status:** ACTIVE
**Created:** 2025-12-29
**Updated:** 2025-12-29
**Category:** Architecture / Governance / Registry

---

## Summary

Established a formal Code Purpose & Authority Registry system to track artifact identity, responsibility, and authority levels across the AI Console codebase. First audit completed for `products/ai-console/` with 17 artifacts registered.

---

## Problem Statement

As the codebase grows across multiple products (AI Console, Agents, Product Builder), we need:
1. **Artifact tracking** - Know what every file does
2. **Authority boundaries** - Who/what can mutate data
3. **Domain mapping** - Ensure files belong to correct domains
4. **Orphan detection** - Find unreachable or unused code

Without this registry, Claude may guess file purposes, leading to incorrect refactors.

---

## Registry Schema v1 (FROZEN)

```yaml
- artifact_id: AOS-<LAYER>-<PRODUCT>-<DOMAIN>-<SEQUENCE>
  name: filename.tsx
  type: ui-page | ui-component | api-route | service | worker | job | script | migration | test | infra | doc
  status: active | deprecated | experimental
  owner: ai-console | backend | infra | founder | unknown
  purpose: One-line description
  responsibility: |
    - What this artifact does
    - What it's responsible for
  authority_level: observe | advise | enforce | mutate
  execution_surface: browser | server | worker | cli | none
  traceability:
    product: ai-console | agents | product-builder
    console: customer | founder | ops
    domain: overview | activity | incidents | policies | logs | account | integrations | system
    subdomain: null | specific-subdomain
    topic_o1: "The question this answers" | null
    order_depth: O0 | O1 | O2 | O3 | O4 | O5
  relations:
    imports: [list of imports]
    imported_by: [list of importers]
  notes: |
    Additional context, warnings, candidate flags
```

---

## Registry ID Format (FROZEN)

```
AOS-<LAYER>-<PRODUCT>-<DOMAIN>-<SEQUENCE>

LAYER:
  FE = Frontend
  BE = Backend
  IF = Infrastructure
  OP = Operations

PRODUCT:
  AIC = AI Console
  AGT = Agents
  PBL = Product Builder
  SYS = System-wide

DOMAIN (AI Console - FROZEN):
  SYS = System/Internal (entry points, layouts)
  OVR = Overview
  ACT = Activity
  INC = Incidents
  POL = Policies
  LOG = Logs
  ACC = Account
  INT = Integrations

SEQUENCE: 001, 002, 003...
```

**Example:** `AOS-FE-AIC-INC-002` = Frontend, AI Console, Incidents domain, artifact #2

---

## Authority Levels (FROZEN)

| Level | Description | Examples |
|-------|-------------|----------|
| **observe** | Read-only, display data | Most pages, status indicators |
| **advise** | Can recommend actions | IncidentDetailPage (suggests recovery) |
| **enforce** | Controls access/routing | AIConsoleApp (controls auth) |
| **mutate** | Can create/modify/delete data | KeysPage (creates/revokes keys) |

---

## First Audit: AI Console (2025-12-29)

### Artifact Summary

| Domain | Count | Files |
|--------|-------|-------|
| SYS (System) | 3 | main.tsx, AIConsoleApp.tsx, AIConsoleLayout.tsx |
| OVR (Overview) | 1 | OverviewPage.tsx |
| ACT (Activity) | 1 | ActivityPage.tsx |
| INC (Incidents) | 5 | IncidentsPage, IncidentDetailPage, DecisionTimeline, IncidentFilters, IncidentSearchBar |
| POL (Policies) | 1 | PoliciesPage.tsx |
| LOG (Logs) | 1 | LogsPage.tsx |
| INT (Integrations) | 2 | IntegrationsPage.tsx, KeysPage.tsx |
| ACC (Account) | 3 | AccountPage.tsx, SettingsPage.tsx, SupportPage.tsx |
| **Total** | **17** | |

### Authority Distribution

| Authority | Count | Files |
|-----------|-------|-------|
| observe | 14 | Most pages and components |
| advise | 1 | IncidentDetailPage |
| enforce | 1 | AIConsoleApp |
| mutate | 1 | KeysPage |

---

## Registry Entries (AI Console)

### Layer 1: Runtime Entry

```yaml
- artifact_id: AOS-FE-AIC-SYS-001
  name: main.tsx
  type: ui-component
  status: active
  owner: ai-console
  purpose: Browser entry point for standalone AI Console deployment
  authority_level: observe
  execution_surface: browser
  traceability:
    product: ai-console
    domain: system
    order_depth: O0
  notes: FROZEN per PIN-235 Freeze #1. No business logic allowed.
```

### Layer 2: Product Root

```yaml
- artifact_id: AOS-FE-AIC-SYS-002
  name: AIConsoleApp.tsx
  type: ui-component
  status: active
  owner: ai-console
  purpose: Product root - routing, providers, authentication, layout
  authority_level: enforce
  execution_surface: browser
  traceability:
    product: ai-console
    domain: system
    order_depth: O0
  notes: FROZEN per PIN-235 Freeze #1.

- artifact_id: AOS-FE-AIC-SYS-003
  name: AIConsoleLayout.tsx
  type: ui-component
  status: active
  owner: ai-console
  purpose: Layout shell with sidebar navigation and header
  authority_level: observe
  execution_surface: browser
  traceability:
    product: ai-console
    domain: system
    order_depth: O0
```

### Layer 3: Pages

```yaml
# Overview Domain
- artifact_id: AOS-FE-AIC-OVR-001
  name: OverviewPage.tsx
  type: ui-page
  status: active
  owner: ai-console
  purpose: "Answer: Is the system okay right now?"
  authority_level: observe
  traceability:
    domain: overview
    topic_o1: "Is the system okay right now?"
    order_depth: O1

# Activity Domain
- artifact_id: AOS-FE-AIC-ACT-001
  name: ActivityPage.tsx
  type: ui-page
  status: active
  owner: ai-console
  purpose: "Answer: What ran / is running?"
  authority_level: observe
  traceability:
    domain: activity
    topic_o1: "What ran / is running?"
    order_depth: O1

# Incidents Domain
- artifact_id: AOS-FE-AIC-INC-001
  name: IncidentsPage.tsx
  type: ui-page
  status: active
  purpose: "Answer: What went wrong?"
  authority_level: observe
  traceability:
    domain: incidents
    topic_o1: "What went wrong?"
    order_depth: O1

- artifact_id: AOS-FE-AIC-INC-002
  name: IncidentDetailPage.tsx
  type: ui-page
  status: active
  purpose: "O3 Accountability View - Full incident investigation"
  authority_level: advise
  traceability:
    domain: incidents
    order_depth: O3

- artifact_id: AOS-FE-AIC-INC-003
  name: DecisionTimeline.tsx
  type: ui-component
  status: active
  purpose: Render step-by-step decision sequence for incidents
  authority_level: observe
  traceability:
    domain: incidents
    order_depth: O3

- artifact_id: AOS-FE-AIC-INC-004
  name: IncidentFilters.tsx
  type: ui-component
  status: active
  purpose: Filter controls for incident list
  authority_level: observe
  traceability:
    domain: incidents
    order_depth: O2

- artifact_id: AOS-FE-AIC-INC-005
  name: IncidentSearchBar.tsx
  type: ui-component
  status: active
  purpose: Search input for incident list
  authority_level: observe
  traceability:
    domain: incidents
    order_depth: O2

# Policies Domain
- artifact_id: AOS-FE-AIC-POL-001
  name: PoliciesPage.tsx
  type: ui-page
  status: active
  purpose: "Answer: How is behavior defined?"
  authority_level: observe
  traceability:
    domain: policies
    topic_o1: "How is behavior defined?"
    order_depth: O1

# Logs Domain
- artifact_id: AOS-FE-AIC-LOG-001
  name: LogsPage.tsx
  type: ui-page
  status: active
  purpose: "Answer: What is the raw truth?"
  authority_level: observe
  traceability:
    domain: logs
    topic_o1: "What is the raw truth?"
    order_depth: O1

# Integrations Domain
- artifact_id: AOS-FE-AIC-INT-001
  name: IntegrationsPage.tsx
  type: ui-page
  status: active
  purpose: Manage connected services and webhooks
  authority_level: observe
  traceability:
    domain: integrations
    order_depth: O2

- artifact_id: AOS-FE-AIC-INT-002
  name: KeysPage.tsx
  type: ui-page
  status: active
  purpose: API key management
  authority_level: mutate
  traceability:
    domain: integrations
    order_depth: O2
  notes: Mutate authority - can create/revoke keys. Security: keys shown ONCE.

# Account Domain
- artifact_id: AOS-FE-AIC-ACC-001
  name: AccountPage.tsx
  type: ui-page
  status: active
  purpose: Organization and team management
  authority_level: observe
  traceability:
    domain: account
    order_depth: O2

- artifact_id: AOS-FE-AIC-ACC-002
  name: SettingsPage.tsx
  type: ui-page
  status: active
  purpose: Configuration and export options
  authority_level: observe
  traceability:
    domain: account
    order_depth: O2
  notes: |
    CRITICAL UX FIX: Fake toggles removed.
    Keys tab duplicates KeysPage - CANDIDATE_CONSOLIDATION.

- artifact_id: AOS-FE-AIC-ACC-003
  name: SupportPage.tsx
  type: ui-page
  status: active
  purpose: Customer support and documentation links
  authority_level: observe
  traceability:
    domain: account
    order_depth: O2
  notes: |
    CANDIDATE_ORPHAN: File exists but no route defined in AIConsoleApp.tsx.
    Decision needed: add route or remove file.
```

---

## Audit Findings

### Suspected Orphans

| Artifact ID | File | Issue | Action Required |
|-------------|------|-------|-----------------|
| AOS-FE-AIC-ACC-003 | SupportPage.tsx | No route defined in AIConsoleApp.tsx | Decide: add route or remove file |

### Candidate Consolidations

| Files | Issue | Recommendation |
|-------|-------|----------------|
| SettingsPage.tsx (Keys tab) + KeysPage.tsx | Duplicate API key display | Remove Keys tab from Settings |

### Authority Boundary Violations

None detected. All pages correctly use observe/advise. Only KeysPage has mutate authority (appropriate).

### Unclear Purposes

None. All artifacts have clear domain alignment per PIN-186 Constitution.

---

## Usage: Claude Audit Prompt

When auditing a new product or folder, use this prompt:

```
AUDIT PROMPT — Code Purpose & Authority Registry

TASK: Identify all artifacts in {target_folder}

FOR EACH FILE:
1. Determine artifact_id using AOS-<LAYER>-<PRODUCT>-<DOMAIN>-<SEQUENCE>
2. Classify type, status, owner
3. Write purpose (one line)
4. List responsibilities
5. Assign authority_level (observe/advise/enforce/mutate)
6. Map to domain and order_depth
7. List imports and imported_by
8. Flag issues: CANDIDATE_ORPHAN, CANDIDATE_CONSOLIDATION, UNCLEAR_PURPOSE

OUTPUT: YAML registry entries grouped by layer

AT END:
- List suspected orphans
- List candidate consolidations
- List authority boundary violations
- List unclear purposes

This is an audit, not a design exercise.
```

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-234 | Customer Console v1 Constitution (defines domains) |
| PIN-235 | Products-First Architecture Migration (defines structure) |
| PIN-186 | Order Constitution (defines O1-O5 depth) |

---

## Freeze Points

### Freeze #1 — Registry Schema v1
The YAML schema defined in this PIN is frozen. No field additions without amendment.

### Freeze #2 — Domain Code Map
```
SYS = System/Internal
OVR = Overview
ACT = Activity
INC = Incidents
POL = Policies
LOG = Logs
ACC = Account
INT = Integrations
```

### Freeze #3 — Authority Levels
```
observe < advise < enforce < mutate
```

---

## Next Steps

1. **Resolve SupportPage orphan** - Add route or remove file
2. **Consolidate Settings Keys tab** - Remove duplicate
3. **Audit agents product** - When created
4. **Audit product-builder** - When created
5. **Add backend registry** - API routes, services

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-29 | Initial creation with AI Console audit (17 artifacts) |
| 2025-12-29 | Defined registry schema v1, ID format, authority levels |
| 2025-12-29 | Identified 1 orphan (SupportPage), 1 consolidation candidate |
