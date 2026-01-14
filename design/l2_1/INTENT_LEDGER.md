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

Capability: overview.activity_snapshot

### Panel: OVR-SUM-HL-O2

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: HIGHLIGHTS
- Slot: 2

Class: interpretation
State: EMPTY

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

Capability: null

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
State: EMPTY

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

Capability: null

### Panel: OVR-SUM-DC-O1

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: DECISIONS
- Slot: 1

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: OVR-SUM-DC-O2

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: DECISIONS
- Slot: 2

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: OVR-SUM-DC-O3

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: DECISIONS
- Slot: 3

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: OVR-SUM-DC-O4

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: DECISIONS
- Slot: 4

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: OVR-SUM-CI-O1

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: COST_INTELLIGENCE
- Slot: 1

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: OVR-SUM-CI-O2

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: COST_INTELLIGENCE
- Slot: 2

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: OVR-SUM-CI-O3

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: COST_INTELLIGENCE
- Slot: 3

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: OVR-SUM-CI-O4

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: COST_INTELLIGENCE
- Slot: 4

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: ACT-LLM-LIVE-O1

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: LIVE
- Slot: 1

Class: interpretation
State: EMPTY

Purpose:
Show how many LLM runs are currently in progress.

What it shows:
- Total number of live LLM runs

What it explicitly does NOT show:
- No breakdown by model, agent, user, or cost
- No status reasons
- No controls

Capability: null

### Panel: ACT-LLM-LIVE-O2

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: LIVE
- Slot: 2

Class: interpretation
State: EMPTY

Purpose:
Surface live runs exceeding expected execution time.

What it shows:
- Count of live runs exceeding time threshold (e.g., > X minutes)

What it explicitly does NOT show:
- No root cause
- No cost data
- No termination control

Capability: null

### Panel: ACT-LLM-LIVE-O3

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: LIVE
- Slot: 3

Class: interpretation
State: EMPTY

Purpose:
Highlight live runs that are approaching failure or limits.

What it shows:
- Count of live runs flagged as near-threshold or unstable

What it explicitly does NOT show:
- No policy actions
- No manual override
- No mitigation controls

Capability: null

### Panel: ACT-LLM-LIVE-O4

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: LIVE
- Slot: 4

Class: interpretation
State: EMPTY

Purpose:
Indicate whether telemetry, logs, and traces are flowing for live runs.

What it shows:
- Percentage or status of live runs emitting evidence

What it explicitly does NOT show:
- No log contents
- No replay
- No export

Capability: null

### Panel: ACT-LLM-LIVE-O5

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: LIVE
- Slot: 5

Class: interpretation
State: EMPTY

Purpose:
Provide a coarse distribution of live runs by major dimension.

What it shows:
- Distribution by LLM provider, agent, or trigger type
  (exact dimension decided later)

What it explicitly does NOT show:
- No drill-down
- No per-run detail
- No controls

Capability: null

### Panel: ACT-LLM-COMP-O1

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: COMPLETED
- Slot: 1

Class: interpretation
State: EMPTY

Purpose:
Show how many LLM runs have completed in the selected window.

What it shows:
- Total completed runs count

What it explicitly does NOT show:
- No success/failure split
- No duration
- No cost

Capability: null

### Panel: ACT-LLM-COMP-O2

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: COMPLETED
- Slot: 2

Class: interpretation
State: EMPTY

Purpose:
Surface how many completed runs finished successfully.

What it shows:
- Count of successful runs

What it explicitly does NOT show:
- No quality scoring
- No downstream impact
- No policy attribution

Capability: null

### Panel: ACT-LLM-COMP-O3

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: COMPLETED
- Slot: 3

Class: interpretation
State: EMPTY

Purpose:
Expose completed runs that ended in failure.

What it shows:
- Count of failed runs

What it explicitly does NOT show:
- No root cause
- No retry controls
- No blame attribution

Capability: null

