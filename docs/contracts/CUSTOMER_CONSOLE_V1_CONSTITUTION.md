# Customer Console v1 Constitution

**Status:** FROZEN
**Effective:** 2025-12-29
**Scope:** Customer Console only (console.agenticverz.com)
**Authority:** Human-approved, not AI-derived

---

## 1. Purpose

This document is the **source of truth** for Customer Console structure, semantics, and governance.

All playbooks, behavior rules, and implementation decisions must align to this constitution.

**This is the law. Playbooks enforce it. Behavior rules guard it.**

---

## 2. Frozen Domains

The following five domains are frozen for v1 and must appear exactly as written:

```
Overview
Activity
Incidents
Policies
Logs
```

### Domain Definitions

| Domain | Fundamental Question | Primary Object Family |
|--------|---------------------|----------------------|
| **Overview** | "Is the system okay right now?" | Status, Health, Pulse |
| **Activity** | "What ran / is running?" | Runs, Traces, Jobs |
| **Incidents** | "What went wrong?" | Incidents, Violations, Failures |
| **Policies** | "How is behavior defined?" | Rules, Limits, Constraints, Approvals |
| **Logs** | "What is the raw truth?" | Traces, Audit, Proof |

### Domain Rules

- These are the **only** core value lenses
- They represent **different views of the same tenant**
- They must **not** be duplicated, merged, or renamed
- All system truth must surface through one of these domains
- Adding a domain = repositioning risk (requires constitutional amendment)

---

## 3. Structural Hierarchy

### 3.1 Domain

- Answers a **fundamental user question**
- Maps to a **primary object family** in code
- Stable over **years**
- Appears in **sidebar only**

### 3.2 Subdomain

- Represents a **real system boundary**
- Owns an **independent lifecycle**
- Has **distinct permissions or sensitivity**
- Would exist even if sibling subdomains didn't
- Appears as **tabs or sections within a domain**

### 3.3 Topic (Order-1)

- A **view** or **capability**
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

### Order Rules

- Sidebar **never changes** with order depth
- Topics stay constant; only **breadcrumb + content** deepen
- Depth is **not implemented as sidebar items**
- Not every order must be a full page (panel/drawer acceptable)
- O5 modals are **terminal** (no navigation inside)

---

## 4. Sidebar Structure

The sidebar must be structured into **three clearly separated sections**:

### 4.1 Core Lenses (Top Section)

```
Overview
Activity
Incidents
Policies
Logs
```

- Primary mental model
- Stable over time
- Maps to industry conventions (Cloudflare / AWS / Datadog)

### 4.2 Connectivity (Middle Section)

```
Integrations
API Keys
```

- Standard industry utilities only
- Not analytical views
- Must not surface system truth
- Must not explain incidents or policies

### 4.3 Account (Secondary Navigation)

Account is **not** a domain. It is **ownership & access management**.

Account appears in **secondary position** (top-right dropdown or footer), **not** in the primary sidebar.

```
Account
  ▸ Projects
  ▸ Users
  ▸ Profile
  ▸ Billing
  ▸ Support
```

**Account Rules:**

- Account is NOT a domain — it manages *who*, *what*, and *billing*, not *what happened*
- Account pages must NOT display executions, incidents, policies, or logs
- Projects are account-scoped containers (not navigation domains)
- Users are account members (developers/operators), not activity subjects
- Matches industry conventions: Cloudflare Account Home, GitHub Org Settings, AWS Account Settings
- No core product insight exposed
- Pure configuration and commercial management

---

## 5. Jurisdiction Boundaries

### 5.1 Customer Console Scope

- **Tenant-scoped only**
- Customer sees only their own:
  - Executions
  - Incidents
  - Policies
  - Spend
  - Logs

### 5.2 Explicit Exclusions

The following concepts are **explicitly excluded** from Customer Console:

| Concept | Belongs To | Reason |
|---------|-----------|--------|
| Founder Pulse | Ops Console | Cross-tenant |
| Discovery Ledger | Ops Console | Learning system |
| Chaos Corpus | Ops Console | Testing infrastructure |
| Cross-tenant intelligence | Ops Console | Multi-tenant data |
| Learned authority | Nowhere (forbidden) | Governance violation |
| Auto-enforcement | Nowhere (forbidden) | Human approval required |

### 5.3 Console Separation

| Console | Scope | Data Boundary |
|---------|-------|---------------|
| Customer Console | Single tenant | Tenant-isolated |
| Founder Console | Cross-tenant | Founder-only |
| Ops Console | Infrastructure | Operator-only |
| Preflight Console | Pre-launch | Reduced depth |

Same themes may exist across consoles, but **data, scope, and authority differ**.

### 5.4 Project Scope (Clarification)

All Customer Console domains, topics, and Orders (O1–O5) are evaluated within a selected **Project context**.

- A Tenant may contain multiple Projects
- Project selection is **global** and **orthogonal** to domain navigation
- Switching Projects changes **data scope only**; it does not change:
  - Domains
  - Sidebar structure
  - Topics
  - Order semantics

**Project Rules:**

- Projects are **account-level containers**
- Projects are managed under **ADMIN** (not Core Lenses)
- Projects are **not domains** and must not appear in the primary sidebar
- Project selector appears in **global header** (not sidebar)
- Cross-project aggregation is **forbidden** in Customer Console

