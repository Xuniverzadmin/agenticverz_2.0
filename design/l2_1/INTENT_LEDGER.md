# Intent Ledger — Customer Console

## Metadata
Authority: Human
Generated: 2026-01-14T18:36:22Z
Status: ACTIVE
Topology: design/l2_1/UI_TOPOLOGY_TEMPLATE.yaml
Grammar: design/l2_1/INTENT_LEDGER_GRAMMAR.md

---

## Topology

This ledger is constrained by UI_TOPOLOGY_TEMPLATE.yaml.

Only panels within these locations are valid.

### OVERVIEW

#### SUMMARY
- HIGHLIGHTS (4 slots)
- COST_INTELLIGENCE (4 slots)
- DECISIONS (4 slots)

### ACTIVITY

#### LLM_RUNS
- LIVE (4 slots)
- COMPLETED (4 slots)
- RISK_SIGNALS (4 slots)

### INCIDENTS

#### EVENTS
- ACTIVE (4 slots)
- RESOLVED (4 slots)
- HISTORICAL (4 slots)

### POLICIES

#### GOVERNANCE
- ACTIVE (4 slots)
- DRAFTS (4 slots)
- POLICY_LIBRARY (4 slots)

#### LIMITS
- USAGE (4 slots)
- THRESHOLDS (4 slots)
- VIOLATIONS (4 slots)

### LOGS

#### RECORDS
- LLM_RUNS (4 slots)
- SYSTEM_LOGS (4 slots)
- AUDIT (4 slots)

### ANALYTICS

#### COST
- USAGE (5 slots)

### ACCOUNT

#### PROFILE
- OVERVIEW (2 slots)

#### BILLING
- USAGE (2 slots)
- INVOICES (2 slots)

#### USERS_ACCESS
- MEMBERS (2 slots)
- ROLES (1 slot)

#### TRUST_COMPLIANCE
- COMPLIANCE (2 slots)

### CONNECTIVITY

#### PROVIDERS
- STATUS (2 slots)
- LIMITS (1 slot)

#### NETWORK
- PATHS (2 slots)

#### CREDENTIALS_SECRETS
- KEYS (2 slots)

#### HEALTH_DIAGNOSTICS
- ERRORS (2 slots)

---

## Facets

Facets are semantic groupings of information needs that span multiple panels.
They provide context for why panels exist together without affecting pipeline mechanics.

**Grammar:** See INTENT_LEDGER_GRAMMAR.md Section "Facet Entry Grammar"

### Facet: system_health_overview
Purpose: Operators need a quick snapshot of overall system health
Criticality: HIGH
Domain: OVERVIEW

Panels:
- OVR-SUM-HL-O1 (activity snapshot)
- OVR-SUM-HL-O2 (incident snapshot)
- OVR-SUM-HL-O4 (policy snapshot)

### Facet: cost_intelligence
Purpose: Operators must understand cost consumption and anomalies
Criticality: HIGH
Domain: OVERVIEW

Panels:
- OVR-SUM-CI-O1 (cost summary)
- OVR-SUM-CI-O2 (cost by feature)
- OVR-SUM-CI-O3 (cost by model)
- OVR-SUM-CI-O4 (cost anomalies)

### Facet: active_execution_monitoring
Purpose: Track currently running and recently completed executions
Criticality: HIGH
Domain: ACTIVITY

Panels:
- ACT-LLM-LIVE-O1 (live runs)
- ACT-LLM-LIVE-O3 (jobs list)
- ACT-LLM-LIVE-O4 (worker runs)
- ACT-LLM-LIVE-O5 (health status)
- ACT-LLM-COMP-O1 (completed runs)
- ACT-LLM-COMP-O2 (summary)

### Facet: execution_signals
Purpose: Surface predictions, anomalies, and risk signals from executions
Criticality: MEDIUM
Domain: ACTIVITY

Panels:
- ACT-LLM-SIG-O1 (signals)
- ACT-LLM-SIG-O2 (predictions list)
- ACT-LLM-SIG-O3 (predictions summary)
- ACT-LLM-SIG-O4 (anomaly detection)

### Facet: incident_lifecycle
Purpose: Track incidents from detection through resolution to history
Criticality: HIGH
Domain: INCIDENTS

Panels:
- INC-EV-ACT-O1 (active incidents list)
- INC-EV-ACT-O2 (incident details)
- INC-EV-ACT-O3 (incident timeline)
- INC-EV-RES-O1 (resolved list)
- INC-EV-RES-O2 (resolution details)
- INC-EV-HIST-O1 (historical incidents)
- INC-EV-HIST-O2 (incident trends)

### Facet: policy_governance
Purpose: Manage active policies and policy proposals
Criticality: HIGH
Domain: POLICIES

Panels:
- POL-GOV-ACT-O1 (active policies)
- POL-GOV-ACT-O2 (policy details)
- POL-GOV-DFT-O1 (lessons list - under LESSONS topic)
- POL-GOV-DFT-O2 (lesson stats - under LESSONS topic)
- POL-GOV-DFT-O3 (lesson detail - under LESSONS topic)
- POL-GOV-DFT-O4 (convert to draft - under LESSONS topic)
- POL-GOV-DFT-O5 (defer lesson - under LESSONS topic)
- POL-GOV-LES-O6 (learning insights - under LESSONS topic)
- POL-GOV-LES-O7 (learning proposals - under LESSONS topic)
- POL-GOV-LIB-O1 (policy templates)
- POL-GOV-LIB-O2 (ethical constraints)

### Facet: limit_violations
Purpose: Track usage limits and violation events
Criticality: HIGH
Domain: POLICIES

Panels:
- POL-LIM-CTR-O1 (controls overview)
- POL-LIM-CTR-O2 (control details)
- POL-LIM-CTR-O3 (set execution controls)
- POL-LIM-VIO-O1 (violations list)
- POL-LIM-VIO-O2 (violation details)

### Facet: execution_traces
Purpose: Provide execution trace logs for debugging and audit
Criticality: MEDIUM
Domain: LOGS

Panels:
- LOG-REC-LLM-O1 (run logs)
- LOG-REC-LLM-O2 (run trace details)
- LOG-REC-SYS-O1 (system logs summary)
- LOG-REC-SYS-O2 (system log entries)

### Facet: audit_trail
Purpose: Maintain immutable audit log for compliance
Criticality: HIGH
Domain: LOGS

Panels:
- LOG-REC-AUD-O1 (audit log)
- LOG-REC-AUD-O2 (audit event details)

### Facet: account_identity
Purpose: Manage organization identity and profile
Criticality: MEDIUM
Domain: ACCOUNT

Panels:
- ACC-PR-OV-O1 (account identity)
- ACC-PR-OV-O2 (admin contacts)

### Facet: billing_usage
Purpose: Track billing, usage, and invoices
Criticality: MEDIUM
Domain: ACCOUNT

Panels:
- ACC-BL-US-O1 (usage summary)
- ACC-BL-US-O2 (cost trend)
- ACC-BL-IN-O1 (invoice list)
- ACC-BL-IN-O2 (invoice export)

### Facet: connectivity_health
Purpose: Monitor provider connectivity and health
Criticality: HIGH
Domain: CONNECTIVITY

Panels:
- CON-PR-ST-O1 (provider status)
- CON-PR-ST-O2 (provider details)
- CON-HD-ER-O1 (connection errors)
- CON-HD-ER-O2 (error details)

---

## Policy Clauses

Policy clauses define non-negotiable control-plane rules for capability surfaces.
Violations are architectural incidents, not implementation bugs.

### Policy: TOPIC-SCOPED-ENDPOINT-001

**Title:** Topic Determines Data Scope, Not Caller

**Status:** ACTIVE
**Effective:** 2026-01-18
**Applies To:** Any capability serving multiple topics with distinct data boundaries

**Problem Statement:**
When a capability (e.g., `activity.runs_by_dimension`) serves panels in different topics
(LIVE vs COMPLETED), the data scope must be enforced at the API boundary.
Caller-controlled filtering (query params, headers) creates:
- Data leakage risk (LIVE panel showing COMPLETED data)
- Frontend misconfiguration surface
- Silent correctness failures
- "Why is LIVE showing completed?" incidents

**Rule (Non-Negotiable):**

> **Topic semantics MUST be enforced at the endpoint, not by the caller.**

**Required Design Pattern:**

1. **Single Capability** — Semantic contract remains unified
2. **Topic-Scoped Endpoints** — Separate URLs with hardcoded state binding
3. **Implicit Filtering** — State injected by endpoint, never from request
4. **Non-Overrideable** — No query param or header can change scope

**Endpoint Naming Convention:**
```
/api/v1/{domain}/{resource}/{topic}/by-{dimension}
```

Examples:
- `/api/v1/activity/runs/live/by-dimension` → state=LIVE (hardcoded)
- `/api/v1/activity/runs/completed/by-dimension` → state=COMPLETED (hardcoded)

**Generic Endpoint Disposition:**
If a generic endpoint exists (e.g., `/runs/by-dimension` with optional state param):
- MUST NOT be bound to any panel
- MUST be marked internal/admin-only
- SHOULD be deprecated if no admin use case exists

**Capability Mapping:**
```yaml
capability_id: activity.runs_by_dimension
endpoints:
  - /api/v1/activity/runs/live/by-dimension      # LIVE topic
  - /api/v1/activity/runs/completed/by-dimension # COMPLETED topic
semantic_contract: "Distribution by dimension, topic-scoped"
```

**Violation Classification:**
- Exposing caller-controlled state filter to panel → **CONTROL-PLANE VIOLATION**
- Panel calling generic endpoint instead of topic-scoped → **BINDING VIOLATION**
- Frontend implementing conditional state logic → **NOISE VIOLATION**

**Audit Requirement:**
Any capability serving multiple topics MUST declare:
1. Which topics it serves
2. Which endpoint serves which topic
3. Confirmation that state binding is implicit

---

## Panels

### Panel: ACC-PR-OV-O1

Location:
- Domain: ACCOUNT
- Subdomain: PROFILE
- Topic: OVERVIEW
- Slot: 1

Class: interpretation
State: EMPTY

Purpose:
Account identity summary (org name, plan, region)

Capability: null

### Panel: ACC-PR-OV-O2

Location:
- Domain: ACCOUNT
- Subdomain: PROFILE
- Topic: OVERVIEW
- Slot: 2

Class: interpretation
State: EMPTY

Purpose:
Primary owner & admin contacts

Capability: null

### Panel: ACC-BL-US-O1

Location:
- Domain: ACCOUNT
- Subdomain: BILLING
- Topic: USAGE
- Slot: 1

Class: interpretation
State: EMPTY

Purpose:
Usage summary (tokens, runs, spend)

Capability: null

### Panel: ACC-BL-US-O2

Location:
- Domain: ACCOUNT
- Subdomain: BILLING
- Topic: USAGE
- Slot: 2

Class: interpretation
State: EMPTY

Purpose:
Cost trend & burn rate

Capability: null

### Panel: ACC-BL-IN-O1

Location:
- Domain: ACCOUNT
- Subdomain: BILLING
- Topic: INVOICES
- Slot: 1

Class: evidence
State: EMPTY

Purpose:
Invoice list & status

Capability: null

### Panel: ACC-BL-IN-O2

Location:
- Domain: ACCOUNT
- Subdomain: BILLING
- Topic: INVOICES
- Slot: 2

Class: execution
State: EMPTY

Purpose:
Download / export invoices

Capability: null

### Panel: ACC-UA-MB-O1

Location:
- Domain: ACCOUNT
- Subdomain: USERS_ACCESS
- Topic: MEMBERS
- Slot: 1

Class: evidence
State: EMPTY