### Panel: ACT-LLM-COMP-O4

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: COMPLETED
- Slot: 4

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: ACT-LLM-COMP-O5

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: COMPLETED
- Slot: 5

Class: interpretation
State: EMPTY

Purpose:
Show runs that ended intentionally before completion.

What it shows:
- Count of aborted or cancelled runs

What it explicitly does NOT show:
- No initiator identity
- No reason codes
- No recovery options

Capability: null

### Panel: ACT-LLM-SIG-O1

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: SIGNALS
- Slot: 1

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: ACT-LLM-SIG-O2

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: SIGNALS
- Slot: 2

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: ACT-LLM-SIG-O3

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: SIGNALS
- Slot: 3

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: ACT-LLM-SIG-O4

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: SIGNALS
- Slot: 4

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: ACT-LLM-SIG-O5

Location:
- Domain: ACTIVITY
- Subdomain: LLM_RUNS
- Topic: SIGNALS
- Slot: 5

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: INC-EV-ACT-O1

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: ACTIVE
- Slot: 1

Class: evidence
State: EMPTY

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

Capability: null

### Panel: INC-EV-ACT-O2

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: ACTIVE
- Slot: 2

Class: interpretation
State: EMPTY

Purpose:
Explain why each incident occurred — cause and trigger classification.

What it shows:
- Triggering condition (cost threshold, token limit, time SLA, policy rule)
- Whether detected after violation or prevented before violation

What it explicitly does NOT show:
- No blame attribution
- No actions or remediation
- No policy editing

Capability: null

### Panel: INC-EV-ACT-O3

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: ACTIVE
- Slot: 3

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: INC-EV-ACT-O4

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: ACTIVE
- Slot: 4

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: INC-EV-ACT-O5

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: ACTIVE
- Slot: 5

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: INC-EV-RES-O1

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: RESOLVED
- Slot: 1

Class: evidence
State: EMPTY

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

Capability: null

### Panel: INC-EV-RES-O2

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: RESOLVED
- Slot: 2

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: INC-EV-RES-O3

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: RESOLVED
- Slot: 3

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: INC-EV-RES-O4

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: RESOLVED
- Slot: 4

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: INC-EV-RES-O5

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: RESOLVED
- Slot: 5

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: INC-EV-HIST-O1

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: HISTORICAL
- Slot: 1

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: INC-EV-HIST-O2

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: HISTORICAL
- Slot: 2

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: INC-EV-HIST-O3

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: HISTORICAL
- Slot: 3

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: INC-EV-HIST-O4

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: HISTORICAL
- Slot: 4

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: INC-EV-HIST-O5

Location:
- Domain: INCIDENTS
- Subdomain: EVENTS
- Topic: HISTORICAL
- Slot: 5

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: POL-GOV-ACT-O1

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: ACTIVE
- Slot: 1

Class: evidence
State: EMPTY

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

Capability: null

### Panel: POL-GOV-ACT-O2

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: ACTIVE
- Slot: 2

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: POL-GOV-ACT-O3

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: ACTIVE
- Slot: 3

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: POL-GOV-ACT-O4

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: ACTIVE
- Slot: 4

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: POL-GOV-ACT-O5

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: ACTIVE
- Slot: 5

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: POL-GOV-DFT-O1

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: DRAFTS
- Slot: 1

Class: evidence
State: EMPTY

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

Capability: null

### Panel: POL-GOV-DFT-O2

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: DRAFTS
- Slot: 2

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: POL-GOV-DFT-O3

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: DRAFTS
- Slot: 3

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: POL-GOV-DFT-O4

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: DRAFTS
- Slot: 4

Class: execution
State: EMPTY

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

Capability: null

### Panel: POL-GOV-DFT-O5

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: DRAFTS
- Slot: 5

Class: execution
State: EMPTY

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

Capability: null

### Panel: POL-GOV-LIB-O1

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: POLICY_LIBRARY
- Slot: 1

Class: evidence
State: EMPTY

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

