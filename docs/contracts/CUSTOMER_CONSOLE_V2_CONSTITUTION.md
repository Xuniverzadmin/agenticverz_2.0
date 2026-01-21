# Customer Console v2 Constitution

**Status:** DRAFT (NOT FROZEN)
**Effective:** 2026-01-20
**Scope:** AI Governance Console (preflight-console.agenticverz.com, console.agenticverz.com)
**Authority:** Human-approved, not AI-derived
**Supersedes:** CUSTOMER_CONSOLE_V1_CONSTITUTION.md (v2.1.0)

---

## 0. Constitutional Status

### Current Status

```
STATUS: DRAFT
SCOPE: AI GOVERNANCE CONSOLE BUILD
FREEZE STATUS: NOT FROZEN - Active development
```

**Purpose:**
This constitution defines the expanded domain structure for the AI Governance Console, incorporating Analytics as a first-class domain and refining the subdomain/topic hierarchy for machine-native agent governance.

---

## 1. Purpose

This document is the **source of truth** for AI Governance Console structure, semantics, and governance.

All playbooks, behavior rules, and implementation decisions must align to this constitution.

**This is the law. Playbooks enforce it. Behavior rules guard it.**

---

## 1.1 UI As Constraint (Primary Principle)

> The Console UI is a declaration of **human intent**, not a reflection of backend readiness.

**Implications:**

* UI may exist in EMPTY or UNBOUND states for extended periods
* Backend completeness is **not** a prerequisite for UI existence
* UI must never be reshaped to accommodate backend gaps

---

## 1.2 Authority Stack (Canonical Order)

```
1. This Constitution                    ← Human Intent (Authoritative)
2. UI Plan (ui_plan.yaml)               ← Declarative Surface
3. Intent Specifications                ← Declarative Binding
4. Capability Registry                  ← Observability State
5. SDSR Scenarios                       ← System Revelation
6. Backend Endpoints                    ← Implementation
7. Frontend Renderer                    ← Passive Consumer
```

**Invariant:**
No lower layer may constrain or reshape a higher layer.

---

## 2. Domain Model (v2)

### 2.1 Eight Domains (Expanded from v1)

The AI Governance Console comprises **eight domains** organized into three tiers:

| Tier | Domains | Purpose |
|------|---------|---------|
| **Core Lenses** | Overview, Activity, Incidents, Policies, Logs | Primary operational visibility |
| **Intelligence** | Analytics | Cost and usage intelligence |
| **Infrastructure** | Connectivity, Account | Platform configuration |

### 2.2 Complete Domain Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────┐
│ AI GOVERNANCE CONSOLE - DOMAIN HIERARCHY v2                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ 1. OVERVIEW                                                             │
│    └─ 1.1 Summary                                                       │
│        ├─ Highlights (system pulse, status)                             │
│        └─ Decisions (pending actions, approvals)                        │
│                                                                         │
│ 2. ACTIVITY                                                             │
│    └─ 2.1 LLM Runs                                                      │
│        ├─ Live (currently executing)                                    │
│        ├─ Completed (finished runs)                                     │
│        └─ Signals (predictions, anomalies, risks)                       │
│                                                                         │
│ 3. INCIDENTS                                                            │
│    └─ 3.1 Events                                                        │
│        ├─ Active (requires attention)                                   │
│        ├─ Resolved (acknowledged, closed)                               │
│        └─ Historical (audit trail)                                      │
│                                                                         │
│ 4. POLICIES                                                             │
│    ├─ 4.1 Governance                                                    │
│    │    ├─ Active (enforced policies)                                   │
│    │    ├─ Lessons (learned patterns, proposals)                        │
│    │    └─ Policy Library (templates, ethical constraints)              │
│    └─ 4.2 Limits                                                        │
│         ├─ Thresholds (configured limits)                               │
│         └─ Violations (limit breaches)                                  │
│                                                                         │
│ 5. LOGS                                                                 │
│    └─ 5.1 Records                                                       │
│        ├─ LLM Runs (execution records)                                  │
│        ├─ System Logs (worker events)                                   │
│        └─ Audit Logs (governance actions)                               │
│                                                                         │
│ 6. ANALYTICS                                                            │
│    ├─ 6.1 Insights                                                      │
│    │    └─ Cost Intelligence (spend, anomalies, forecasts)              │
│    └─ 6.2 Usage Statistics                                              │
│         ├─ Policies Usage (effectiveness, coverage)                     │
│         └─ Productivity (saved time, efficiency gains)                  │
│                                                                         │
│ 7. CONNECTIVITY                                                         │
│    ├─ 7.1 Integrations                                                  │
│    │    └─ SDK Integration (aos_sdk setup, future platforms)            │
│    └─ 7.2 API                                                           │
│         └─ API Keys (lifecycle: create, rotate, revoke)                 │
│                                                                         │
│ 8. ACCOUNT                                                              │
│    ├─ 8.1 Profile (organization identity)                               │
│    ├─ 8.2 Billing (subscription, invoices)                              │
│    ├─ 8.3 Subuser Management (team members, RBAC - admin only)          │
│    └─ 8.4 Account Management (suspend, terminate)                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Domain Definitions (Complete)