Purpose:
User list with roles

Capability: null

### Panel: ACC-UA-MB-O2

Location:
- Domain: ACCOUNT
- Subdomain: USERS_ACCESS
- Topic: MEMBERS
- Slot: 2

Class: execution
State: EMPTY

Purpose:
Invite / deactivate users

Capability: null

### Panel: ACC-UA-RL-O1

Location:
- Domain: ACCOUNT
- Subdomain: USERS_ACCESS
- Topic: ROLES
- Slot: 1

Class: evidence
State: EMPTY

Purpose:
Role definitions & permissions

Capability: null

### Panel: ACC-TC-CP-O1

Location:
- Domain: ACCOUNT
- Subdomain: TRUST_COMPLIANCE
- Topic: COMPLIANCE
- Slot: 1

Class: interpretation
State: EMPTY

Purpose:
Compliance status (SOC2, ISO, etc.)

Capability: null

### Panel: ACC-TC-CP-O2

Location:
- Domain: ACCOUNT
- Subdomain: TRUST_COMPLIANCE
- Topic: COMPLIANCE
- Slot: 2

Class: execution
State: EMPTY

Purpose:
Evidence export (for auditors / CTO)

Capability: null

### Panel: CON-PR-ST-O1

Location:
- Domain: CONNECTIVITY
- Subdomain: PROVIDERS
- Topic: STATUS
- Slot: 1

Class: interpretation
State: EMPTY

Purpose:
Connected LLM providers (OpenAI, Anthropic, etc.)

Capability: null

### Panel: CON-PR-ST-O2

Location:
- Domain: CONNECTIVITY
- Subdomain: PROVIDERS
- Topic: STATUS
- Slot: 2

Class: interpretation
State: EMPTY

Purpose:
Provider health & outages

Capability: null

### Panel: CON-PR-LM-O1

Location:
- Domain: CONNECTIVITY
- Subdomain: PROVIDERS
- Topic: LIMITS
- Slot: 1

Class: evidence
State: EMPTY

Purpose:
Provider rate limits & quotas

Capability: null

### Panel: CON-NW-PT-O1

Location:
- Domain: CONNECTIVITY
- Subdomain: NETWORK
- Topic: PATHS
- Slot: 1

Class: interpretation
State: EMPTY

Purpose:
Network paths & routing overview

Capability: null

### Panel: CON-NW-PT-O2

Location:
- Domain: CONNECTIVITY
- Subdomain: NETWORK
- Topic: PATHS
- Slot: 2

Class: interpretation
State: EMPTY

Purpose:
Latency & failure points

Capability: null

### Panel: CON-CS-KY-O1

Location:
- Domain: CONNECTIVITY
- Subdomain: CREDENTIALS_SECRETS
- Topic: KEYS
- Slot: 1

Class: evidence
State: EMPTY

Purpose:
API keys & secret references

Capability: null

### Panel: CON-CS-KY-O2

Location:
- Domain: CONNECTIVITY
- Subdomain: CREDENTIALS_SECRETS
- Topic: KEYS
- Slot: 2

Class: interpretation
State: EMPTY

Purpose:
Rotation status & expiry risk

Capability: null

### Panel: CON-HD-ER-O1

Location:
- Domain: CONNECTIVITY
- Subdomain: HEALTH_DIAGNOSTICS
- Topic: ERRORS
- Slot: 1

Class: evidence
State: EMPTY

Purpose:
Connection failures & retries

Capability: null

### Panel: CON-HD-ER-O2

Location:
- Domain: CONNECTIVITY
- Subdomain: HEALTH_DIAGNOSTICS
- Topic: ERRORS
- Slot: 2

Class: interpretation
State: EMPTY

Purpose:
Degraded connectivity alerts

Capability: null

### Panel: OVR-SUM-HL-O1

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: HIGHLIGHTS
- Slot: 1

Class: interpretation
State: BOUND

Purpose:
Provide a single, glanceable snapshot of current system activity so the user
can immediately understand whether the system is calm, active, or stressed.

What it shows:
- Count of currently running LLM executions
- Count of executions completed in the last window (e.g. 15 min)
- Count of executions currently in near-threshold or risk state
- Timestamp of last successful observation update

What it explicitly does NOT show:
- No logs
- No configuration
- No historical charts
- No per-run drilldown
- No policy or cost breakdown

Capability: overview.highlights

### Panel: OVR-SUM-HL-O2

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: HIGHLIGHTS
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Surface non-ignorable signals that require human attention,
without requiring navigation into domains.

What it shows:
- Count of active incidents (any severity)
- Count of runs currently in near-threshold state
- Count of policy violations prevented by governance
- Highest severity level currently present (if any)

What it explicitly does NOT show:
- No historical incidents
- No explanations
- No root cause
- No controls or actions
- No links or drilldowns

Capability: overview.incident_snapshot

### Panel: OVR-SUM-HL-O3

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: HIGHLIGHTS
- Slot: 3

Class: interpretation
State: EMPTY

Purpose:
Surface emerging pattern shifts across domains — non-obvious directional change
that is not yet an incident but is statistically meaningful.

What it shows:
- Week-over-week deltas in failure ratios, near-threshold frequency
- Prevention counts and escalation latency trends
- Trigger frequency and auto-prevent vs override ratio changes
- Approach-to-limit velocity shifts
- Change-point detection (z-score / percentile shift)

What it explicitly does NOT show:
- No alerts or actions
- No raw data
- No incident details
- No policy editing

Capability: null

### Panel: OVR-SUM-HL-O4

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: HIGHLIGHTS
- Slot: 4

Class: interpretation
State: DRAFT

Purpose:
Expose rare but high-impact clusters — low-frequency, high-cost events
invisible in averages.

What it shows:
- Severity-weighted cost/time loss ranking
- Long-tail outliers (top 1-2%)
- Extreme run duration/cost spikes
- Overridden violations with high blast radius
- Impact-ranked clusters by LLM, agent, human, policy

What it explicitly does NOT show:
- No count-based rankings
- No actions or controls
- No policy editing
- No drill-down beyond identification

Capability: overview.policy_snapshot

### Panel: OVR-SUM-DC-O1

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: DECISIONS
- Slot: 1

Class: interpretation
State: DRAFT

Purpose:
Surface decisions that require explicit human approval or rejection,
without forcing navigation into policies or incidents.

What it shows:
- Count of pending policy approvals
- Count of blocked runs awaiting human override
- Count of escalations requiring approval/reject decision
- Oldest pending decision age (time-based pressure)

What it explicitly does NOT show:
- No execution buttons
- No approval/reject actions
- No policy details
- No explanations or rationale
- No historical decisions

Capability: overview.decisions_list

### Panel: OVR-SUM-DC-O2

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: DECISIONS
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Provide short-term feedback on recent human decisions so the user
can confirm impact without drilling into other domains.

What it shows:
- Last N decisions taken (approve / reject / override)
- Resulting outcome state (resolved / still pending / failed)
- Time-to-effect (decision → outcome)

What it explicitly does NOT show:
- No ability to re-open or change decisions
- No policy configuration
- No incident details
- No execution controls
- No historical archive beyond recent window

Capability: overview.decisions_count

### Panel: OVR-SUM-DC-O3

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: DECISIONS
- Slot: 3

Class: interpretation
State: DRAFT

Purpose:
Identify recurrent human decisions that should become policy —
where humans are acting as rate limiters instead of governance.

What it shows:
- Repeated decision patterns (same condition, same outcome, same actors)
- Frequency × avoided effort × avoided cost ranking
- Cost-overrun overrides approved repeatedly
- Manual allowlist decisions trending up
- Direct links to Policies → Drafts and Limits → Thresholds (pre-filled context)

What it explicitly does NOT show:
- No execution or approval actions
- No policy editing
- No incident details

Capability: overview.recovery_stats

### Panel: OVR-SUM-DC-O4

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: DECISIONS
- Slot: 4

Class: interpretation
State: DRAFT

Purpose:
Show decisions avoided by governance — where the system already removed
decision load successfully, reinforcing trust in automation.

What it shows:
- Auto-prevent counts (decisions not escalated)
- Avoidance attribution: by policy, by limit, by automation
- Trust progression tracking
- Policies that avoided human interventions
- Agents/LLMs now fully governed (no manual touch for N days)

What it explicitly does NOT show:
- No execution controls
- No policy editing
- No approval actions

Capability: overview.decisions

### Panel: OVR-SUM-CI-O1

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: COST_INTELLIGENCE
- Slot: 1

Class: interpretation
State: DRAFT

Purpose:
Give an immediate snapshot of current cost posture without requiring
navigation into Activity or Policies.

What it shows:
- Current spend rate (aggregate)
- Trend indicator (up / flat / down)
- Primary cost driver (top contributor category)

What it explicitly does NOT show:
- No historical charts
- No per-run breakdown
- No policy configuration
- No thresholds or limits editing
- No predictions

Capability: overview.cost_summary

### Panel: OVR-SUM-CI-O2

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: COST_INTELLIGENCE
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Show how total cost is distributed across primary drivers so the user
understands what is consuming money at a glance.

What it shows:
- Cost split by driver category (e.g., model, project, policy bucket)
- Percentage contribution per driver
- Top 1–3 contributors only

What it explicitly does NOT show:
- No per-run or per-request logs
- No time-series charts
- No configuration controls
- No thresholds or alerts
- No forecasts

Capability: overview.costs

### Panel: OVR-SUM-CI-O3

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: COST_INTELLIGENCE
- Slot: 3

Class: interpretation
State: DRAFT

Purpose:
Provide a short-horizon view of cost movement so the user can tell
whether spend is trending up, flat, or down.

What it shows:
- Aggregate cost trend over a short window (e.g., last N periods)
- Directional indicator only (↑ ↓ →)
- Relative change, not absolute detail

What it explicitly does NOT show:
- No driver-level breakdown
- No per-run or per-model detail
- No long-term forecasting
- No alerts or policy thresholds
- No controls

Capability: overview.costs

### Panel: OVR-SUM-CI-O4

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: COST_INTELLIGENCE
- Slot: 4

Class: interpretation
State: DRAFT

Purpose:
Provide a near-term cost trajectory based on recent behavior,
so the user can anticipate direction without detailed forecasting.

What it shows:
- Near-term projected direction (increase / stable / decrease)
- Confidence band or qualitative confidence (low / medium / high)
- Projection based on recent trend only

What it explicitly does NOT show:
- No long-range forecasts
- No scenario modeling
- No "what-if" controls
- No policy or alert thresholds
- No per-run or per-model detail

Capability: overview.costs

### Panel: ACT-LLM-LIVE-O1

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: LIVE
- Slot: 1

Class: interpretation
State: DRAFT

Purpose:
Show how many LLM runs are currently in progress.

What it shows:
- Total number of live LLM runs

What it explicitly does NOT show:
- No breakdown by model, agent, user, or cost
- No status reasons
- No controls

Capability: activity.live_runs

### Panel: ACT-LLM-LIVE-O2

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: LIVE
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Surface live runs exceeding expected execution time.

What it shows:
- Count of live runs exceeding time threshold (e.g., > X minutes)
- Runs flagged as AT_RISK or VIOLATED for execution time

What it explicitly does NOT show:
- No root cause
- No cost data
- No termination control

Capability: activity.risk_signals

### Panel: ACT-LLM-LIVE-O3

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: LIVE
- Slot: 3

Class: interpretation
State: DRAFT

Purpose:
Highlight live runs that are approaching failure or limits.

What it shows:
- Count of live runs flagged as near-threshold or unstable

What it explicitly does NOT show:
- No policy actions
- No manual override
- No mitigation controls

Capability: activity.live_runs

