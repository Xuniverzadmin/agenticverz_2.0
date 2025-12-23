# PIN-138: M28 Console Structure Audit

**Status:** COMPLETE
**Category:** M28 Planning / Architecture Audit
**Created:** 2025-12-23
**Milestone:** M28 Console Rebuild

---

## Summary

Comprehensive audit of the current console structure across M0-M27 milestones. Provides a DELETE list, REHOME/MERGE recommendations, and gap analysis to support the M28 Console Rebuild with clear Founder/Customer separation.

---

## Strategic Vision

### Founder Ops Console (Internal, Hidden)
- Internal control plane: eyes, ears, brain
- Behavioral truth for founders
- Questions: "Who should I call today?", "What's breaking?", "Where's the revenue risk?"

### Customer Console (Product Surface)
- Trust & control for customers
- Tenant-scoped operations
- Questions: "Is my AI safe?", "What happened?", "How do I stop it?"

### Constraints
- M25 policy loop, confidence model, evidence artifacts are FROZEN
- Console must be read-only over enforcement paths
- No re-computation of policy or graduation logic in UI

---

## TASK 1: Current State Map

### Backend API Routes

| Route | Original Purpose | Actual Usage Today | Capability (Milestone) | Belongs To |
|-------|-----------------|-------------------|----------------------|------------|
| **GUARD CONSOLE (/guard/*)** |
| `/guard/status` | Protection status | Customer health check | M23 | Customer |
| `/guard/snapshot/today` | Today's metrics | Customer dashboard | M23 | Customer |
| `/guard/killswitch/activate` | Emergency stop | Critical control | M22 | Customer |
| `/guard/killswitch/deactivate` | Resume operations | Critical control | M22 | Customer |
| `/guard/killswitch/status` | Check killswitch state | Status check | M22 | Customer |
| `/guard/incidents` | List incidents | Incident browsing | M23 | Customer |
| `/guard/incidents/search` | Search incidents | Customer search | M23 | Customer |
| `/guard/incidents/{id}` | Get single incident | Detail view | M23 | Customer |
| `/guard/incidents/{id}/timeline` | Decision timeline | Trust transparency | M23 | Customer |
| `/guard/incidents/{id}/export` | PDF evidence export | Compliance | M24 | Customer |
| `/guard/replay/{call_id}` | Replay with certificates | Audit/debug | M23 | Customer |
| `/guard/keys` | API key management | Customer self-service | M23 | Customer |
| `/guard/settings` | Read-only settings | Configuration view | M23 | Customer |
| `/guard/demo/seed-incident` | Seed demo data | Demo only | M23 | **DELETE** |
| `/guard/validate/content-accuracy` | Content validation | Demo/test | M23 | **DELETE** |
| `/guard/onboarding/verify` | Real safety test | Onboarding | M24 | Customer |
| `/guard/onboarding/status` | Onboarding progress | Onboarding | M24 | Customer |
| **OPERATOR CONSOLE (/operator/*)** |
| `/operator/status` | System-wide health | Cross-tenant oversight | M22 | Founder |
| `/operator/tenants/top` | Top tenants by metric | Business intelligence | M22 | Founder |
| `/operator/incidents` | Cross-tenant incidents | System-wide view | M22 | Founder |
| `/operator/tenants/{id}` | Tenant profile | Tenant drilldown | M22 | Founder |
| `/operator/tenants/{id}/metrics` | Tenant metrics | Tenant health | M22 | Founder |
| `/operator/tenants/{id}/guardrails` | Tenant guardrails | Config view | M22 | Founder |
| `/operator/tenants/{id}/incidents` | Tenant incidents | Tenant drill | M22 | Founder |
| `/operator/tenants/{id}/keys` | Tenant keys | Admin view | M22 | Founder |
| `/operator/tenants/{id}/freeze` | Freeze tenant | Emergency control | M22 | Founder |
| `/operator/tenants/{id}/unfreeze` | Unfreeze tenant | Emergency control | M22 | Founder |
| `/operator/audit/policy` | Policy enforcement audit | Governance view | M22 | Founder |
| `/operator/audit/policy/export` | CSV export | Compliance | M22 | Founder |
| `/operator/guardrails` | Guardrail types | Reference data | M22 | **MERGE** |
| `/operator/replay/*` | Operator replay | Debug/audit | M22 | Founder |
| **OPS/FOUNDER CONSOLE (/ops/*)** |
| `/ops/pulse` | System pulse (business health) | Founder dashboard | M24 | Founder |
| `/ops/customers` | Customer intelligence | Customer profiles | M24 | Founder |
| `/ops/customers/at-risk` | At-risk customers | "Who to call today?" | M24 | Founder |
| `/ops/customers/{id}/timeline` | Customer event timeline | Behavioral analysis | M24 | Founder |
| `/ops/incidents/patterns` | Systemic failure patterns | Pattern detection | M24 | Founder |
| `/ops/stickiness` | Product stickiness metrics | Retention analysis | M24 | Founder |
| `/ops/revenue` | Revenue & risk estimates | Financial intelligence | M24 | Founder |
| `/ops/infra` | Infrastructure & limits | Capacity planning | M24 | Founder |
| `/ops/playbooks` | Founder intervention playbooks | Actionable guides | M24 | Founder |
| `/ops/events` | Raw event stream | Replay Lab source | M24 | Founder |
| `/ops/jobs/detect-silent-churn` | Background job trigger | System job | M24 | **DELETE** |
| `/ops/jobs/compute-stickiness` | Background job trigger | System job | M24 | **DELETE** |
| **MAIN CONSOLE (Protected Routes)** |
| `/dashboard` | Main dashboard | Developer view | M0 | Customer |
| `/skills` | Skills registry | Skill management | M11 | Customer |
| `/simulation` | Job simulator | Pre-execution test | M5 | Customer |
| `/traces` | Execution traces | Debug/audit | M4 | Customer |
| `/replay` | Job runner | Re-execution | M5 | Customer |
| `/workers` | Worker studio | Execution console | M12 | Customer |
| `/workers/console` | Worker execution | Live execution | M12 | Customer |
| `/failures` | Failure catalog | Failure browsing | M9 | Customer |
| `/recovery` | Recovery suggestions | Self-healing | M10 | Customer |
| `/integration` | M25 Integration Dashboard | Loop monitoring | M25 | Founder |
| `/integration/loop/:incidentId` | Loop status | Individual loop | M25 | Founder |
| `/memory` | Blackboard/Memory | State inspection | M7 | Customer |
| `/sba` | SBA Inspector | Agent governance | M15 | Founder |
| `/credits` | Credit usage | Billing view | M12 | Customer |
| `/metrics` | System metrics | Observability | M6 | **MERGE** |
| `/agents` | Legacy redirect | Unused | M0 | **DELETE** |
| `/blackboard` | Legacy redirect | Unused | M0 | **DELETE** |
| `/jobs/*` | Legacy redirect | Unused | M0 | **DELETE** |
| `/messaging` | Legacy redirect | Unused | M0 | **DELETE** |

### Frontend Pages

| Page | Original Purpose | Actual Usage | Belongs To |
|------|-----------------|--------------|------------|
| `GuardConsoleEntry` | Guard console entry | Customer entry | Customer |
| `GuardDashboard` | Guard overview | Customer dashboard | Customer |
| `GuardOverview` | Guard status | Customer status | Customer |
| `IncidentsPage` | Incident list | Customer incident view | Customer |
| `DecisionTimeline` | Trust transparency | Customer audit | Customer |
| `KillSwitchPage` | Emergency control | Critical control | Customer |
| `GuardSettingsPage` | Settings view | Customer config | Customer |
| `LiveActivityPage` | Live activity feed | Customer monitoring | Customer |
| `LogsPage` | Log viewer | Customer debug | Customer |
| `AccountPage` | Account management | Customer self-service | Customer |
| `SupportPage` | Support access | Customer support | Customer |
| `OpsConsoleEntry` | Ops console entry | Founder entry | Founder |
| `FounderOpsConsole` | Founder dashboard | Founder intelligence | Founder |
| `SBAInspectorPage` | Agent governance | Founder oversight | Founder |
| `IntegrationDashboard` | M25 loop monitor | Founder oversight | Founder |
| `LoopStatusPage` | Individual loop status | Founder inspection | Founder |
| `GlobalOverview` | Operator overview | Founder system view | Founder |
| `TenantDrilldown` | Tenant details | Founder tenant view | Founder |
| `PolicyAuditLog` | Policy audit | Founder governance | Founder |
| `LiveIncidentStream` | Cross-tenant incidents | Founder monitoring | Founder |
| `ReplayLab` | Replay analysis | Founder debug | Founder |
| `DashboardPage` | Developer dashboard | Customer main view | Customer |
| `SkillsPage` | Skills registry | Customer skill management | Customer |
| `JobSimulatorPage` | Pre-execution test | Customer simulation | Customer |
| `JobRunnerPage` | Job execution | Customer execution | Customer |
| `TracesPage` | Trace viewer | Customer debug | Customer |
| `FailuresPage` | Failure catalog | Customer failure view | Customer |
| `RecoveryPage` | Recovery suggestions | Customer self-healing | Customer |
| `BlackboardPage` | Memory/state viewer | Customer state inspection | Customer |
| `CreditsPage` | Credit usage | Customer billing | Customer |
| `MetricsPage` | System metrics | Internal metrics | **MERGE** |
| `WorkerStudioHome` | Worker overview | Customer execution | Customer |
| `WorkerExecutionConsole` | Live execution | Customer execution | Customer |

---

## TASK 2: DELETE LIST

### Mandatory Deletions

| Route/Page | Reason | Category |
|------------|--------|----------|
| `/guard/demo/seed-incident` | Vanity/demo-only - no production value | Demo-only |
| `/guard/validate/content-accuracy` | Internal testing exposed to customer | Internal mechanics exposed |
| `/ops/jobs/detect-silent-churn` | Background job trigger - should be internal cron | Internal mechanics exposed |
| `/ops/jobs/compute-stickiness` | Background job trigger - should be internal cron | Internal mechanics exposed |
| `/agents` (redirect) | Legacy redirect - unused since M11 | Redundant |
| `/blackboard` (redirect) | Legacy redirect - now `/memory` | Redundant |
| `/jobs/*` (redirect) | Legacy redirect - now `/simulation` | Redundant |
| `/messaging` (redirect) | Legacy redirect - feature removed | No clear decision supported |
| `IncidentConsolePage.jsx` (landing) | Duplicate of guard console | Redundant |

### Deletion Rationale Categories

1. **Redundant**: Route duplicates another or redirects to deprecated path
2. **Violates separation of concerns**: Customer route exposing founder/internal mechanics
3. **Internal mechanics exposed**: Background jobs, cron triggers visible in UI
4. **No clear decision supported**: Feature doesn't answer any user question
5. **Vanity/demo-only**: Only used for demos, no production value

---

## TASK 3: REHOME/MERGE LIST

### Proposed Structure

```
/fops/*     → Founder Ops Console (internal, hidden)
/console/*  → Customer Console (product-facing)
```

### REHOME Recommendations

| Current Route | New Route | Rationale |
|--------------|-----------|-----------|
| `/operator/*` | `/fops/operator/*` | Operator is founder-facing |
| `/ops/*` | `/fops/intel/*` | Ops is founder intelligence |
| `/sba` | `/fops/sba/*` | SBA governance is founder-facing |
| `/integration/*` | `/fops/loop/*` | M25 loop is founder-facing |
| `/metrics` | `/fops/metrics` | System metrics are internal |
| `/guard/*` | `/console/guard/*` | Guard is customer-facing |
| `/dashboard` | `/console/dashboard` | Customer main view |
| `/skills` | `/console/skills` | Customer skill management |
| `/simulation` | `/console/simulation` | Customer simulation |
| `/traces` | `/console/traces` | Customer debugging |
| `/replay` | `/console/replay` | Customer execution |
| `/workers/*` | `/console/workers/*` | Customer execution |
| `/failures` | `/console/failures` | Customer failure view |
| `/recovery` | `/console/recovery` | Customer self-healing |
| `/memory` | `/console/memory` | Customer state inspection |
| `/credits` | `/console/credits` | Customer billing |

### MERGE Recommendations

| Current Routes | Merged Route | Rationale |
|---------------|--------------|-----------|
| `/operator/guardrails` + `/guard/settings` | `/fops/config/guardrails` | Guardrail config is one concept |
| `/metrics` + Prometheus endpoints | `/fops/observability` | All observability in one place |
| `/operator/replay/*` + `/replay` | Keep separate | Different audiences, different UX |

### Backend API Consolidation

| Current Prefix | New Prefix | Handler Module |
|----------------|------------|----------------|
| `/guard/*` | `/console/guard/*` | `app/api/guard.py` |
| `/operator/*` | `/fops/operator/*` | `app/api/operator.py` |
| `/ops/*` | `/fops/intel/*` | `app/api/ops.py` |

---

## TASK 4: Gap Check

### Founder Questions Currently NOT Supported

| Question | Gap | Recommendation |
|----------|-----|----------------|
| "What's the ROI of M25 policy loop?" | No policy ROI dashboard | Add `/fops/loop/roi` with prevented incidents vs cost |
| "Which customers are about to churn?" | At-risk detection exists but lacks predictive scoring | Enhance `/fops/intel/at-risk` with ML-based churn prediction |
| "What's the system-wide failure rate trend?" | Pattern view exists but no trend analysis | Add `/fops/intel/trends` with time-series analysis |
| "How much money did we save customers today?" | Prevention value not quantified | Add `/fops/loop/value` with estimated savings |
| "What's the confidence distribution across all policies?" | No policy portfolio view | Add `/fops/loop/portfolio` with confidence histogram |
| "Which skills are causing the most failures?" | Failure catalog lacks skill attribution | Enhance `/console/failures` with skill breakdown |
| "What's the average time from incident to prevention?" | No loop velocity metrics | Add `/fops/loop/velocity` with time-to-prevention |
| "How many policies are in shadow vs active?" | No policy lifecycle view | Add `/fops/loop/lifecycle` with policy states |

### Customer Questions Currently NOT Supported

| Question | Gap | Recommendation |
|----------|-----|----------------|
| "How safe is my AI compared to others?" | No benchmark comparison | Out of scope (competitive data) |
| "What would have happened without Guard?" | No counterfactual analysis | Add `/console/guard/value` with "what-if" simulation |
| "Can I see my safety score over time?" | Point-in-time only | Add `/console/guard/history` with trend view |
| "How do I know my API key is secure?" | Key management exists but no audit trail | Add `/console/guard/keys/audit` |

---

## Implementation Priority

### Phase 1: Cleanup (DELETE)
1. Remove demo/test endpoints from production
2. Remove legacy redirects
3. Remove job trigger endpoints (move to internal cron)

### Phase 2: Separation (REHOME)
1. Create `/fops/*` namespace
2. Create `/console/*` namespace
3. Migrate routes with backward compatibility

### Phase 3: Enhancement (GAP FILL)
1. Add loop ROI dashboard
2. Add policy portfolio view
3. Add loop velocity metrics

---

## Related PINs

- PIN-137: M25 Stabilization & Hygiene Freeze (constraints)
- PIN-130: M25 Graduation System Design (loop mechanics)
- PIN-111: Ops Console Implementation (current state)
- PIN-100: M23 AI Incident Console (guard implementation)

---

## Changelog

- 2025-12-23: Initial audit complete - DELETE, REHOME, GAP analysis done