| Domain | Fundamental Question | Primary Object Family |
|--------|---------------------|----------------------|
| **Overview** | "Is the system okay right now?" | Status, Health, Pulse, Decisions |
| **Activity** | "What ran / is running?" | Runs, Jobs, Predictions, Signals |
| **Incidents** | "What went wrong?" | Incidents, Violations, Failures |
| **Policies** | "How is behavior defined?" | Rules, Limits, Constraints, Proposals |
| **Logs** | "What is the raw truth?" | Traces, Audit, Proof, Records |
| **Analytics** | "What can we learn?" | Cost, Usage, Productivity, Trends |
| **Connectivity** | "How does the system connect?" | Integrations, API Keys, SDK |
| **Account** | "Who am I and what do I own?" | Profile, Billing, Users, Plans |

### 2.4 Domain Rules

- Core Lenses (5) are the **primary value lenses** - operational focus
- Analytics (1) is the **intelligence lens** - learning and optimization
- Infrastructure (2) are **supporting infrastructure** - configuration and access
- Domains represent **different views of the same tenant**
- They must **not** be duplicated, merged, or renamed
- All system truth must surface through one of these domains
- Adding a domain = repositioning risk (requires constitutional amendment)

---

## 3. Structural Hierarchy

### 3.1 Domain → Subdomain → Topic → Panel

```
Domain (8)
  └─ Subdomain (varies by domain)
       └─ Topic (3-4 per subdomain)
            └─ Panel (UI component, O1-O5 depth)
```

### 3.2 Subdomain Definition

- Represents a **real system boundary**
- Owns an **independent lifecycle**
- Has **distinct permissions or sensitivity**
- Would exist even if sibling subdomains didn't
- Appears as **tabs or sections within a domain**

### 3.3 Topic Definition

- A **view** or **capability** within a subdomain
- Shallow, read-oriented entry point
- Safe to add without changing domain structure
- Appears as **page content** within subdomain

### 3.4 Orders (O1-O5) — Epistemic Depth

| Order | Meaning | Invariant |
|-------|---------|-----------|
| O1 | Summary / Snapshot | Scannable, shallow, safe entry |
| O2 | List of instances | "Show me instances" |
| O3 | Detail / Explanation | "Explain this thing" |
| O4 | Context / Impact | "What else did this affect?" |
| O5 | Raw records / Proof | "Show me proof" |

---

## 4. Design Decisions (Locked)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Topics Location** | Tabs in main workspace (NOT in sidebar) | Topics are views within a subdomain; switching topics doesn't change navigation context |
| **Subdomains Location** | Nested under domains in sidebar | Clear hierarchy; subdomains are clickable navigation items |
| **Account Location** | Pinned to sidebar footer | Always accessible, separated from core navigation |
| **Route Format** | Domain-level only (e.g., `/precus/policies`) | Simplicity; subdomain/topic state preserved in query params or session |

---

## 5. Sidebar Structure

### 5.1 Primary Navigation (Sidebar with Nested Subdomains)

```
┌─────────────────────────────────────┐
│ CORE LENSES                         │
│                                     │
│   🏠 Overview                       │
│       └─ Summary                    │
│                                     │
│   📊 Activity                       │
│       └─ LLM Runs                   │
│                                     │
│   ⚠️ Incidents                      │
│       └─ Events                     │
│                                     │
│   🛡️ Policies                       │
│       ├─ Governance                 │
│       └─ Limits                     │
│                                     │
│   📝 Logs                           │
│       └─ Records                    │
│                                     │
├─────────────────────────────────────┤
│ INTELLIGENCE                        │
│                                     │
│   📈 Analytics                      │
│       ├─ Insights                   │
│       └─ Usage Stats                │
│                                     │
├─────────────────────────────────────┤
│ CONNECTIVITY                        │
│                                     │
│   🔌 Connectivity                   │
│       ├─ Integrations               │
│       └─ API                        │
│                                     │
├─────────────────────────────────────┤
│ (spacer)                            │
├─────────────────────────────────────┤
│ ACCOUNT (pinned to footer)          │
│                                     │
│   👤 Account                        │
│       ├─ Profile                    │
│       ├─ Billing                    │
│       ├─ Team (admin only)          │
│       └─ Settings                   │
└─────────────────────────────────────┘
```

