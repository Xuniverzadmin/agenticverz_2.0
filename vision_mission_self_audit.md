# Vision, Mission, and Self-Audit

## Vision
Build a AI governance console system that monitors each LLM run, captures events, supports replay, and is auditable, deterministic, and traceable by default. The system must be agnostic to customer environments. Added benefit of policy management that governs LLM behavior and control management that enforces LLM limits. Every execution path is linear, every decision has a single owner, and every change is accountable.

## Mission
Deliver HOC with strict layer integrity, explicit authority boundaries, and zero ambiguity in wiring.
Ship governance capabilities that work across customer environments while preserving determinism, replayability, and auditability.

### Domain Goals (hoc/cus/*)
- Overview: Whats happening. What needs my attention. What needs my decision.
- Overview > Summary: Cross-domain highlights.
- Overview > Summary > Topic Tabs: Highlights. Cost Intelligence. Decisions.

- Activity: What are my LLM runs. What happened to the runs. What needs my attention.
- Activity > LLM Runs > Topic Tabs: Live. Completed. Risk Signals.

- Incidents: What are my success/failure/near-threshold runs that are currently active. What runs have been prevented from cost overrun or failure due to policy governance. My history of incidents from LLM runs.
- Incidents > Events > Topic Tabs: Active. Resolved. Historical.

- Policies: What policies are active and preventing/regulating incidents. Which policies require my decision to approve/reject based on success/failure/near-threshold runs (lessons learned to be converted to policies). What is my policy library vs overall policies available for consumption.
- Policies > Governance > Topic Tabs: Active. Drafts. Policy Library.

- Controls: Configure my environment and LLM with policies, limits, and control.
- Controls > Usage: Topic tab 1.
- Controls > Thresholds: Topic tab 2.
- Controls > Violations: Topic tab 3.
- Controls > Limits: Subdomain.

- Logs: Logs, traces, snapshot of success/failure/near-threshold LLM runs, evidence export for CTO or SOC2 compliance. 60s incident replay logs with the 30th second as inflection. System infra logs and traces during corresponding LLM runs (LLM provider, customer infra). Audit of logs (human ID, deterministic state condition, integrity state conditions).
- Logs > Records > Topic Tabs: LLM Runs. System Logs. Audit.

- Analytics: Provide cost performance with and without AI console support. Provide LLM performance by provider/model. Provide customer usage by human actor ID.
- Analytics > Summary > Topic Tabs: Cost Intelligence. LLM Provider Analytics. LLM Usage Analytics.

- Integrations: Configure environment/LLM to be monitored. Provide guide/FAQ/blogs. Install AOS SDK into the environment.
- Integrations > Configure > Topic Tabs: Env/LLM. Guide. SDK.

- API Keys: Provide access and control to AI console.
- API Keys > Configure > Topic Tabs: Key Management.

- Accounts: Tenant and sub-tenant management, billing plan, subscriptions, account management.
- Accounts > Account Management > Topic Tab: CRUD.

## Self-Audit: In-Execution (Pre-Commit)
Ask before merging or shipping:
1. Does the change respect the HOC layer topology and import rules?
2. Are routers properly wired to an entrypoint?
3. Is any L2 calling L5/L6 directly?
4. Are engines free of DB/ORM imports?
5. Are drivers free of business logic?
6. Did I introduce any new “service” files or layer violations?
7. Is the integration environment-agnostic (no hard-coded provider assumptions)?

If any answer is “no” or “unclear,” stop and fix or escalate.

## Self-Audit: Post-Execution (Post-Change)
After changes land:
1. Re-check wiring in entrypoints (`backend/app/main.py`, `backend/app/hoc/api/int/agent/main.py`)
2. Re-run layer boundary or cross-domain validators if relevant
3. Re-scan for dead or unused modules introduced by the change
4. Update any audit notes, migration logs, or docs touched by the change
5. Confirm no governance or architecture rules were broken

## Escalation Triggers
Stop and ask for approval if:
- You need to delete or move files
- You’re changing routers or entrypoint wiring
- You’re altering layer responsibilities
- A change violates engine/driver constraints

## Definition of Done
A change is done only when:
- It is wired
- It is testable
- It respects layer boundaries
- It can be traced to a governance or architectural rule