### Panel: ACT-LLM-LIVE-O4

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: LIVE
- Slot: 4

Class: interpretation
State: DRAFT

Purpose:
Indicate whether telemetry, logs, and traces are flowing for live runs.

What it shows:
- Percentage or status of live runs emitting evidence

What it explicitly does NOT show:
- No log contents
- No replay
- No export

Capability: activity.runtime_traces

### Panel: ACT-LLM-LIVE-O5

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: LIVE
- Slot: 5

Class: interpretation
State: DRAFT

Purpose:
Provide a coarse distribution of live runs by major dimension.

What it shows:
- Distribution by LLM provider, agent, source, risk level, status, or cost
- Dimension selector buttons to switch views (LIVE topic-scoped):
  - By Provider → /runs/live/by-dimension?dim=provider_type
  - By Source → /runs/live/by-dimension?dim=source
  - By Agent → /runs/live/by-dimension?dim=agent_id
  - By Risk → /runs/live/by-dimension?dim=risk_level
  - By Status → /summary/by-status (future: /summary/live/by-status)
  - By Cost → /cost-analysis (future: /cost-analysis/live)
- NOTE: Per Policy TOPIC-SCOPED-ENDPOINT-001, state=LIVE is hardcoded at endpoint

What it explicitly does NOT show:
- No drill-down
- No per-run detail
- No controls

Capability: activity.runs_by_dimension

NOTE: This panel also uses activity.summary_by_status (shared with COMP-O2)
and activity.cost_analysis (shared with SIG-O4) as secondary data sources.

### Panel: ACT-LLM-COMP-O1

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: COMPLETED
- Slot: 1

Class: interpretation
State: DRAFT

Purpose:
Show how many LLM runs have completed in the selected window.

What it shows:
- Total completed runs count

What it explicitly does NOT show:
- No success/failure split
- No duration
- No cost

Capability: activity.completed_runs

### Panel: ACT-LLM-COMP-O2

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: COMPLETED
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Surface how many completed runs finished successfully.

What it shows:
- Count of successful runs

What it explicitly does NOT show:
- No quality scoring
- No downstream impact
- No policy attribution

Capability: activity.summary_by_status

### Panel: ACT-LLM-COMP-O3

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: COMPLETED
- Slot: 3

Class: interpretation
State: DRAFT

Purpose:
Expose completed runs that ended in failure.

What it shows:
- Count of failed runs (from status breakdown)
- Uses FAILED bucket from summary_by_status

What it explicitly does NOT show:
- No root cause
- No retry controls
- No blame attribution

Capability: activity.summary_by_status

### Panel: ACT-LLM-COMP-O4

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: COMPLETED
- Slot: 4

Class: interpretation
State: DRAFT

Purpose:
Highlight runs that completed but came close to limits.

What it shows:
- Count of completed runs that were near:
  - Cost limits
  - Time limits
  - Token limits

What it explicitly does NOT show:
- No violations
- No enforcement
- No tuning actions

Capability: activity.completed_runs

### Panel: ACT-LLM-COMP-O5

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: COMPLETED
- Slot: 5

Class: interpretation
State: DRAFT

Purpose:
Show runs that ended intentionally before completion.

What it shows:
- Count of aborted or cancelled runs

What it explicitly does NOT show:
- No initiator identity
- No reason codes
- No recovery options

Capability: activity.run_detail

### Panel: ACT-LLM-SIG-O1

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: SIGNALS
- Slot: 1

Class: interpretation
State: DRAFT

Purpose:
Surface what is happening right now that matters — the primary attention surface.

What it shows:
- Critical failures
- Critical successes
- Active risk conditions
- Only currently active or very recent signals

What it explicitly does NOT show:
- No historical signals
- No controls or actions
- No policy execution

Capability: activity.signals

### Panel: ACT-LLM-SIG-O2

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: SIGNALS
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Surface runs approaching failure, policy, or cost limits (threshold proximity).

What it shows:
- Token limits nearing breach
- Cost ceilings approaching
- Timeouts nearing SLA breach
- Frequency/rate-limit pressure

What it explicitly does NOT show:
- No actions or mitigations
- No policy controls
- No historical trends

Capability: activity.signals

### Panel: ACT-LLM-SIG-O3

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: SIGNALS
- Slot: 3

Class: interpretation
State: DRAFT

Purpose:
Surface temporal signals — behavior patterns over time indicating instability.

What it shows:
- Frequent retries
- Latency spikes
- Repeated partial failures
- Flapping success/failure patterns

What it explicitly does NOT show:
- No single-event failures (patterns only)
- No root cause analysis
- No remediation controls

Capability: activity.patterns

### Panel: ACT-LLM-SIG-O4

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: SIGNALS
- Slot: 4

Class: interpretation
State: DRAFT

Purpose:
Surface economic deviations — where money is being lost or saved unexpectedly.

What it shows:
- Cost overruns
- Cost savers (first-class signals)
- Efficiency anomalies
- Unexpected cost spikes or drops

What it explicitly does NOT show:
- No budget controls
- No policy enforcement
- No historical cost trends

Capability: activity.cost_analysis

### Panel: ACT-LLM-SIG-O5

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: SIGNALS
- Slot: 5

Class: interpretation
State: DRAFT

Purpose:
Synthesize attention priority — what to look at first and why.

What it shows:
- Prioritized attention queue combining:
  - Severity (O1)
  - Proximity (O2)
  - Pattern persistence (O3)
  - Economic impact (O4)
- Grouping by LLM, Agent, or Human
- Cross-cutting issues

What it explicitly does NOT show:
- No decisions or actions
- No policy execution
- No drill-down details

Capability: activity.signals

### Panel: INC-EV-ACT-O1

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: ACTIVE
- Slot: 1

Class: evidence
State: DRAFT

Purpose:
Show the canonical set of currently active incidents.

What it shows:
- Failures (hard policy violation)
- Near-threshold escalations (policy-defined)
- Prevented overruns (policy intervened)
- Governance-triggered halts
- One row = one incident (no aggregation)

What it explicitly does NOT show:
- No trends or interpretation
- No raw signals (those are in Activity)
- No actions or controls

Capability: incidents.active_list

### Panel: INC-EV-ACT-O2

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: ACTIVE
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Explain why each incident occurred — cause and trigger classification.

What it shows:
- Triggering condition (cost threshold, token limit, time SLA, policy rule)
- Whether detected after violation or prevented before violation

What it explicitly does NOT show:
- No blame attribution
- No actions or remediation
- No policy editing

Capability: incidents.active_list

### Panel: INC-EV-ACT-O3

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: ACTIVE
- Slot: 3

Class: interpretation
State: DRAFT

Purpose:
Show control state — whether each incident is contained or still dangerous.

What it shows:
- Still active / paused / quarantined
- Human override applied or not
- Auto-remediation attempted or not
- Guardrails holding or breached

What it explicitly does NOT show:
- No escalation actions
- No policy changes
- No resolution controls

Capability: incidents.metrics_v2

### Panel: INC-EV-ACT-O4

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: ACTIVE
- Slot: 4

Class: interpretation
State: DRAFT

Purpose:
Show impact assessment — actual damage or prevented damage.

What it shows:
- Actual cost incurred
- Cost prevented by policy
- Downtime / latency impact
- Business impact classification (if available)
- Prevented damage is first-class

What it explicitly does NOT show:
- No cost controls
- No budget editing
- No forecasts

Capability: incidents.cost_impact

### Panel: INC-EV-ACT-O5

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: ACTIVE
- Slot: 5

Class: interpretation
State: DRAFT

Purpose:
Provide attribution and escalation context for each incident.

What it shows:
- Attribution by LLM, Agent, Human, Policy
- Repeated incident marker
- Linked past incidents (if any)
- Escalation eligibility (yes/no)

What it explicitly does NOT show:
- No approval actions
- No policy changes
- No resolution execution

Capability: incidents.active_list

### Panel: INC-EV-RES-O1

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: RESOLVED
- Slot: 1

Class: evidence
State: DRAFT

Purpose:
Show the canonical list of recently resolved incidents.

What it shows:
- Incidents transitioned from Active → Resolved
- Within the recent window (not long-term history)
- Resolution timestamp mandatory
- Original incident ID preserved

What it explicitly does NOT show:
- No active incidents
- No historical aggregation
- No controls

Capability: incidents.resolved_list_v2

### Panel: INC-EV-RES-O2

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: RESOLVED
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Show how each incident was resolved — resolution method.

What it shows:
- Automatic recovery
- Policy enforcement succeeded
- Human override
- Manual intervention
- System rollback
- External dependency recovery
- Each incident maps to exactly one primary resolution method

What it explicitly does NOT show:
- No resolution actions
- No policy editing

Capability: incidents.learnings

### Panel: INC-EV-RES-O3

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: RESOLVED
- Slot: 3

Class: interpretation
State: DRAFT

Purpose:
Show time-to-resolution (TTR) and SLA compliance.

What it shows:
- Detection time
- Resolution time
- Total duration in exception
- SLA classification (within / breached)

What it explicitly does NOT show:
- No contextual judgment
- No policy adjustments
- No controls

Capability: incidents.metrics_v2

### Panel: INC-EV-RES-O4

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: RESOLVED
- Slot: 4

Class: interpretation
State: DRAFT

Purpose:
Show outcome and impact post-resolution — the final reality.

What it shows:
- Final cost incurred
- Cost prevented
- Residual impact (if any)
- Side effects introduced by resolution

What it explicitly does NOT show:
- No projections
- No forecasts
- No policy controls

Capability: incidents.resolved_list_v2

### Panel: INC-EV-RES-O5

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: RESOLVED
- Slot: 5

Class: interpretation
State: DRAFT

Purpose:
Surface learning and follow-up signals from resolved incidents.

What it shows:
- Policy change suggested (yes/no)
- Recurrence risk (low/medium/high)
- Similar past incidents detected
- Escalate to: Policies / Humans / Engineering backlog

What it explicitly does NOT show:
- No policy edits
- No approvals
- No automated actions

Capability: incidents.learnings

### Panel: INC-EV-HIST-O1

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: HISTORICAL
- Slot: 1

Class: interpretation
State: DRAFT

Purpose:
Show incident volume and trend baseline over time.

What it shows:
- Incident counts by time window (day / week / month)
- Trend direction (rising, flat, declining)
- Aggregates only (no per-incident rows)

What it explicitly does NOT show:
- No individual incidents
- No real-time data
- No controls

Capability: incidents.historical_trend

### Panel: INC-EV-HIST-O2

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: HISTORICAL
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Show incident type distribution over time.

What it shows:
- Failure type distribution (success breach, failure, near-threshold)
- Policy-related vs non-policy
- Cost-related vs performance-related
- Infrastructure vs model vs human-triggered

What it explicitly does NOT show:
- No individual incidents
- No real-time data
- No controls

Capability: incidents.historical_distribution

### Panel: INC-EV-HIST-O3

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: HISTORICAL
- Slot: 3

Class: interpretation
State: DRAFT

Purpose:
Show repeatability and recurrence analysis — which incidents keep coming back.

What it shows:
- Same root cause recurring
- Same policy involved repeatedly
- Same agent / LLM / human role involved
- Short recurrence intervals

What it explicitly does NOT show:
- No blame attribution
- No policy changes
- No actions

Capability: incidents.recurring

### Panel: INC-EV-HIST-O4

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: HISTORICAL
- Slot: 4

Class: interpretation
State: DRAFT

Purpose:
Show cost and impact over time — true economic footprint.

What it shows:
- Total cost incurred
- Total cost prevented (via governance)
- Cost avoided vs cost paid ratio
- Long-term cost trend
- Finalized costs only (no forecasts)

