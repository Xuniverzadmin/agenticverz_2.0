# Domain Language Guide

**Status:** LOCKED
**Created:** 2026-01-26
**Purpose:** Canonical reference for domain classification decisions

---

## Prime Invariant

> **Keywords do not define domains. Decisions do.**

Generic keywords such as *runtime*, *enforcement*, *threshold*, *governance*, and *policy* have **zero classificatory power** unless qualified by an explicit decision phrase.

Unqualified usage must be treated as **AMBIGUOUS**.

---

## The Qualifier Test

When classifying any file, ask **two questions** in order:

1. **Decision of WHAT?** (What is being decided/enforced/configured?)
2. **Decision for WHOM?** (System invariants or customer-owned?)

| Answer | Domain |
|--------|--------|
| System invariants, execution order, retries | **General** |
| Customer-defined rules | **Policies** |
| Customer-configured limits | **Controls** |
| Problem classification | **Incidents** |
| Run lifecycle facts | **Activity** |
| Derived metrics | **Analytics** |
| Read-only summaries | **Overview** |
| Immutable audit trail | **Logs** |
| External adapters | **Integrations** |
| API key/scope management | **APIs** |
| Tenancy/ownership | **Account** |

---

## Ambiguous Keywords (INVALID as Standalone Signals)

These words **cannot** determine domain classification alone:

| Keyword | Why Ambiguous |
|---------|---------------|
| `enforcement` | System enforcement vs policy enforcement vs limit enforcement |
| `runtime` | Runtime orchestration vs LLM runtime vs runtime config |
| `threshold` | Threshold config vs threshold violation |
| `governance` | System governance vs customer governance rules |
| `policy` | Policy domain vs general policy (ambiguous) |
| `aggregation` | Derived aggregation vs dashboard aggregation |
| `config` | Control config vs integration config vs general config |
| `limit` | Control limit vs rate limit vs scope limit |

**Rule:** If these appear unqualified, classification = **AMBIGUOUS**.

---

## Domain Disambiguation Matrices

### Enforcement

| Qualified Phrase | Domain | Rationale |
|------------------|--------|-----------|
| governance enforcement | **General** | System invariants |
| runtime enforcement | **General** | Execution order |
| gateway enforcement | **General** | Request routing |
| policy enforcement | **Policies** | Customer rules |
| rule enforcement | **Policies** | Customer rules |
| limit enforcement | **Controls** | Customer limits |
| threshold enforcement | **Controls** | Customer thresholds |
| violation enforcement | **Incidents** | Problem response |

---

### Runtime

| Qualified Phrase | Domain | Rationale |
|------------------|--------|-----------|
| runtime orchestration | **General** | Execution coordination |
| runtime coordinator | **General** | Execution coordination |
| execution runtime | **General** | System execution |
| LLM runtime | **Activity** | Run lifecycle |
| run lifecycle | **Activity** | Run lifecycle |
| runtime config | **Controls** | Customer configuration |

---

### Threshold

| Qualified Phrase | Domain | Rationale |
|------------------|--------|-----------|
| threshold config | **Controls** | Customer limits |
| threshold definition | **Controls** | Customer limits |
| threshold violation | **Incidents** | Problem classification |
| near-threshold | **Incidents** | Problem classification |
| threshold evaluation | **Incidents** | Problem classification |

---

### Aggregation

| Qualified Phrase | Domain | Rationale |
|------------------|--------|-----------|
| derived aggregation | **Analytics** | Computed metrics |
| statistical aggregation | **Analytics** | Computed metrics |
| metric aggregation | **Analytics** | Computed metrics |
| dashboard aggregation | **Overview** | Read-only display |
| read-only summary | **Overview** | Read-only display |
| summary view | **Overview** | Read-only display |

---

### Governance

| Qualified Phrase | Domain | Rationale |
|------------------|--------|-----------|
| governance orchestration | **General** | System coordination |
| governance enforcement | **General** | System invariants |
| system governance | **General** | System invariants |
| governance rule | **Policies** | Customer rules |
| customer governance | **Policies** | Customer rules |

---

## Domain Reference Cards

### General

**Exclusive Decision:** WHEN and HOW system actions execute

**Qualifier Test:** Enforcement of system invariants, for system orchestration

**Allowed Phrases:**
- governance orchestration
- runtime orchestration
- execution coordinator
- gateway control
- retry logic
- governance enforcement
- runtime enforcement
- contract activation
- job state tracker
- system-wide orchestration

**Veto Phrases (→ NOT General):**
- policy enforcement → POLICIES
- limit enforcement → CONTROLS
- threshold violation → INCIDENTS
- customer rule → POLICIES
- tenant config → ACCOUNT

---

### Policies

**Exclusive Decision:** WHAT rules govern behavior

**Qualifier Test:** Enforcement of customer-defined rules

**Allowed Phrases:**
- policy definition
- policy evaluation
- policy proposal
- policy enforcement
- rule engine
- lesson learned
- customer rule
- governance rule (customer context)

**Veto Phrases (→ NOT Policies):**
- runtime orchestration → GENERAL
- gateway control → GENERAL
- system invariant → GENERAL