**Shared Resources:**

- Policies may be scoped to `ORG` (all projects) or `PROJECT` (single project)
- Agents may be bound to multiple projects
- Executions are always **project-scoped**
- Incidents attach to executions → always project-scoped

---

## 6. Governance Rules

### 6.1 Power & Authority Constraints

- No global automation
- No learned authority
- No cross-tenant intelligence claims
- No "system decided" language

### 6.2 Action Requirements

All actions must be:

- **Explicit** — declared, not inferred
- **Scoped** — tenant-bounded
- **Attributable** — to a human actor
- **Auditable** — logged immutably

### 6.3 Data Integrity

- Logs and evidence are **immutable**
- No rewriting history
- No "fixing" past traces
- No inferring missing facts
- First truth wins (ON CONFLICT DO NOTHING)

### 6.4 Governed Control (GC_L)

**Added:** 2026-01-06 (PIN-339)

Customers may exercise governed control over their own platform configuration subject to:

1. **Policy Library Constraint** — All configuration must use pre-approved Policy Library templates
2. **Parameter Bounds** — Template parameters have enforced minimum/maximum bounds
3. **Conflict Prevention** — System prevents application of conflicting policies
4. **Audit Trail** — All configuration changes are logged with attribution

**GC_L Authority Hierarchy:**
```
OBSERVE_OWN < GC_L < INVOKE_OWN < MUTATE_OWN < ADMIN
```

**GC_L does NOT allow:**
- Creating arbitrary policies from scratch
- Modifying templates or bounds
- Cross-tenant configuration
- Automatic enforcement without customer action

**Learning Component:**
- System may learn from customer selections for recommendations
- Learning is for **recommendation only** — never enforcement
- Enforcement without human action is **forbidden**
- Policy Library is **mandatory** before any learned policy surfaces

### 6.5 System Facilitation

**Added:** 2026-01-06 (PIN-339)

The system may provide advisory guidance to help customers make safe choices:

1. **Recommendations** — Suggest Policy Library entries based on observed patterns
2. **Warnings** — Alert customers to potentially risky configurations
3. **Alternatives** — Offer safer options when risky choices are made

**FACILITATION does NOT:**
- Block customer choices (except security-critical violations)
- Auto-apply changes
- Override customer decisions
- Use learned authority for enforcement
- **Mutate state** (FACILITATION is read-only advisory)

**Security-Critical Blocking:**
FACILITATION may block only for security-critical violations (e.g., HTTPS required for webhooks).
All other guidance is advisory.

---

## 7. Overview Philosophy

Overview must be **boring, factual, and reassuring**.

It answers only: **"Is anything wrong right now?"**

### What Overview Is

- 3-state status (PROTECTED / ATTENTION / ACTION)
- Max 3 summary cards
- Max 3 recent activity items
- Auto-refresh every 30 seconds (calm, not frantic)

### What Overview Is Not

- Deep actions
- Storytelling
- Learning claims
- Charts or animations
- "Smart" features

**Overview is not where value is demonstrated.**

---

## 8. Deviation Protocol

### 8.1 When Deviation Occurs

Any deviation from this constitution must be:

1. **Explicitly flagged** — state what deviates
2. **Clearly justified** — provide evidence
3. **Not applied automatically** — human approval required

### 8.2 Amendment Process

To amend this constitution:

1. Proposal documented with rationale
2. Impact assessment on existing structure
3. Human review and approval
4. Version increment
5. Playbook updates
6. Behavior rule updates

### 8.3 Forbidden Actions

| Action | Reason |
|--------|--------|
| Rename frozen domains | Breaks mental model |
| Add new domains without amendment | Repositioning risk |
| Merge domains | Collapses distinct questions |
| Mix jurisdictions | Data boundary violation |
| Auto-apply learned patterns | Governance violation |

---

## 9. Claude's Role

### 9.1 Allowed

- Validate existence of objects and flows in codebase
- Report fits, gaps, partial fits, and violations
- Map existing code to approved domains and topics
- Generate drafts for human review
- Flag deviations explicitly

### 9.2 Not Allowed

- Introducing new domains
- Renaming frozen domains
- Mixing customer and founder jurisdictions
- Suggesting automation or learned authority
- Auto-applying structural changes
- "Improving" without explicit approval

### 9.3 Failure Mode to Avoid

> "Claude-suggested improvement" that silently mutates product identity.

---

## 10. Version History

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.3.0 | 2026-01-06 | Added Section 6.4 (GC_L) and 6.5 (FACILITATION) per PIN-339 | Human-approved |
| 1.2.0 | 2025-12-29 | Renamed Administration → Account (secondary nav), clarified Account rules | Human-approved |
| 1.1.0 | 2025-12-29 | Added Project Scope (5.4), Projects to Admin section | Human-approved |
| 1.0.0 | 2025-12-29 | Initial freeze | Human-approved |

---

## 11. References

| Document | Purpose |
|----------|---------|
| `SESSION_PLAYBOOK.yaml` | Enforcement at session start |
| `CLAUDE.md` | Quick reference for contributors |
| `CLAUDE_BEHAVIOR_LIBRARY.md` | Deviation detection rules |
| `docs/memory-pins/INDEX.md` | Project memory |

---

**This constitution is the source of truth for Customer Console v1.**

**Playbooks enforce it. Behavior rules guard it. Humans amend it.**