Capability: null

### Panel: POL-GOV-LIB-O2

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: POLICY_LIBRARY
- Slot: 2

Class: interpretation
State: EMPTY

Purpose:
Show applicability and compatibility matrix — where each policy can be applied.

What it shows:
- Supported targets: LLMs, agents, human executors, run types
- Org-wide applicability
- Mutually exclusive policies, required prerequisites, known incompatibilities

What it explicitly does NOT show:
- No human override at this stage
- No adoption actions

Capability: null

### Panel: POL-GOV-LIB-O3

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: POLICY_LIBRARY
- Slot: 3

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: POL-GOV-LIB-O4

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: POLICY_LIBRARY
- Slot: 4

Class: execution
State: EMPTY

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

Capability: null

### Panel: POL-GOV-LIB-O5

Location:
- Domain: POLICIES
- Subdomain: GOVERNANCE
- Topic: POLICY_LIBRARY
- Slot: 5

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: POL-LIM-USG-O1

Location:
- Domain: POLICIES
- Subdomain: LIMITS
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

### Panel: POL-LIM-USG-O2

Location:
- Domain: POLICIES
- Subdomain: LIMITS
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

### Panel: POL-LIM-USG-O3

Location:
- Domain: POLICIES
- Subdomain: LIMITS
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

### Panel: POL-LIM-USG-O4

Location:
- Domain: POLICIES
- Subdomain: LIMITS
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

### Panel: POL-LIM-USG-O5

Location:
- Domain: POLICIES
- Subdomain: LIMITS
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

### Panel: POL-LIM-THR-O1

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: THRESHOLDS
- Slot: 1

Class: evidence
State: EMPTY

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

Capability: null

### Panel: POL-LIM-THR-O2

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: THRESHOLDS
- Slot: 2

Class: execution
State: EMPTY

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

Capability: null

### Panel: POL-LIM-THR-O3

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: THRESHOLDS
- Slot: 3

Class: execution
State: EMPTY

Purpose:
Provide blast radius and rollout strategy controls.

What it shows:
- Start scope: single LLM/agent
- Expansion path: group → global
- Rollout mode: shadow → enforce, partial enforcement (% of runs)
- Rollback switch: one-click revert
- High blast radius requires shadow period and review acknowledgement

What it explicitly does NOT show:
- No usage data
- No violation data

Capability: null

### Panel: POL-LIM-THR-O4

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: THRESHOLDS
- Slot: 4

Class: execution
State: EMPTY

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

Capability: null

### Panel: POL-LIM-THR-O5

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: THRESHOLDS
- Slot: 5

Class: execution
State: EMPTY

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

Capability: null

### Panel: POL-LIM-VIO-O1

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: VIOLATIONS
- Slot: 1

Class: evidence
State: EMPTY

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

Capability: null

### Panel: POL-LIM-VIO-O2

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: VIOLATIONS
- Slot: 2

Class: interpretation
State: EMPTY

Purpose:
Show violation classification and attribution — why and who.

What it shows:
- Aggregations: by limit type, by LLM, by agent, by human, by policy
- Primary trigger: cost overrun, token spike, time breach
- Secondary factor: retry loop, fan-out, poor prompt, downstream latency

What it explicitly does NOT show:
- No policy controls
- No excuses

Capability: null

### Panel: POL-LIM-VIO-O3

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: VIOLATIONS
- Slot: 3

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: POL-LIM-VIO-O4

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: VIOLATIONS
- Slot: 4

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: POL-LIM-VIO-O5

Location:
- Domain: POLICIES
- Subdomain: LIMITS
- Topic: VIOLATIONS
- Slot: 5

Class: interpretation
State: EMPTY

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

Capability: null

### Panel: LOG-REC-LLM-O1

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: LLM_RUNS
- Slot: 1

Class: evidence
State: EMPTY

Purpose:
Show the run log envelope — canonical immutable record per run.