What it explicitly does NOT show:
- No budget controls
- No projections
- No real-time data

Capability: incidents.historical_cost_trend

### Panel: INC-EV-HIST-O5

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: HISTORICAL
- Slot: 5

Class: interpretation
State: DRAFT

Purpose:
Surface systemic signals and governance pressure from historical patterns.

What it shows:
- Policies with chronic incident association
- Thresholds consistently too tight or too loose
- Areas where human overrides dominate
- Domains where automation underperforms

What it explicitly does NOT show:
- No policy execution
- No approvals
- No automated actions

Capability: incidents.patterns

### Panel: POL-GOV-ACT-O1

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: ACTIVE
- Slot: 1

Class: evidence
State: DRAFT

Purpose:
Show the complete inventory of currently active (enabled + enforced) policies.

What it shows:
- List/count of all active policies
- Grouped by policy type (cost, rate, approval, safety, escalation)
- Grouped by scope (global / domain / agent / LLM / user)
- Grouped by enforcement mode (hard block / soft block / require approval)

What it explicitly does NOT show:
- No impact metrics
- No drafts or proposals
- No historical policies

Capability: policies.active_policies

### Panel: POL-GOV-ACT-O2

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: ACTIVE
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Show enforcement effectiveness — are policies actually doing anything.

What it shows:
- Per policy: times evaluated, triggered, enforced, bypassed
- Dead policies (never triggered)
- Over-firing policies
- Policies with zero real-world impact

What it explicitly does NOT show:
- No policy editing
- No recommendations
- No draft proposals

Capability: policies.metrics

### Panel: POL-GOV-ACT-O3

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: ACTIVE
- Slot: 3

Class: interpretation
State: DRAFT

Purpose:
Show incident prevention and regulation impact — what policies are preventing or shaping.

What it shows:
- Incidents prevented entirely
- Incidents soft-regulated (slowed, capped, gated)
- Incidents escalated to human decision
- Policy → incident class mapping
- Evidence-backed only (claimed prevention without observation ignored)

What it explicitly does NOT show:
- No policy changes
- No enforcement controls
- No draft proposals

Capability: policies.requests

### Panel: POL-GOV-ACT-O4

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: ACTIVE
- Slot: 4

Class: interpretation
State: DRAFT

Purpose:
Show cost and performance side effects — what governance is costing us.

What it shows:
- Cost saved by enforcement
- Cost introduced by enforcement (latency, friction, rejects)
- Trade-offs: safety vs throughput, cost vs success rate, automation vs human load
- Numbers only, no value judgment

What it explicitly does NOT show:
- No policy tuning controls
- No recommendations
- No forecasts

Capability: policies.layer_state

### Panel: POL-GOV-ACT-O5

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: ACTIVE
- Slot: 5

Class: interpretation
State: DRAFT

Purpose:
Surface governance stress and decision signals — which policies need review.

What it shows:
- Policies with frequent overrides
- Policies frequently hit near thresholds
- Policies causing cascading blocks
- Policies correlated with user/system friction
- Candidates for adjustment, split, promotion, or decommissioning

What it explicitly does NOT show:
- No policy state changes
- No disabling
- No auto-rewriting

Capability: policies.metrics

### Panel: POL-GOV-DFT-O1

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: LESSONS
- Slot: 1

Class: evidence
State: DRAFT

Purpose:
Show observed governance signals — raw lessons from system behavior.

What it shows:
- Critical failures, critical successes
- Near-threshold runs, frequent temporal breaks
- Cost overruns, cost savers
- High override frequency
- Grouped by LLM, Agent, Human actor, Policy gap type

What it explicitly does NOT show:
- No synthesis or recommendations
- No draft policies yet
- No actions

Capability: lessons.list

### Panel: POL-GOV-DFT-O2

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: LESSONS
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Show draft policy candidates — machine-proposed governance rules.

What it shows:
- Auto-generated draft policies
- Each draft linked to evidence (incident IDs, run IDs)
- Observed benefit or risk per draft
- Drafts are non-executable

What it explicitly does NOT show:
- No enforcement
- No activation
- No human bypass

Capability: lessons.stats

### Panel: POL-GOV-DFT-O3

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: LESSONS
- Slot: 3

Class: interpretation
State: DRAFT

Purpose:
Show draft justification and impact preview — why each draft exists.

What it shows:
- Problem statement (derived from evidence)
- Expected effect: incidents prevented, costs saved, failures reduced
- Known risks: false positives, reduced throughput, human friction
- Preview based on historical/simulated data only

What it explicitly does NOT show:
- No future predictions beyond evidence
- No black-box proposals
- No enforcement

Capability: lessons.get

### Panel: POL-GOV-DFT-O4

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: LESSONS
- Slot: 4

Class: execution
State: DRAFT

Purpose:
Provide approval and blast radius control for draft policies.

What it shows:
- Scope selection: single LLM, group of LLMs, agent class, human role
- Blast radius: pilot (1 entity), limited (subset), global
- Enforcement mode: observe-only, soft gate, hard block
- Explicit choices only, no defaults

What it explicitly does NOT show:
- No auto-activation
- No silent inheritance

Capability: lessons.convert_to_draft

### Panel: POL-GOV-DFT-O5

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: LESSONS
- Slot: 5

Class: execution
State: DRAFT

Purpose:
Show decision outcomes and lifecycle routing after human decides.

What it shows:
- Approved: draft → active policy, moves to Governance → Active
- Rejected: draft archived with reason, signal suppressed
- Deferred: parked for more data, re-evaluated later
- Every draft must end in one of these three states

What it explicitly does NOT show:
- No silent expiration
- No auto-decisions

Capability: lessons.dismiss_or_defer

### Panel: POL-GOV-LES-O6

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: LESSONS
- Slot: 6

Class: evidence
State: DRAFT

Purpose:
Show lessons learned from system behavior — observed patterns that inform governance.

What it shows:
- Critical failures and their root causes
- Near-threshold runs and recurring patterns
- Cost overruns and cost-saving behaviors
- High override frequency signals
- Grouped by: LLM, Agent, Human actor, Policy gap type
- Evidence links: incident IDs, run IDs, trace IDs

What it explicitly does NOT show:
- No recommendations or synthesis
- No draft policies
- No actions or controls

Capability: lessons.list

### Panel: POL-GOV-LES-O7

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: LESSONS
- Slot: 7

Class: interpretation
State: DRAFT

Purpose:
Show draft policy proposals derived from lessons — awaiting human approval or rejection.

What it shows:
- Machine-proposed policy drafts based on observed lessons
- Each proposal linked to source lessons (evidence chain)
- Expected benefit: incidents prevented, costs saved
- Known risks: false positives, friction
- Proposal status: pending, approved, rejected, deferred

What it explicitly does NOT show:
- No auto-activation
- No enforcement
- No silent decisions

Capability: lessons.get

### Panel: POL-GOV-LIB-O1

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: POLICY_LIBRARY
- Slot: 1

Class: evidence
State: DRAFT

Purpose:
Show the global policy catalog — all policies available from Agenticverz backend.

What it shows:
- Complete list of global policies (cost controls, rate limits, safety guards, etc.)
- Metadata: policy ID, category, default enforcement mode, version, maintainer
- Read-only discovery surface

What it explicitly does NOT show:
- No adoption controls
- No filtering by current usage
- No enforcement

Capability: policies.rules

### Panel: POL-GOV-LIB-O2

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: POLICY_LIBRARY
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Show applicability and compatibility matrix — where each policy can be applied.

What it shows:
- Supported targets: LLMs, agents, human executors, run types
- Org-wide applicability
- Mutually exclusive policies, required prerequisites, known incompatibilities

What it explicitly does NOT show:
- No human override at this stage
- No adoption actions

Capability: policies.rules

### Panel: POL-GOV-LIB-O3

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: POLICY_LIBRARY
- Slot: 3

Class: interpretation
State: DRAFT

Purpose:
Show adoption status and current usage — how and where each policy is used.

What it shows:
- Adoption state: not used, used in limited scope, used globally
- Active scopes: specific LLMs, agents, humans, all runs
- Last modified, who approved
- Reflects actual enforcement, not intent

What it explicitly does NOT show:
- No adoption controls
- No proposed changes

Capability: policies.rules

### Panel: POL-GOV-LIB-O4

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: POLICY_LIBRARY
- Slot: 4

Class: execution
State: DRAFT

Purpose:
Provide attach/detach policy controls — human action to adopt or remove policies.

What it shows:
- Attach policy to: single LLM, agent group, human role, all runs
- Detach policy from any scope
- Required inputs: scope selection, enforcement mode, justification (mandatory)
- Every change is auditable

What it explicitly does NOT show:
- No default scope
- No silent inheritance

Capability: policies.rules

### Panel: POL-GOV-LIB-O5

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: POLICY_LIBRARY
- Slot: 5

Class: interpretation
State: DRAFT

Purpose:
Show change impact and audit trail for policy adoption changes.

What it shows:
- Impact preview based on historical runs
- Expected prevented incidents, cost savings
- Known risks
- Audit record: policy, scope before/after, approved by, timestamp
- Rollback option (first-class)

What it explicitly does NOT show:
- No auto-rollback
- No silent changes

Capability: policies.rules

### Panel: ANA-CST-USG-O1

Location:
- Domain: ANALYTICS
- Subdomain: COST
- Topic: USAGE
- Slot: 1

Class: interpretation
State: EMPTY

Purpose:
Show limit policy coverage and blast radius — how many policies and how wide.

What it shows:
- Total active limit policies
- Coverage by scope: org-wide, by LLM, by agent, by human executor
- Blast radius distribution: narrow, medium, broad
- Breakdowns: cost limits, token limits, rate limits, time limits

What it explicitly does NOT show:
- No configuration controls
- No threshold editing
- No policy creation

Capability: null

### Panel: ANA-CST-USG-O2

Location:
- Domain: ANALYTICS
- Subdomain: COST
- Topic: USAGE
- Slot: 2

Class: interpretation
State: EMPTY

Purpose:
Show configured limits vs actual usage — how close are we running to limits.

What it shows:
- Per limit: configured threshold, actual observed usage (p50/p95/p99)
- Headroom remaining (%)
- Slices: by LLM, by agent, by human, by policy
- Chronic near-limit behavior, over-conservative limits

What it explicitly does NOT show:
- No threshold editing
- No policy changes

Capability: null

### Panel: ANA-CST-USG-O3

Location:
- Domain: ANALYTICS
- Subdomain: COST
- Topic: USAGE
- Slot: 3

Class: interpretation
State: EMPTY

Purpose:
Show violations, prevented runs, and overrides — what limits actually stopped.

What it shows:
- Total violation attempts, prevented executions
- Allowed-but-flagged executions, explicit human overrides
- Categorization: cost overrun, token exhaustion, timeouts, rate bursts
- Override analysis: who overrode, which policy, outcome after override

What it explicitly does NOT show:
- No override controls
- No policy editing

Capability: null

### Panel: ANA-CST-USG-O4

Location:
- Domain: ANALYTICS
- Subdomain: COST
- Topic: USAGE
- Slot: 4

Class: interpretation
State: EMPTY

Purpose:
Show savings and risk reduction attribution — what policies saved.

What it shows:
- Cost saved, tokens saved, time saved, incidents avoided
- Attribution: by policy, by LLM, by agent, by human, by time window
- Risk lens: high-savings/low-friction vs low-savings/high-friction

What it explicitly does NOT show:
- No policy controls
- No threshold editing

Capability: null

### Panel: ANA-CST-USG-O5

Location:
- Domain: ANALYTICS
- Subdomain: COST
- Topic: USAGE
- Slot: 5

Class: interpretation
State: EMPTY