### 5.2 Navigation Behavior

- Clicking **domain** in sidebar → loads default subdomain + first topic
- Clicking **subdomain** in sidebar → loads first topic of that subdomain
- Clicking **topic tab** in main workspace → switches topic within current subdomain
- Subdomains are always expanded (no collapse)
- Account section is visually separated and pinned to footer

---

## 6. Main Workspace Layout

### 6.1 Layout Structure (Top to Bottom)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. BREADCRUMB                                                   │
│    Activity > LLM Runs > Live                                   │
├─────────────────────────────────────────────────────────────────┤
│ 2. TOPIC HEADER (selected topic + definition)                   │
│    Live: Currently executing LLM runs                           │
├─────────────────────────────────────────────────────────────────┤
│ 3. TOPIC TABS                                                   │
│    [LIVE]  [COMPLETED]  [SIGNALS]                               │
│     ^^^^                                                        │
│     (selected)                                                  │
├─────────────────────────────────────────────────────────────────┤
│ 4. PANEL CONTENT                                                │
│                                                                 │
│    [Data tables, cards, charts, forms, etc.]                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Layout Rules

| Component | Purpose | Invariant |
|-----------|---------|-----------|
| **Breadcrumb** | Navigation path (Domain > Subdomain > Topic) | Always visible |
| **Topic Header** | Selected topic name + definition | Shows current context |
| **Topic Tabs** | Horizontal tabs for switching topics | Topics within subdomain |
| **Panel Content** | Actual data/UI for the selected topic | Scrollable area |

### 6.3 Topic Tab Behavior

- Topics appear as **horizontal tabs** in the main workspace
- Tabs are **not** in the sidebar
- Switching tabs does NOT change the URL (state preserved in memory/query params)
- First topic in a subdomain is the default

---

## 7. Panel State Model

| State | Constitutional Meaning | Rendering |
|-------|------------------------|-----------|
| EMPTY | Planned UI surface; intent not yet declared | Must render (empty state UX) |
| UNBOUND | Intent exists; system capability missing | Must render (coming soon UX) |
| DRAFT | Capability declared; not validated | Must render (disabled controls) |
| BOUND | Capability observed/validated | Full functionality |
| DEFERRED | Explicit governance decision (human-only) | Hidden or explanation |

**Rule:**
EMPTY and UNBOUND states **must render**. Silence is a violation.

---

## 8. v2 Additions (Relative to v1)

### 8.1 Analytics Domain (NEW)

Analytics is now a **first-class domain**, not a subdomain of another lens.

| Subdomain | Topics | Purpose |
|-----------|--------|---------|
| **Insights** | Cost Intelligence | Spend tracking, anomaly detection, forecasting |
| **Usage Statistics** | Policies Usage, Productivity | Effectiveness measurement, ROI |

**Rationale:**
Machine-native agents require continuous cost optimization and productivity measurement. Analytics deserves domain-level prominence for:
- Cost attribution ("saved cost by policy")
- Efficiency metrics ("productivity gains")
- Usage patterns ("policy effectiveness")

### 8.2 Refined Subdomain Structure

| Domain | v1 Subdomains | v2 Subdomains |
|--------|---------------|---------------|
| Overview | Summary | Summary (unchanged) |
| Activity | LLM Runs | LLM Runs (unchanged) |
| Incidents | Events | Events (unchanged) |
| Policies | Governance, Limits | Governance (+ Lessons), Limits |
| Logs | Records | Records (unchanged) |
| Analytics | (new) | Insights, Usage Statistics |
| Connectivity | Providers, Network, Credentials, Health | Integrations, API |
| Account | Profile, Billing, Users, Compliance | Profile, Billing, Subuser Mgmt, Account Mgmt |

### 8.3 Topic Refinements

**Policies > Governance:**
- Renamed "Drafts" → "Lessons" (learned patterns, policy proposals)
- Added "Policy Library" (templates, ethical constraints)

**Analytics:**
- "Cost Intelligence" under Insights
- "Policies Usage" and "Productivity" under Usage Statistics

**Connectivity:**
- Simplified to "Integrations" (SDK setup) and "API" (key management)

**Account:**
- Added "Account Management" (suspend, terminate)
- Clarified "Subuser Management" is admin-only (RBAC)

---

## 9. Governance Rules (Unchanged from v1)

### 9.1 Power & Authority Constraints

- No global automation
- No learned authority
- No cross-tenant intelligence claims
- No "system decided" language

### 9.2 Action Requirements

All actions must be:

- **Explicit** — declared, not inferred
- **Scoped** — tenant-bounded
- **Attributable** — to a human actor
- **Auditable** — logged immutably

### 9.3 Data Integrity

- Logs and evidence are **immutable**
- No rewriting history
- No "fixing" past traces
- No inferring missing facts
- First truth wins (ON CONFLICT DO NOTHING)

---

## 10. Jurisdiction Boundaries

### 10.1 Console Types

| Console | Scope | Data Boundary |
|---------|-------|---------------|
| Customer Console | Single tenant | Tenant-isolated |
| Preflight Console | Pre-launch | Same data, debug UI |
| Founder Console | Cross-tenant | Founder-only |
| Ops Console | Infrastructure | Operator-only |

### 10.2 Project Scope

All Console domains are evaluated within a selected **Project context**.

- Project selector in **global header** (not sidebar)
- Switching Projects changes **data scope only**
- Cross-project aggregation is **forbidden** in Customer Console

---

## 11. Route Structure (Preflight Console)

### 11.1 URL Pattern (Domain-Level Only)

```
/precus/{domain}
```

**Design Decision:** Routes stop at domain level. Subdomain and topic state is preserved in:
- Session state (React state)
- Query parameters (optional: `?subdomain=governance&topic=lessons`)

### 11.2 Route Examples

| Route | Default View | Subdomain | Topic |
|-------|--------------|-----------|-------|
| `/precus` | Overview > Summary > HIGHLIGHTS | Summary | Highlights |
| `/precus/overview` | Overview > Summary > HIGHLIGHTS | Summary | Highlights |
| `/precus/activity` | Activity > LLM Runs > LIVE | LLM Runs | Live |
| `/precus/incidents` | Incidents > Events > ACTIVE | Events | Active |
| `/precus/policies` | Policies > Governance > ACTIVE | Governance | Active |
| `/precus/logs` | Logs > Records > LLM_RUNS | Records | LLM Runs |
| `/precus/analytics` | Analytics > Insights > COST_INTELLIGENCE | Insights | Cost Intelligence |
| `/precus/connectivity` | Connectivity > Integrations > SDK_SETUP | Integrations | SDK Setup |
| `/precus/account` | Account > Profile > OVERVIEW | Profile | Overview |

### 11.3 Navigation Behavior

- Clicking **domain** in sidebar → loads default subdomain + first topic
- Clicking **subdomain** in sidebar → loads first topic of that subdomain
- Clicking **topic tab** → switches topic within current subdomain (no URL change)
- Back/forward browser buttons preserve domain (subdomain/topic from session state)

---

## 12. What Remains from v1

The following are **preserved without change**:

* Order semantics (O1-O5 definitions)
* Panel state model (EMPTY → UNBOUND → DRAFT → BOUND → DEFERRED)
* Governance rules (no learned authority, no cross-tenant)
* Data integrity rules (immutability)
* Claude's role constraints
* Deviation protocol

---

## 13. Differences from v1

| Aspect | v1 | v2 |
|--------|----|----|
| Domains | 7 (5 core + 2 infrastructure) | 8 (5 core + 1 intelligence + 2 infrastructure) |
| Analytics | Part of Overview (implied) | First-class domain |
| Lessons | Under "Drafts" topic | Renamed, under Governance |
| Connectivity | 4 subdomains | 2 subdomains (simplified) |
| Account subdomains | 4 | 4 (reorganized) |
| Status | FROZEN | DRAFT (not frozen) |

---

## 14. Version History

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 2.0.0 | 2026-01-20 | **v2 DRAFT** — Analytics as domain, refined hierarchy, NOT FROZEN | Human-approved |
| 2.1.0 | 2026-01-20 | **Design Decisions Locked** — Topics as tabs, domain-level routes, Account pinned to footer | Human-approved |

---

## 15. References

| Document | Purpose |
|----------|---------|
| `CUSTOMER_CONSOLE_V1_CONSTITUTION.md` | Previous version |
| `docs/design/AI_GOVERNANCE_CONSOLE_WIREFRAME.md` | UI wireframe structure |
| `docs/architecture/FRONTEND_L1_BUILD_PLAN.md` | Frontend implementation plan |
| `docs/architecture/BACKEND_DOMAIN_INVENTORY.md` | Backend endpoint mapping |
| `SESSION_PLAYBOOK.yaml` | Enforcement at session start |
| `CLAUDE_AUTHORITY.md` | Supreme authority |
| `docs/memory-pins/INDEX.md` | Project memory |

---

**This constitution is the source of truth for AI Governance Console v2.**

**Playbooks enforce it. Behavior rules guard it. Humans amend it.**