What it shows:
- Run ID, start/end timestamp
- Executor type (LLM, agent, human), executor identity
- Outcome: success, failure, near threshold, terminated
- Correlation IDs: policy IDs, incident IDs, trace IDs
- Append-only, no summarization, no redaction

What it explicitly does NOT show:
- No interpretation
- No aggregation

Capability: null

### Panel: LOG-REC-LLM-O2

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: LLM_RUNS
- Slot: 2

Class: evidence
State: EMPTY

Purpose:
Show execution trace — step-by-step progression of the run.

What it shows:
- Step number, timestamp, action type (prompt, tool, API call, delegation)
- Inputs/outputs (hashed if sensitive)
- Latency per step, tokens in/out
- Deterministic replay graph

What it explicitly does NOT show:
- No summarization
- No policy judgment

Capability: null

### Panel: LOG-REC-LLM-O3

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: LLM_RUNS
- Slot: 3

Class: evidence
State: EMPTY

Purpose:
Show threshold and policy interaction trace — governance footprint per run.

What it shows:
- Threshold checks (cost/time/token/rate)
- Policy evaluations, near-breach warnings, violations
- Overrides (who, when, why)
- Per event: policy ID, rule evaluated, decision result, enforcer

What it explicitly does NOT show:
- No policy editing
- No recommendations

Capability: null

### Panel: LOG-REC-LLM-O4

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: LLM_RUNS
- Slot: 4

Class: evidence
State: EMPTY

Purpose:
Show 60-second incident replay window — what happened around the inflection point.

What it shows:
- T-30s → T+30s around inflection point
- Prompt changes, retry loops, latency spikes
- Cost acceleration, agent fan-out, human intervention
- Same time scale across all runs, replayable as sequence

What it explicitly does NOT show:
- No summarization
- No interpretation

Capability: null

### Panel: LOG-REC-LLM-O5

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: LLM_RUNS
- Slot: 5

Class: evidence
State: EMPTY

Purpose:
Show audit and export package — legally defensible evidence bundle.

What it shows:
- Audit metadata: accessed by, deterministic state hash, integrity checksum
- Retention class, compliance tags (SOC2, internal, legal)
- Exports: JSON (raw), CSV (events), PDF (timeline snapshot)
- Export does not mutate logs, every export is itself logged

What it explicitly does NOT show:
- No modification controls
- No redaction controls

Capability: null

### Panel: LOG-REC-SYS-O1

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: SYSTEM_LOGS
- Slot: 1

Class: evidence
State: EMPTY

Purpose:
Show environment snapshot — baseline state at run start.

What it shows:
- Customer environment ID, region/zone, VPC/subnet
- Node/pod/container ID, instance type
- CPU/memory allocation, disk I/O limits, network class
- Immutable environment fingerprint

What it explicitly does NOT show:
- No interpretation
- No recommendations

Capability: null

### Panel: LOG-REC-SYS-O2

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: SYSTEM_LOGS
- Slot: 2

Class: evidence
State: EMPTY

Purpose:
Show network and bandwidth telemetry — connectivity health during execution.

What it shows:
- Time-series: ingress/egress bandwidth, packet loss %, latency (p50/p95/p99)
- DNS resolution time, TLS handshake failures, connection retries
- Correlated with run timestamps, LLM provider calls, agent fan-out

What it explicitly does NOT show:
- No interpretation
- No blame attribution

Capability: null

### Panel: LOG-REC-SYS-O3

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: SYSTEM_LOGS
- Slot: 3

Class: evidence
State: EMPTY

Purpose:
Show infra interrupts and degradation events — what infra did to the run.

What it shows:
- Node restarts, pod evictions, autoscaling events
- CPU throttling, memory pressure/OOM, disk saturation, provider brownouts
- Per event: infra component, start/end time, severity, affected run IDs

What it explicitly does NOT show:
- No interpretation
- No recommendations

Capability: null