Purpose:
Show policy performance health and recommendations — which policies work.

What it shows:
- Health classification: effective & stable, effective but noisy, ineffective, harmful
- Signals: violation-to-prevention ratio, override frequency, savings vs disruption
- Flags for Drafts: consider tightening, relaxing, deprecating (read-only)

What it explicitly does NOT show:
- No auto-actions
- No policy editing

Capability: null

### Panel: POL-LIM-CTR-O1

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: CONTROLS
- Slot: 1

Class: evidence
State: DRAFT

Purpose:
Show limit policy definition matrix — what limits exist and where they apply.

What it shows:
- Policy ID/Name, limit type (cost/token/rate/time)
- Scope: org/project, LLM(s), agent(s), human executor(s)
- Blast radius: single, group, global
- Status: active, shadow (observe only), disabled

What it explicitly does NOT show:
- No usage metrics
- No violation data

Capability: policies.limits

### Panel: POL-LIM-CTR-O2

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: CONTROLS
- Slot: 2

Class: execution
State: DRAFT

Purpose:
Provide threshold configuration and fine-tuning controls.

What it shows:
- Per policy: hard limit (enforced), soft limit (warn/flag)
- Grace window: time-based, count-based
- Cool-down/reset logic
- Dimensions: by LLM, by agent class, by human role, by time
- Live preview: "At current usage, this would have blocked X runs yesterday"

What it explicitly does NOT show:
- No usage analytics
- No violation history

Capability: policies.budgets

### Panel: POL-LIM-CTR-O3

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: CONTROLS
- Slot: 3

Class: configuration
State: DRAFT

Purpose:
Set execution thresholds that drive LLM run governance signals.

This is the authoritative input surface for customer-controlled limits.
These params feed the LLMRunThresholdResolver which evaluates runs.

What it shows:
- Max Execution Time (ms): 1000-300000, default 60000
- Max Tokens: 256-200000, default 8192
- Max Cost (USD): 0.01-100.00, default 1.00
- Signal on Failure: toggle, default ON
- Effective defaults shown when empty (grey "Inherited default")
- Yellow badge: "Overrides default"
- Red badge: "Invalid / rejected"

What it enables:
- ACT-LLM-LIVE-O2: Surface live runs exceeding expected execution time
- ACT-LLM-COMP-O3: Expose completed runs that ended in failure

What it explicitly does NOT show:
- No usage analytics
- No violation history
- No live run data

Capability: policies.limits.threshold_params

### Panel: POL-LIM-CTR-O4

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: CONTROLS
- Slot: 4

Class: execution
State: DRAFT

Purpose:
Provide experimentation and what-if simulation capabilities.

What it shows:
- Clone existing policy, modify thresholds
- Run simulation against last 7/30/90 days
- Compare: blocks vs allows, cost saved vs runs blocked
- Comparison view: current policy vs candidate policy
- Experiments do not affect live runs, must be named and scoped

What it explicitly does NOT show:
- No live enforcement
- No production impact

Capability: policies.limits

### Panel: POL-LIM-CTR-O5

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: CONTROLS
- Slot: 5

Class: execution
State: DRAFT

Purpose:
Provide approval, audit, and activation workflow for threshold changes.

What it shows:
- Workflow: draft → review → active
- Optional multi-approver, activation notes required
- Audit log: threshold changes, scope changes, rollbacks, overrides
- Post-activation hooks: auto-link to Usage → O3, Governance → Active

What it explicitly does NOT show:
- No silent activation
- No hidden changes

Capability: policies.limits

### Panel: POL-LIM-VIO-O1

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: VIOLATIONS
- Slot: 1

Class: evidence
State: DRAFT

Purpose:
Show the violation ledger — immutable record of every limit violation.

What it shows:
- Run ID, timestamp, policy ID, limit type
- Violation mode: hard terminate, temporal fracture, human override
- Actor at violation: LLM, agent, human
- Enforcement state: blocked, allowed (override)
- One row per violation event, overrides do not erase violation

What it explicitly does NOT show:
- No configuration controls
- No policy editing

Capability: policies.violations

### Panel: POL-LIM-VIO-O2

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: VIOLATIONS
- Slot: 2

Class: interpretation
State: DRAFT

Purpose:
Show violation classification and attribution — why and who.

What it shows:
- Aggregations: by limit type, by LLM, by agent, by human, by policy
- Primary trigger: cost overrun, token spike, time breach
- Secondary factor: retry loop, fan-out, poor prompt, downstream latency

What it explicitly does NOT show:
- No policy controls
- No excuses

Capability: policies.violations

### Panel: POL-LIM-VIO-O3

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: VIOLATIONS
- Slot: 3

Class: interpretation
State: DRAFT

Purpose:
Show override and fracture analysis — which violations were ignored or softened.

What it shows:
- Override count, override rate (% of violations)
- Fracture duration (avg/p95), re-entry success rate
- Breakdown: by role, by policy, by urgency tag
- Flags: repeated overrides on same policy, overrides followed by failure

What it explicitly does NOT show:
- No override controls
- No policy editing

Capability: policies.violations

### Panel: POL-LIM-VIO-O4

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: VIOLATIONS
- Slot: 4

Class: interpretation
State: DRAFT

Purpose:
Show loss and impact quantification — what violations actually cost.

What it shows:
- Cost lost, time lost (compute + human wait), productivity lost
- Cost saved (from enforced blocks)
- Views: by LLM, by agent, by human, by policy, by time window
- Saved and lost shown together (no vanity metrics)

What it explicitly does NOT show:
- No policy controls
- No threshold editing

Capability: policies.violations

### Panel: POL-LIM-VIO-O5

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: VIOLATIONS
- Slot: 5

Class: interpretation
State: DRAFT

Purpose:
Show escalation, evidence, and governance hooks for violations requiring action.

What it shows:
- Triggers: repeated violations, high override density, high loss concentration
- Links to: Governance → Drafts (revision), Governance → Active (review)
- Export: audit logs, evidence bundles (SOC2/internal review)
- This surface escalates, not fixes

What it explicitly does NOT show:
- No editing limits
- No approvals

Capability: policies.violations

### Panel: LOG-REC-LLM-O1

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: LLM_RUNS
- Slot: 1

Class: evidence
State: DRAFT

Purpose:
Show the run log envelope — canonical immutable record per run.

Capability: logs.llm_runs

What it shows:
- Run ID, start/end timestamp
- Executor type (LLM, agent, human), executor identity
- Outcome: success, failure, near threshold, terminated
- Correlation IDs: policy IDs, incident IDs, trace IDs
- Append-only, no summarization, no redaction

What it explicitly does NOT show:
- No interpretation
- No aggregation

Capability: logs.llm_runs

### Panel: LOG-REC-LLM-O2

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: LLM_RUNS
- Slot: 2

Class: evidence
State: DRAFT

Purpose:
Show execution trace — step-by-step progression of the run.

Capability: logs.llm_runs

What it shows:
- Step number, timestamp, action type (prompt, tool, API call, delegation)
- Inputs/outputs (hashed if sensitive)
- Latency per step, tokens in/out
- Deterministic replay graph

What it explicitly does NOT show:
- No summarization
- No policy judgment

Capability: logs.llm_runs

### Panel: LOG-REC-LLM-O3

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: LLM_RUNS
- Slot: 3

Class: evidence
State: DRAFT

Purpose:
Show threshold and policy interaction trace — governance footprint per run.

Capability: logs.llm_runs

What it shows:
- Threshold checks (cost/time/token/rate)
- Policy evaluations, near-breach warnings, violations
- Overrides (who, when, why)
- Per event: policy ID, rule evaluated, decision result, enforcer

What it explicitly does NOT show:
- No policy editing
- No recommendations

Capability: logs.llm_runs

### Panel: LOG-REC-LLM-O4

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: LLM_RUNS
- Slot: 4

Class: evidence
State: DRAFT

Purpose:
Show 60-second incident replay window — what happened around the inflection point.

Capability: logs.llm_runs

What it shows:
- T-30s → T+30s around inflection point
- Prompt changes, retry loops, latency spikes
- Cost acceleration, agent fan-out, human intervention
- Same time scale across all runs, replayable as sequence

What it explicitly does NOT show:
- No summarization
- No interpretation

Capability: logs.llm_runs

### Panel: LOG-REC-LLM-O5

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: LLM_RUNS
- Slot: 5

Class: evidence
State: DRAFT

Purpose:
Show audit and export package — legally defensible evidence bundle.

Capability: logs.llm_runs

What it shows:
- Audit metadata: accessed by, deterministic state hash, integrity checksum
- Retention class, compliance tags (SOC2, internal, legal)
- Exports: JSON (raw), CSV (events), PDF (timeline snapshot)
- Export does not mutate logs, every export is itself logged

What it explicitly does NOT show:
- No modification controls
- No redaction controls

Capability: logs.llm_runs

### Panel: LOG-REC-SYS-O1

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: SYSTEM_LOGS
- Slot: 1

Class: evidence
State: DRAFT

Purpose:
Show environment snapshot — baseline state at run start.

Capability: logs.system

What it shows:
- Customer environment ID, region/zone, VPC/subnet
- Node/pod/container ID, instance type
- CPU/memory allocation, disk I/O limits, network class
- Immutable environment fingerprint

What it explicitly does NOT show:
- No interpretation
- No recommendations

### Panel: LOG-REC-SYS-O2

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: SYSTEM_LOGS
- Slot: 2

Class: evidence
State: DRAFT

Purpose:
Show network and bandwidth telemetry — connectivity health during execution.

Capability: logs.system

What it shows:
- Time-series: ingress/egress bandwidth, packet loss %, latency (p50/p95/p99)
- DNS resolution time, TLS handshake failures, connection retries
- Correlated with run timestamps, LLM provider calls, agent fan-out

What it explicitly does NOT show:
- No interpretation
- No blame attribution

### Panel: LOG-REC-SYS-O3

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: SYSTEM_LOGS
- Slot: 3

Class: evidence
State: DRAFT

Purpose:
Show infra interrupts and degradation events — what infra did to the run.

Capability: logs.system

What it shows:
- Node restarts, pod evictions, autoscaling events
- CPU throttling, memory pressure/OOM, disk saturation, provider brownouts
- Per event: infra component, start/end time, severity, affected run IDs

What it explicitly does NOT show:
- No interpretation
- No recommendations

### Panel: LOG-REC-SYS-O4

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: SYSTEM_LOGS
- Slot: 4

Class: evidence
State: DRAFT

Purpose:
Show run-aligned infra replay window — infra state at moment of anomaly.

Capability: logs.system

What it shows:
- 60-second window aligned to failure/near-threshold/cost spike/latency anomaly
- CPU spikes, network jitter, scaling reactions, provider API instability
- Time-aligned with LLM Runs → O4 (same timestamps, different layer)

What it explicitly does NOT show:
- No interpretation
- No blame shifting

### Panel: LOG-REC-SYS-O5

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: SYSTEM_LOGS
- Slot: 5

Class: interpretation
State: DRAFT

Purpose:
Show infra audit and attribution record — who is responsible.

Capability: logs.system

What it shows:
- Infra fault attribution: customer infra, cloud provider, LLM provider, internal platform
- Confidence score, evidence references (O2-O4), linked run IDs
- Exports: SOC2 infra evidence, incident RCA attachments, customer-shareable report

What it explicitly does NOT show:
- No policy controls
- No recommendations

### Panel: LOG-REC-AUD-O1

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: AUDIT
- Slot: 1

Class: evidence
State: DRAFT

Purpose:
Show identity and authentication lifecycle — who accessed and how.

Capability: logs.audit