---

### Controls

**Exclusive Decision:** WHAT limits and configurations apply

**Qualifier Test:** Customer-configured limits and thresholds

**Allowed Phrases:**
- killswitch
- circuit breaker
- feature flag
- rate limit
- token limit
- cost limit
- quota config
- threshold config
- limit enforcement
- control config

**Veto Phrases (→ NOT Controls):**
- threshold violation → INCIDENTS
- near-threshold incident → INCIDENTS
- runtime orchestration → GENERAL

---

### Incidents

**Exclusive Decision:** WHETHER an outcome is a problem

**Qualifier Test:** Classification of failures and violations

**Allowed Phrases:**
- incident classification
- failure classification
- threshold violation
- near-threshold
- violation detection
- recovery signal
- incident pattern
- problem classification

**Veto Phrases (→ NOT Incidents):**
- threshold config → CONTROLS
- policy definition → POLICIES

---

### Activity

**Exclusive Decision:** WHAT LLM run occurred

**Qualifier Test:** Run lifecycle and execution metadata

**Allowed Phrases:**
- run lifecycle
- execution metadata
- run state
- llm run
- worker run
- run history
- trace step
- run pattern

**Veto Phrases (→ NOT Activity):**
- runtime orchestration → GENERAL
- policy evaluation → POLICIES

---

### Analytics

**Exclusive Decision:** WHAT can be derived

**Qualifier Test:** Derived metrics, not source-of-truth

**Allowed Phrases:**
- cost intelligence
- statistical analysis
- behavioral analysis
- derived metric
- divergence analysis
- aggregate metric
- kl divergence

**Veto Phrases (→ NOT Analytics):**
- dashboard → OVERVIEW
- summary view → OVERVIEW
- source-of-truth → (wrong layer)

---

### Overview

**Exclusive Decision:** WHAT consolidated state is visible

**Qualifier Test:** Read-only summaries for display

**Allowed Phrases:**
- dashboard
- summary view
- consolidated state
- read-only aggregation
- status overview
- health summary

**Veto Phrases (→ NOT Overview):**
- write → (wrong domain)
- mutate → (wrong domain)
- trigger action → GENERAL

---

### Logs

**Exclusive Decision:** WHAT immutable record exists

**Qualifier Test:** Append-only audit trail

**Allowed Phrases:**
- audit ledger
- audit trail
- append-only
- immutable record
- evidence record
- system log
- proof record

**Veto Phrases (→ NOT Logs):**
- classification → INCIDENTS
- aggregation → ANALYTICS
- mutation → (wrong domain)

---

### Integrations

**Exclusive Decision:** HOW external systems connect

**Qualifier Test:** External adapters and bridges

**Allowed Phrases:**
- sdk setup
- external adapter
- data bridge
- webhook handler
- external auth
- integration config
- connector

**Veto Phrases (→ NOT Integrations):**
- policy decision → POLICIES
- runtime orchestration → GENERAL

---

### APIs

**Exclusive Decision:** WHO can call what

**Qualifier Test:** API key and scope management

**Allowed Phrases:**
- api key
- access scope
- api permission
- key management
- scope definition
- api access control

**Veto Phrases (→ NOT APIs):**
- business logic → (wrong layer)
- policy evaluation → POLICIES

---

### Account

**Exclusive Decision:** WHO owns what

**Qualifier Test:** Tenancy and ownership

**Allowed Phrases:**
- tenant
- subscription
- user role
- membership
- billing
- sub-tenant
- organization

**Veto Phrases (→ NOT Account):**
- runtime → GENERAL
- analytic → ANALYTICS
- policy rule → POLICIES

---

## Classification Rules (LOCKED)

1. **Exclusions are VETOES, not penalties**
   - If a phrase matches but a veto phrase also matches → domain is INVALID

2. **Weak keywords can never exceed phrase signals**
   - Single keywords are tie-breakers only, never primary evidence

3. **If two domains score similarly → AMBIGUOUS, STOP**
   - No forced classification
   - Margin must be >= 3 points

4. **Unqualified ambiguous keywords → AMBIGUOUS**
   - If `enforcement`, `runtime`, `threshold`, etc. appear without qualifier → STOP

---

## Reviewer Checklist

When reviewing domain classification:

- [ ] Does the file contain ambiguous keywords?
- [ ] Are all ambiguous keywords qualified by decision phrases?
- [ ] Does the qualifier test pass? (Decision of WHAT? For WHOM?)
- [ ] Are there any veto phrase matches?
- [ ] Is there sufficient margin between top two candidates?
- [ ] If AMBIGUOUS, is it marked for split analysis?

---

## Anti-Patterns (Avoid)

| Wrong | Right |
|-------|-------|
| "This file mentions enforcement, so it's General" | "What is being enforced, and for whom?" |
| "This has runtime logic" | "Does it decide WHEN execution happens, or describe a run?" |
| "Contains threshold, must be Controls" | "Is this threshold config or threshold violation?" |
| "Has policy in the name" | "Does it define rules or orchestrate execution?" |

---

*Document Status: LOCKED - Changes require explicit approval*