### Panel: LOG-REC-SYS-O4

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: SYSTEM_LOGS
- Slot: 4

Class: evidence
State: EMPTY

Purpose:
Show run-aligned infra replay window — infra state at moment of anomaly.

What it shows:
- 60-second window aligned to failure/near-threshold/cost spike/latency anomaly
- CPU spikes, network jitter, scaling reactions, provider API instability
- Time-aligned with LLM Runs → O4 (same timestamps, different layer)

What it explicitly does NOT show:
- No interpretation
- No blame shifting

Capability: null

### Panel: LOG-REC-SYS-O5

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: SYSTEM_LOGS
- Slot: 5

Class: interpretation
State: EMPTY

Purpose:
Show infra audit and attribution record — who is responsible.

What it shows:
- Infra fault attribution: customer infra, cloud provider, LLM provider, internal platform
- Confidence score, evidence references (O2-O4), linked run IDs
- Exports: SOC2 infra evidence, incident RCA attachments, customer-shareable report

What it explicitly does NOT show:
- No policy controls
- No recommendations

Capability: null

### Panel: LOG-REC-AUD-O1

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: AUDIT
- Slot: 1

Class: evidence
State: EMPTY

Purpose:
Show identity and authentication lifecycle — who accessed and how.

What it shows:
- Login/logout, token issuance/refresh/revocation
- Auth method (API key, OAuth, SSO, cert), MFA events
- Identity type: human, agent, service, system
- Per event: identity ID, auth provider, timestamp, source IP, session ID

What it explicitly does NOT show:
- No authorization decisions (that's O2)
- No interpretation

Capability: null

### Panel: LOG-REC-AUD-O2

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: AUDIT
- Slot: 2

Class: evidence
State: EMPTY

Purpose:
Show authorization and access decisions — what each identity was allowed to do.

What it shows:
- Resource accessed, action attempted
- Policy evaluated, decision (ALLOW/DENY/CONDITIONAL)
- Reason code (policy ID, rule ID), override flag
- Both allow and deny must be logged (silent allows illegal)

What it explicitly does NOT show:
- No policy editing
- No recommendations

Capability: null

### Panel: LOG-REC-AUD-O3

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: AUDIT
- Slot: 3

Class: evidence
State: EMPTY

Purpose:
Show trace and log access audit — who viewed, exported, or modified observability data.

What it shows:
- Actions: log view, trace replay, evidence export, redaction applied, deletion attempts
- Per action: actor identity, object accessed (run ID, trace ID), purpose tag, scope, timestamp

What it explicitly does NOT show:
- No modification controls
- No deletion controls (deletions must fail but are logged)

Capability: null

### Panel: LOG-REC-AUD-O4

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: AUDIT
- Slot: 4

Class: evidence
State: EMPTY

Purpose:
Show integrity and tamper detection — was any audit data altered or compromised.

What it shows:
- Integrity: hashes per log segment, hash chaining, write-once markers
- Clock skew detection, missing sequence detection
- Anomalies: hash mismatch, gaps in sequence, clock rollback, unauthorized mutation attempts

What it explicitly does NOT show:
- No modification controls
- No recovery actions

Capability: null

### Panel: LOG-REC-AUD-O5

Location:
- Domain: LOGS
- Subdomain: RECORDS
- Topic: AUDIT
- Slot: 5

Class: evidence
State: EMPTY

Purpose:
Show compliance and export record — what audit evidence was produced, shared, or certified.

What it shows:
- Per export: type (SOC2, ISO, internal, customer), scope, requestor, approval chain
- Redaction policy applied, delivery channel, retention class
- Auditor access (read-only), certification timestamps, evidence checksum

What it explicitly does NOT show:
- No modification controls
- No approval actions

Capability: null

---

## Capabilities

### Capability: overview.activity_snapshot

Panel: OVR-SUM-HL-O1
Status: OBSERVED
Verified: 2026-01-14

Implementation:
- Endpoint: /api/v1/activity/summary
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