What it shows:
- Login/logout, token issuance/refresh/revocation
- Auth method (API key, OAuth, SSO, cert), MFA events
- Identity type: human, agent, service, system
- Per event: identity ID, auth provider, timestamp, source IP, session ID

What it explicitly does NOT show:
- No authorization decisions (that's O2)
- No interpretation

### Panel: LOG-REC-AUD-O2

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: AUDIT
- Slot: 2

Class: evidence
State: DRAFT

Purpose:
Show authorization and access decisions — what each identity was allowed to do.

Capability: logs.audit

What it shows:
- Resource accessed, action attempted
- Policy evaluated, decision (ALLOW/DENY/CONDITIONAL)
- Reason code (policy ID, rule ID), override flag
- Both allow and deny must be logged (silent allows illegal)

What it explicitly does NOT show:
- No policy editing
- No recommendations

### Panel: LOG-REC-AUD-O3

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: AUDIT
- Slot: 3

Class: evidence
State: DRAFT

Purpose:
Show trace and log access audit — who viewed, exported, or modified observability data.

Capability: logs.audit

What it shows:
- Actions: log view, trace replay, evidence export, redaction applied, deletion attempts
- Per action: actor identity, object accessed (run ID, trace ID), purpose tag, scope, timestamp

What it explicitly does NOT show:
- No modification controls
- No deletion controls (deletions must fail but are logged)

### Panel: LOG-REC-AUD-O4

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: AUDIT
- Slot: 4

Class: evidence
State: DRAFT

Purpose:
Show integrity and tamper detection — was any audit data altered or compromised.

Capability: logs.audit

What it shows:
- Integrity: hashes per log segment, hash chaining, write-once markers
- Clock skew detection, missing sequence detection
- Anomalies: hash mismatch, gaps in sequence, clock rollback, unauthorized mutation attempts

What it explicitly does NOT show:
- No modification controls
- No recovery actions

### Panel: LOG-REC-AUD-O5

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: AUDIT
- Slot: 5

Class: evidence
State: DRAFT

Purpose:
Show compliance and export record — what audit evidence was produced, shared, or certified.

Capability: logs.audit

What it shows:
- Per export: type (SOC2, ISO, internal, customer), scope, requestor, approval chain
- Redaction policy applied, delivery channel, retention class
- Auditor access (read-only), certification timestamps, evidence checksum

What it explicitly does NOT show:
- No modification controls
- No approval actions

---

## Capabilities

### Capability: overview.highlights

Panel: OVR-SUM-HL-O1
Status: OBSERVED
Verified: 2026-01-14

Implementation:
- Endpoint: /api/v1/activity/summary/by-status
- Method: GET

Data Mapping:
- count_running → runs.by_status.running
- count_completed_window → runs.by_status.completed
- count_near_threshold → attention.at_risk_count
- last_observed_at → provenance.generated_at

SDSR Verification:
- Endpoint exists: PASS
- Schema matches: PASS
- Auth works: PASS
- Data is real: PASS

Scenario: observe_overview_activity_snapshot

### Capability: overview.live_runs

Panel: OVR-SUM-HL-O1
Status: DECLARED
Added: 2026-01-17

NOTE: Derived capability from Activity domain, exposed via Overview facade.

Implementation:
- Endpoint: /api/v1/overview/highlights
- Method: GET

Data Mapping:
- live_runs → pulse.live_runs (count of status='running' in worker_runs)

Domain Lineage:
- Source Domain: ACTIVITY
- Source Table: worker_runs
- Drill-Through: /precus/activity

Acceptance:
- Returns count of currently running executions
- Included in SystemPulse.live_runs field
- Tenant-scoped query

Scenario: PENDING (SDSR to be created)

### Capability: overview.queued_runs

Panel: OVR-SUM-HL-O1
Status: DECLARED
Added: 2026-01-17

NOTE: Derived capability from Activity domain, exposed via Overview facade.

Implementation:
- Endpoint: /api/v1/overview/highlights
- Method: GET

Data Mapping:
- queued_runs → pulse.queued_runs (count of status='queued' in worker_runs)

Domain Lineage:
- Source Domain: ACTIVITY
- Source Table: worker_runs
- Drill-Through: /precus/activity

Acceptance:
- Returns count of queued/pending executions
- Included in SystemPulse.queued_runs field
- Tenant-scoped query

Scenario: PENDING (SDSR to be created)

### Capability: overview.policy_breaches

Panel: OVR-SUM-HL-O2
Status: DECLARED
Added: 2026-01-17

NOTE: Derived capability from Policies domain, exposed via Overview facade.

Implementation:
- Endpoint: /api/v1/overview/highlights
- Method: GET

Data Mapping:
- recent_breaches → pulse.recent_breaches (count of breaches in last 24h)

Domain Lineage:
- Source Domain: POLICIES
- Source Table: limit_breaches
- Drill-Through: /precus/policies

Acceptance:
- Returns count of recent limit breaches (last 24h)
- Included in SystemPulse.recent_breaches field
- Also shown in Policies domain_count.critical
- Tenant-scoped query

Scenario: PENDING (SDSR to be created)

### Capability: activity.runs

Panel: ACT-LLM-LIVE-O1
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/activity/runs
- Method: GET

Data Mapping:
- count → total count of runs with status=running

Acceptance:
- Returns count of currently running LLM executions
- Response includes total count field

Scenario: SDSR-ACT-LLM-LIVE-O1-001

### Capability: activity.runs

Panel: ACT-LLM-COMP-O1
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/activity/runs
- Method: GET

Data Mapping:
- count → total count of runs with status=completed in window

Acceptance:
- Returns count of completed LLM executions in time window
- Response includes total count field

Scenario: SDSR-ACT-LLM-COMP-O1-001

### Capability: activity.runs_by_dimension

Panel: ACT-LLM-LIVE-O5, ACT-LLM-COMP-O5
Status: DECLARED

Implementation:
- Method: GET
- Policy: TOPIC-SCOPED-ENDPOINT-001

Topics Served:
  - topic: LIVE
    endpoint: /api/v1/activity/runs/live/by-dimension
    state_binding: implicit (LIVE hardcoded)
  - topic: COMPLETED
    endpoint: /api/v1/activity/runs/completed/by-dimension
    state_binding: implicit (COMPLETED hardcoded)

Generic Endpoint (INTERNAL/ADMIN ONLY):
  - endpoint: /api/v1/activity/runs/by-dimension
  - status: DEPRECATED
  - note: NOT FOR PANEL USE

Data Mapping:
- dimension → grouping field (provider_type, source, agent_id, risk_level, status)
- groups → array of {value, count, percentage}
- total_runs → total count before grouping

Acceptance:
- Returns run counts grouped by specified dimension
- Response includes dimension, groups array, total_runs
- State binding is IMPLICIT (injected by endpoint, not caller-controlled)
- Frontend calls topic-scoped endpoint directly (no state param needed)

Scenario: SDSR-ACT-LLM-LIVE-O5-001

### Capability: activity.summary_by_status

Panel: ACT-LLM-COMP-O2, ACT-LLM-LIVE-O5
Status: OBSERVED

Implementation:
- Endpoint: /api/v1/activity/summary/by-status
- Method: GET

Data Mapping:
- buckets → array of {status, count, percentage}
- total_runs → total count across all statuses

Acceptance:
- Returns run counts grouped by execution status
- Response includes buckets array with status breakdown
- Supports state filter for LIVE/COMPLETED scoping

Scenario: SDSR-ACT-LLM-COMP-O2-001

### Capability: activity.patterns

Panel: ACT-LLM-SIG-O3
Status: OBSERVED

Implementation:
- Endpoint: /api/v1/activity/patterns
- Method: GET

Data Mapping:
- patterns → detected instability patterns (retry_loop, step_oscillation, tool_call_loop, timeout_cascade)

Acceptance:
- Returns detected behavior patterns over time
- Response includes pattern_type, run_id, confidence, details

Scenario: SDSR-ACT-LLM-SIG-O3-001

### Capability: activity.cost_analysis

Panel: ACT-LLM-SIG-O4, ACT-LLM-LIVE-O5
Status: DECLARED

Implementation:
- Endpoint: /api/v1/activity/cost-analysis
- Method: GET

Data Mapping:
- agents → cost anomalies via Z-score comparison against baseline

Acceptance:
- Returns cost anomaly analysis per agent
- Response includes z_score, is_anomaly, baseline comparison

Scenario: SDSR-ACT-LLM-SIG-O4-001

### Capability: activity.signals

Panel: ACT-LLM-SIG-O1, ACT-LLM-SIG-O2, ACT-LLM-SIG-O5
Status: OBSERVED

Implementation:
- Endpoint: /api/v1/activity/attention-queue
- Method: GET

Data Mapping:
- queue → prioritized attention items with composite scores

Acceptance:
- Returns runs ranked by attention score (risk 35%, impact 25%, latency 15%, recency 15%, evidence 10%)
- Response includes attention_score, reasons, state, status

Scenario: SDSR-ACT-LLM-SIG-O5-001

### Capability: incidents.active_list

Panel: INC-EV-ACT-O1
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/active
- Method: GET

Data Mapping:
- incidents → list of active incidents

Acceptance:
- Returns list of currently active incidents
- Response includes incident details

Scenario: SDSR-INC-EV-ACT-O1-001

### Capability: incidents.active_list

Panel: INC-EV-ACT-O2
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/active
- Method: GET

Data Mapping:
- summary → aggregated incident statistics

Acceptance:
- Returns incident summary with counts by type
- Response includes cause classification

Scenario: SDSR-INC-EV-ACT-O2-001

### Capability: incidents.metrics

Panel: INC-EV-ACT-O3
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/metrics
- Method: GET

Data Mapping:
- metrics → incident control state metrics

Acceptance:
- Returns incident metrics (containment status)
- Response includes guardrail status

Scenario: SDSR-INC-EV-ACT-O3-001

### Capability: incidents.cost_impact

Panel: INC-EV-ACT-O4
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/cost-impact
- Method: GET

Data Mapping:
- patterns → incident impact patterns

Acceptance:
- Returns incident patterns and cost impact
- Response includes damage assessment

Scenario: SDSR-INC-EV-ACT-O4-001

### Capability: incidents.active_list

Panel: INC-EV-ACT-O5
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/active
- Method: GET

Data Mapping:
- infra_summary → attribution and escalation context

Acceptance:
- Returns incident attribution data
- Response includes escalation eligibility

Scenario: SDSR-INC-EV-ACT-O5-001

### Capability: incidents.resolved_list

Panel: INC-EV-RES-O1
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/resolved
- Method: GET

Data Mapping:
- resolved → list of recently resolved incidents

Acceptance:
- Returns list of resolved incidents
- Response includes resolution timestamp

Scenario: SDSR-INC-EV-RES-O1-001

### Capability: incidents.learnings

Panel: INC-EV-RES-O2
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/{incident_id}/learnings
- Method: GET

Data Mapping:
- actions → resolution methods applied

Acceptance:
- Returns recovery actions taken
- Response includes resolution method type

Scenario: SDSR-INC-EV-RES-O2-001

### Capability: incidents.metrics

Panel: INC-EV-RES-O3
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/metrics
- Method: GET

Data Mapping:
- candidates → TTR and SLA compliance data

Acceptance:
- Returns recovery candidates with timing
- Response includes SLA compliance status

Scenario: SDSR-INC-EV-RES-O3-001

### Capability: incidents.resolved_list

Panel: INC-EV-RES-O4
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/resolved
- Method: GET

Data Mapping:
- graduation → post-resolution outcomes

Acceptance:
- Returns graduated incident outcomes
- Response includes final cost data

Scenario: SDSR-INC-EV-RES-O4-001

### Capability: incidents.learnings

Panel: INC-EV-RES-O5
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/{incident_id}/learnings
- Method: GET

Data Mapping:
- replay → learning signals from resolved incidents

Acceptance:
- Returns replay summary with learnings
- Response includes recurrence risk

Scenario: SDSR-INC-EV-RES-O5-001

### Capability: incidents.historical_trend

Panel: INC-EV-HIST-O1
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/historical/trend
- Method: GET

Data Mapping:
- historical → incident volume trends

Acceptance:
- Returns historical incident counts
- Response includes trend direction

Scenario: SDSR-INC-EV-HIST-O1-001

### Capability: incidents.historical_dist

Panel: INC-EV-HIST-O2
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/historical/distribution
- Method: GET

Data Mapping:
- guard → incident type distribution

Acceptance:
- Returns guarded incident types
- Response includes category breakdown

Scenario: SDSR-INC-EV-HIST-O2-001

### Capability: incidents.recurring

Panel: INC-EV-HIST-O3
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/recurring
- Method: GET

Data Mapping:
- v1_list → recurrence analysis data

Acceptance:
- Returns v1 incident list with recurrence data
- Response includes repeat markers

Scenario: SDSR-INC-EV-HIST-O3-001

### Capability: incidents.historical_cost

Panel: INC-EV-HIST-O4
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/historical/cost-trend
- Method: GET

Data Mapping:
- ops_list → cost and impact over time

Acceptance:
- Returns ops incident list with costs
- Response includes cost prevented data

Scenario: SDSR-INC-EV-HIST-O4-001

### Capability: incidents.patterns

Panel: INC-EV-HIST-O5
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/incidents/patterns
- Method: GET

Data Mapping:
- stats → systemic governance signals

Acceptance:
- Returns integration statistics
- Response includes policy associations

Scenario: SDSR-INC-EV-HIST-O5-001

### Capability: policies.rules

Panel: POL-GOV-ACT-O1
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-proposals
- Method: GET

Data Mapping:
- proposals → list of policy proposals

Acceptance:
- Returns list of policy proposals
- Response includes proposal status and metadata

Scenario: SDSR-POL-GOV-ACT-O1-001

### Capability: policies.rules

Panel: POL-GOV-ACT-O2
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-proposals/stats/summary
- Method: GET

Data Mapping:
- summary → enforcement effectiveness metrics

Acceptance:
- Returns policy enforcement statistics
- Response includes evaluation counts

Scenario: SDSR-POL-GOV-ACT-O2-001

### Capability: policies.requests

Panel: POL-GOV-ACT-O3
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policies/requests
- Method: GET

Data Mapping:
- requests → policy action requests

Acceptance:
- Returns policy requests
- Response includes request status

Scenario: SDSR-POL-GOV-ACT-O3-001

### Capability: policies.state

Panel: POL-GOV-ACT-O4
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-layer/state
- Method: GET

Data Mapping:
- state → policy layer state

Acceptance:
- Returns policy layer current state
- Response includes active policies

Scenario: SDSR-POL-GOV-ACT-O4-001

### Capability: policies.metrics

Panel: POL-GOV-ACT-O5
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-layer/metrics
- Method: GET

Data Mapping:
- metrics → governance stress signals

Acceptance:
- Returns policy performance metrics
- Response includes stress indicators

Scenario: SDSR-POL-GOV-ACT-O5-001

### Capability: lessons.list

Panel: POL-GOV-DFT-O1
Domain: POLICIES
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-layer/lessons
- Method: GET

Data Mapping:
- lessons → list of lessons learned

Acceptance:
- Returns lessons list
- Response includes status, evidence links

Scenario: SDSR-POL-GOV-DFT-O1-001

### Capability: lessons.stats

Panel: POL-GOV-DFT-O2
Domain: POLICIES
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-layer/lessons/stats
- Method: GET

Data Mapping:
- stats → lesson statistics

Acceptance:
- Returns lesson stats
- Response includes counts by status

Scenario: SDSR-POL-GOV-DFT-O2-001

### Capability: lessons.get

Panel: POL-GOV-DFT-O3
Domain: POLICIES
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-layer/lessons/{lesson_id}
- Method: GET

Data Mapping:
- lesson → lesson detail

Acceptance:
- Returns lesson detail
- Response includes evidence chain

Scenario: SDSR-POL-GOV-DFT-O3-001

### Capability: lessons.convert_to_draft

Panel: POL-GOV-DFT-O4
Domain: POLICIES
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-layer/lessons/{lesson_id}/convert
- Method: POST

Data Mapping:
- draft_id → created draft proposal ID

Acceptance:
- Converts lesson to draft proposal
- Response includes new draft ID

Scenario: SDSR-POL-GOV-DFT-O4-001

### Capability: lessons.dismiss_or_defer

Panel: POL-GOV-DFT-O5
Domain: POLICIES
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-layer/lessons/{lesson_id}/defer
- Method: POST

Data Mapping:
- success → defer status

Acceptance:
- Defers lesson until specified date
- Response includes deferred_until timestamp

Scenario: SDSR-POL-GOV-DFT-O5-001

### Capability: policies.rules

Panel: POL-GOV-LIB-O1
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-layer/safety-rules
- Method: GET

Data Mapping:
- rules → safety policy rules

Acceptance:
- Returns safety rule catalog
- Response includes rule metadata

Scenario: SDSR-POL-GOV-LIB-O1-001

### Capability: policies.rules

Panel: POL-GOV-LIB-O2
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-layer/ethical-constraints
- Method: GET

Data Mapping:
- constraints → ethical constraints

Acceptance:
- Returns ethical constraint list
- Response includes applicability matrix

Scenario: SDSR-POL-GOV-LIB-O2-001

### Capability: policies.rules

Panel: POL-GOV-LIB-O3
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy/active
- Method: GET

Data Mapping:
- policies → active policy list (V2 facade)

Acceptance:
- Returns active policies
- Response includes adoption status

Scenario: SDSR-POL-GOV-LIB-O3-001

### Capability: policies.rules

Panel: POL-GOV-LIB-O4
Status: ASSUMED

Implementation:
- Endpoint: /guard/policies
- Method: GET

Data Mapping:
- policies → guard policies

Acceptance:
- Returns guard policy list
- Response includes enforcement controls

Scenario: SDSR-POL-GOV-LIB-O4-001

### Capability: policies.rules

Panel: POL-GOV-LIB-O5
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-layer/temporal-policies
- Method: GET

Data Mapping:
- policies → temporal policies

Acceptance:
- Returns temporal policy list
- Response includes audit trail

Scenario: SDSR-POL-GOV-LIB-O5-001

### Capability: policies.limits

Panel: POL-LIM-CTR-O1
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-layer/risk-ceilings
- Method: GET

Data Mapping:
- ceilings → risk ceiling definitions

Acceptance:
- Returns risk ceiling matrix
- Response includes scope information

Scenario: SDSR-POL-LIM-CTR-O1-001

### Capability: policies.budgets

Panel: POL-LIM-CTR-O2
Status: ASSUMED

Implementation:
- Endpoint: /cost/budgets
- Method: GET

Data Mapping:
- budgets → budget configurations

Acceptance:
- Returns budget list
- Response includes threshold values

Scenario: SDSR-POL-LIM-CTR-O2-001

### Capability: policies.limits.threshold_params

Panel: POL-LIM-CTR-O3
Status: DECLARED

Implementation:
- Endpoint: /api/v1/policies/limits/{limit_id}/params
- Method: PUT

Data Mapping:
- max_execution_time_ms → Maximum execution time in milliseconds (1s-5min)
- max_tokens → Maximum tokens allowed (256-200k)
- max_cost_usd → Maximum cost per run (0.01-100)
- failure_signal → Emit signal on run failure (boolean)

Acceptance:
- Validates all params within bounds (no partial garbage)
- Rejects unknown keys (extra: forbid)
- Returns effective params with defaults applied
- Only accepts THRESHOLD category limits

Scenario: SDSR-POL-LIM-CTR-O3-001

### Capability: policies.limits

Panel: POL-LIM-CTR-O4
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/tenant/quota/tokens
- Method: GET

Data Mapping:
- quota → token quota limits

Acceptance:
- Returns token quota configuration
- Response includes usage/limits

Scenario: SDSR-POL-LIM-CTR-O4-001

### Capability: policies.limits

Panel: POL-LIM-CTR-O5
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy-layer/cooldowns
- Method: GET

Data Mapping:
- cooldowns → cooldown configurations

Acceptance:
- Returns cooldown list
- Response includes reset logic

Scenario: SDSR-POL-LIM-CTR-O5-001

### Capability: policies.violations

Panel: POL-LIM-VIO-O1
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy/violations
- Method: GET

Data Mapping:
- violations → violation records (V2 facade list)

Acceptance:
- Returns violation ledger
- Response includes enforcement state

Scenario: SDSR-POL-LIM-VIO-O1-001

### Capability: policies.violations

Panel: POL-LIM-VIO-O2
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy/violations
- Method: GET

Data Mapping:
- violations → violation list (V2 facade filtered view)

Acceptance:
- Returns violation list with classification
- Response includes enforcement state

Scenario: SDSR-POL-LIM-VIO-O2-001

### Capability: policies.violations

Panel: POL-LIM-VIO-O3
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy/violations/{violation_id}
- Method: GET

Data Mapping:
- violation → violation detail (V2 facade detail)

Acceptance:
- Returns violation detail
- Response includes full enforcement context

Scenario: SDSR-POL-LIM-VIO-O3-001

### Capability: policies.violations

Panel: POL-LIM-VIO-O4
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy/violations/{violation_id}
- Method: GET

Data Mapping:
- violation → violation context (V2 facade impact view)

Acceptance:
- Returns violation with impact context
- Response includes related policies and thresholds

Scenario: SDSR-POL-LIM-VIO-O4-001

### Capability: policies.violations

Panel: POL-LIM-VIO-O5
Status: ASSUMED

Implementation:
- Endpoint: /api/v1/policy/violations/{violation_id}
- Method: GET

Data Mapping:
- violation → violation proof (V2 facade raw evidence)

Acceptance:
- Returns violation with raw proof data
- Response includes audit trail and evidence

Scenario: SDSR-POL-LIM-VIO-O5-001

### Capability: logs.llm_runs

Panel: LOG-REC-LLM-O1
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/llm-runs/{run_id}/envelope
- Method: GET

Data Mapping:
- LLMRunRecord → canonical immutable run envelope
- EvidenceMetadata → correlation spine, provenance

Acceptance:
- Returns canonical immutable run record
- Response includes EvidenceMetadata (INV-LOG-META-001)
- Tenant-scoped query

Scenario: SDSR-LOG-REC-LLM-O1-001

### Capability: logs.llm_runs

Panel: LOG-REC-LLM-O2
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/llm-runs/{run_id}/trace
- Method: GET

Data Mapping:
- aos_traces → trace header
- aos_trace_steps → step-by-step progression

Acceptance:
- Returns step-by-step execution trace
- Response includes EvidenceMetadata
- Tenant-scoped query

Scenario: SDSR-LOG-REC-LLM-O2-001

### Capability: logs.llm_runs

Panel: LOG-REC-LLM-O3
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/llm-runs/{run_id}/governance
- Method: GET

Data Mapping:
- audit_ledger → policy/limit events for run

Acceptance:
- Returns policy and threshold interaction trace
- Response includes EvidenceMetadata
- Tenant-scoped query

Scenario: SDSR-LOG-REC-LLM-O3-001

### Capability: logs.llm_runs

Panel: LOG-REC-LLM-O4
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/llm-runs/{run_id}/replay
- Method: GET

Data Mapping:
- aos_trace_steps + system_records + audit_ledger → T±30s window

Acceptance:
- Returns 60-second replay window around inflection point
- Response includes events from llm, system, policy sources
- Tenant-scoped query

Scenario: SDSR-LOG-REC-LLM-O4-001

### Capability: logs.llm_runs

Panel: LOG-REC-LLM-O5
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/llm-runs/{run_id}/export
- Method: GET

Data Mapping:
- log_exports → export metadata
- available_formats, compliance_tags

Acceptance:
- Returns audit-grade evidence bundle information
- Response includes available formats, compliance tags
- Tenant-scoped query

Scenario: SDSR-LOG-REC-LLM-O5-001

### Capability: logs.system_logs

Panel: LOG-REC-SYS-O1
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/system/{run_id}/snapshot
- Method: GET

Data Mapping:
- system_records → environment baseline snapshot

Acceptance:
- Returns environment baseline state at run start
- Response includes EvidenceMetadata
- Tenant-scoped query

Scenario: SDSR-LOG-REC-SYS-O1-001

### Capability: logs.system_logs

Panel: LOG-REC-SYS-O2
Status: DECLARED (STUB)
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/system/{run_id}/telemetry
- Method: GET

Data Mapping:
- STUB response (producer not implemented)

Acceptance:
- Returns telemetry_not_collected stub
- Infrastructure telemetry producer not yet implemented
- Future milestone: M-TBD

Scenario: SDSR-LOG-REC-SYS-O2-001

### Capability: logs.system_logs

Panel: LOG-REC-SYS-O3
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/system/{run_id}/events
- Method: GET

Data Mapping:
- system_records → infra events correlated to run

Acceptance:
- Returns infrastructure events affecting the run
- Response includes EvidenceMetadata
- Tenant-scoped query

Scenario: SDSR-LOG-REC-SYS-O3-001

### Capability: logs.system_logs

Panel: LOG-REC-SYS-O4
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/system/{run_id}/replay
- Method: GET

Data Mapping:
- system_records → T±30s window around anomaly

Acceptance:
- Returns infra replay window around anomaly
- Response includes EvidenceMetadata
- Tenant-scoped query

Scenario: SDSR-LOG-REC-SYS-O4-001

### Capability: logs.system_logs

Panel: LOG-REC-SYS-O5
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/system/audit
- Method: GET

Data Mapping:
- system_records → infra attribution and audit

Acceptance:
- Returns infrastructure attribution records
- Response includes EvidenceMetadata
- Tenant-scoped query

Scenario: SDSR-LOG-REC-SYS-O5-001

### Capability: logs.audit

Panel: LOG-REC-AUD-O1
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/audit/identity
- Method: GET

Data Mapping:
- audit_ledger (user_create, user_modify, user_delete) → identity lifecycle
- EvidenceMetadata → correlation spine, provenance

Acceptance:
- Returns identity lifecycle audit records
- Response includes EvidenceMetadata (INV-LOG-META-001)
- Tenant-scoped query

Scenario: SDSR-LOG-REC-AUD-O1-001

### Capability: logs.audit

Panel: LOG-REC-AUD-O2
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/audit/authorization
- Method: GET

Data Mapping:
- audit_ledger (permission, rbac, auth) → authorization decisions
- EvidenceMetadata → correlation spine, provenance

Acceptance:
- Returns authorization decision records
- Response includes EvidenceMetadata (INV-LOG-META-001)
- Tenant-scoped query

Scenario: SDSR-LOG-REC-AUD-O2-001

### Capability: logs.audit

Panel: LOG-REC-AUD-O3
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/audit/access
- Method: GET

Data Mapping:
- audit_ledger (log_access, export, download) → log access records
- EvidenceMetadata → correlation spine, provenance

Acceptance:
- Returns log access audit records
- Response includes EvidenceMetadata (INV-LOG-META-001)
- Tenant-scoped query

Scenario: SDSR-LOG-REC-AUD-O3-001

### Capability: logs.audit

Panel: LOG-REC-AUD-O4
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/audit/integrity
- Method: GET

Data Mapping:
- audit_ledger (checksum, verify, seal) → integrity markers
- EvidenceMetadata → correlation spine, provenance

Acceptance:
- Returns integrity check records
- Response includes EvidenceMetadata (INV-LOG-META-001)
- Tenant-scoped query

Scenario: SDSR-LOG-REC-AUD-O4-001

### Capability: logs.audit

Panel: LOG-REC-AUD-O5
Status: DECLARED
Updated: 2026-01-19 (LOGS Domain V2)

Implementation:
- Endpoint: /api/v1/logs/audit/exports
- Method: GET

Data Mapping:
- log_exports → compliance export records (O5 evidence bundles)
- EvidenceMetadata → correlation spine, provenance

Acceptance:
- Returns compliance export records
- Response includes EvidenceMetadata (INV-LOG-META-001)
- Tenant-scoped query

Scenario: SDSR-LOG-REC-AUD-O5-001

---

### Missing Capability Definitions (Added 2026-01-19)

> **NOTE:** The following capabilities were referenced by panels but lacked definitions.
> Use DECLARED if endpoint exists, DEFERRED if no backend support yet.

### Capability: activity.live_runs

Panel: ACT-LLM-LIVE-O1, ACT-LLM-LIVE-O3
Status: DECLARED
Added: 2026-01-19

Implementation:
- Endpoint: /api/v1/activity/runs
- Method: GET

Query Params:
- status: running (implicit filter)
- window: 24h

Acceptance:
- Returns list of currently running executions
- Tenant-scoped query

Scenario: PENDING

### Capability: activity.completed_runs

Panel: ACT-LLM-COMP-O1, ACT-LLM-COMP-O4
Status: DECLARED
Added: 2026-01-19

Implementation:
- Endpoint: /api/v1/activity/runs
- Method: GET

Query Params:
- status: completed (implicit filter)
- window: 24h

Acceptance:
- Returns list of completed executions
- Tenant-scoped query

Scenario: PENDING

### Capability: activity.risk_signals

Panel: ACT-LLM-LIVE-O2
Status: DECLARED
Added: 2026-01-19

Implementation:
- Endpoint: /api/v1/activity/attention-queue
- Method: GET

Acceptance:
- Returns executions with risk signals
- Tenant-scoped query

Scenario: PENDING

### Capability: activity.run_detail

Panel: ACT-LLM-COMP-O5
Status: DECLARED
Added: 2026-01-19

Implementation:
- Endpoint: /api/v1/activity/runs/{run_id}
- Method: GET

Acceptance:
- Returns detailed run information
- Tenant-scoped query

Scenario: PENDING

### Capability: activity.runtime_traces

Panel: ACT-LLM-LIVE-O4
Status: DEFERRED
Added: 2026-01-19

NOTE: No direct backend endpoint exists. Requires backend implementation.
Deferred until traces service is complete.

Implementation:
- Endpoint: null
- Method: GET

Scenario: DEFERRED

### Capability: overview.cost_summary

Panel: OVR-SUM-CI-O1
Status: DECLARED
Added: 2026-01-19

Implementation:
- Endpoint: /api/v1/overview/costs
- Method: GET

Acceptance:
- Returns cost summary for tenant
- Tenant-scoped query

Scenario: PENDING

### Capability: overview.costs

Panel: OVR-SUM-CI-O2, OVR-SUM-CI-O3, OVR-SUM-CI-O4
Status: DECLARED
Added: 2026-01-19

Implementation:
- Endpoint: /api/v1/overview/costs
- Method: GET

Acceptance:
- Returns cost breakdown by feature/model/anomaly
- Tenant-scoped query

Scenario: PENDING

### Capability: overview.decisions

Panel: OVR-SUM-DC-O4
Status: DECLARED
Added: 2026-01-19

Implementation:
- Endpoint: /api/v1/overview/decisions
- Method: GET

Acceptance:
- Returns pending decisions queue
- Tenant-scoped query

Scenario: PENDING

### Capability: overview.decisions_count

Panel: OVR-SUM-DC-O2
Status: DECLARED
Added: 2026-01-19

Implementation:
- Endpoint: /api/v1/overview/decisions/count
- Method: GET

Acceptance:
- Returns decisions count summary
- Tenant-scoped query

Scenario: PENDING

### Capability: overview.decisions_list

Panel: OVR-SUM-DC-O1
Status: DECLARED
Added: 2026-01-19

Implementation:
- Endpoint: /api/v1/overview/decisions
- Method: GET

Acceptance:
- Returns list of pending decisions
- Tenant-scoped query

Scenario: PENDING

### Capability: overview.recovery_stats

Panel: OVR-SUM-DC-O3
Status: DECLARED
Added: 2026-01-19

Implementation:
- Endpoint: /api/v1/overview/recovery-stats
- Method: GET

Acceptance:
- Returns recovery statistics
- Tenant-scoped query

Scenario: PENDING

### Capability: overview.incident_snapshot

Panel: OVR-SUM-HL-O2
Status: DEFERRED
Added: 2026-01-19

NOTE: Requires facade endpoint to aggregate incidents for overview.
Can be derived from /api/v1/incidents/metrics.

Implementation:
- Endpoint: null
- Method: GET

Scenario: DEFERRED

### Capability: overview.policy_snapshot

Panel: OVR-SUM-HL-O4
Status: DEFERRED
Added: 2026-01-19

NOTE: Requires facade endpoint to aggregate policies for overview.

Implementation:
- Endpoint: null
- Method: GET

Scenario: DEFERRED

### Capability: incidents.metrics_v2

Panel: INC-EV-ACT-O3, INC-EV-RES-O3
Status: DEFERRED
Added: 2026-01-19

NOTE: V2 metrics endpoint not yet implemented.
Deferred until v2 incidents service is complete.

Implementation:
- Endpoint: null
- Method: GET

Scenario: DEFERRED

### Capability: incidents.resolved_list_v2

Panel: INC-EV-RES-O1, INC-EV-RES-O4
Status: DEFERRED
Added: 2026-01-19

NOTE: V2 resolved list endpoint not yet implemented.
Deferred until v2 incidents service is complete.

Implementation:
- Endpoint: null
- Method: GET

Scenario: DEFERRED

### Capability: incidents.historical_distribution

Panel: INC-EV-HIST-O2
Status: DEFERRED
Added: 2026-01-19

NOTE: Historical distribution endpoint not yet implemented.

Implementation:
- Endpoint: null
- Method: GET

Scenario: DEFERRED

### Capability: incidents.historical_cost_trend

Panel: INC-EV-HIST-O4
Status: DEFERRED
Added: 2026-01-19

NOTE: Historical cost trend endpoint not yet implemented.

Implementation:
- Endpoint: null
- Method: GET

Scenario: DEFERRED

### Capability: logs.system

Panel: LOG-REC-SYS-O1, LOG-REC-SYS-O2, LOG-REC-SYS-O3, LOG-REC-SYS-O4, LOG-REC-SYS-O5
Status: DEFERRED
Added: 2026-01-19

NOTE: System logs capability not yet implemented.
Requires backend log aggregation service.

Implementation:
- Endpoint: null
- Method: GET

Scenario: DEFERRED

### Capability: policies.active_policies

Panel: POL-GOV-ACT-O1
Status: DECLARED
Added: 2026-01-19

Implementation:
- Endpoint: /api/v1/policy/active
- Method: GET

Acceptance:
- Returns list of active policies
- Tenant-scoped query

Scenario: PENDING

### Capability: policies.layer_state

Panel: POL-GOV-ACT-O4
Status: DECLARED
Added: 2026-01-19

Implementation:
- Endpoint: /api/v1/policy-layer/state
- Method: GET

Acceptance:
- Returns current policy layer state
- Tenant-scoped query

Scenario: PENDING

