# PIN-074: M16 Agent Governance Console

**Serial:** PIN-074
**Title:** M16 Agent Governance Console - Profile, Activity & Health Dashboard
**Category:** Milestone / Specification / Governance Platform
**Status:** **COMPLETE**
**Created:** 2025-12-14
**Updated:** 2025-12-14
**Depends On:** PIN-073 (M15.1.1 SBA Inspector UI), PIN-072 (M15.1 SBA Foundations)
**Supersedes:** BudgetLLM naming (rebranded to StrategyBound)

---

## Executive Summary

M16 creates a **single dashboard** where you can see:
- What each agent is **set up to do** (Profile)
- What each agent is **doing right now** (Activity)
- Whether each agent is **working correctly** (Health)

---

## Terminology: Simple English

### UI Tab Names (Consumer-Facing)

| Tab | What It Shows |
|-----|---------------|
| **Profile** | Purpose, Permissions, Checklist, Score |
| **Activity** | Costs, Spending, Retries, Blockers |
| **Health** | Warnings and issues to fix |

### Term Mapping

| Technical Term | Simple English | Used In |
|----------------|----------------|---------|
| Winning Aspiration | **Purpose** | Profile tab |
| Where-to-Play | **Permissions** | Profile tab |
| How-to-Win | **Task Checklist** | Profile tab |
| Fulfillment % | **Completion Score** | Profile tab |
| Strategy Cascade | **Agent Rules** | Internal only |
| DoD (Definition of Done) | **Success Criteria** | Checklist |
| Cost/Risk Heatmap | **Cost & Risk Overview** | Activity tab |
| Budget Burn | **Spending Tracker** | Activity tab |
| Retry Decisions | **Retry Log** | Activity tab |
| Blocked Items | **Issues & Blockers** | Activity tab |
| Missing Capabilities | **Missing Tools** | Health tab |
| Undeclared Dependencies | **Unregistered Connections** | Health tab |
| No Orchestration Plan | **No Workflow Defined** | Health tab |
| Aspiration Mismatch | **Purpose vs Tasks Conflict** | Health tab |
| Marketplace-safe | **Ready to Publish** | Health tab |

### Internal vs External Names

| Context | Name |
|---------|------|
| **Code/APIs** | StrategyBound Engine, SBA |
| **UI Labels** | Simple English (above) |
| **Enterprise Sales** | AgentGovern |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENT GOVERNANCE CONSOLE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    1. PROFILE TAB                            │    │
│  │                                                              │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │    │
│  │  │   Purpose    │ │ Permissions  │ │   Checklist  │         │    │
│  │  │              │ │              │ │              │         │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘         │    │
│  │                         │                                    │    │
│  │                  Completion Score                            │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    2. ACTIVITY TAB                           │    │
│  │                                                              │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │    │
│  │  │  Cost &      │ │   Spending   │ │    Retry     │         │    │
│  │  │  Risk        │ │   Tracker    │ │     Log      │         │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘         │    │
│  │                         │                                    │    │
│  │                  Issues & Blockers                           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    3. HEALTH TAB                             │    │
│  │                                                              │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │    │
│  │  │   Missing    │ │ Unregistered │ │  Purpose vs  │         │    │
│  │  │    Tools     │ │ Connections  │ │   Tasks      │         │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘         │    │
│  │                                                              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tab 1: Profile

Shows what each agent is set up to do.

### 1.1 Purpose

**What it answers:** "What is this agent for?"

**Displayed on:**
- Agent cards
- Detail modal header
- Job dashboard

**UI Component:**
```tsx
<PurposeCard
  description="Scrapes product data from e-commerce sites"
  alignment={0.92}  // How well is it following its purpose?
/>
```

### 1.2 Permissions

**What it answers:** "What is this agent allowed to do?"

**Shows:**
- Domains it can access
- Tools it can use
- External systems it can connect to
- Resource limits (memory, time, budget)

**UI Component:**
```tsx
<PermissionsPanel
  domains={['web-scraping', 'data-extraction']}
  tools={['http_fetch', 'json_parse', 'csv_export']}
  limits={{ memory: '512MB', timeout: '5min', budget: 1000 }}
  violations={[]}  // Red flags if agent exceeded permissions
/>
```

### 1.3 Task Checklist

**What it answers:** "What does this agent need to complete?"

**Shows:**
- List of tasks to complete
- Tests that must pass
- Success criteria with checkmarks
- Real-time status updates

**UI Component:**
```tsx
<TaskChecklist
  tasks={[
    { name: 'Fetch product URLs', done: true },
    { name: 'Extract pricing data', done: true },
    { name: 'Validate data format', done: false },
    { name: 'Export to CSV', done: false }
  ]}
  tests={[
    { name: 'Schema validation', passed: true },
    { name: 'No duplicate entries', passed: false }
  ]}
/>
```

### 1.4 Completion Score

**What it answers:** "How done is this agent?"

**A single number (0-100%) based on:**
- Tasks completed
- Tests passed
- Success criteria met
- System feedback

**UI Component:**
```tsx
<CompletionScore
  value={75}
  breakdown={{
    tasks: 85,
    tests: 70,
    criteria: 65,
    system: 80
  }}
  threshold={80}  // Needs 80% to be "Ready to Publish"
/>
```

---

## Tab 2: Activity

Shows what's happening right now.

### 2.1 Cost & Risk Overview

**What it answers:** "How much is this costing and is it safe?"

**Shows:**
- Cost level for each worker (low/medium/high)
- Risk score for each operation
- Budget used vs allocated
- Anomalies highlighted in red

**UI Component:**
```tsx
<CostRiskOverview
  workers={[
    { id: 'worker-1', cost: 'low', risk: 0.2, budget_used: 45 },
    { id: 'worker-2', cost: 'high', risk: 0.7, budget_used: 89 }
  ]}
  onClick={(worker) => showDetails(worker)}
/>
```

### 2.2 Spending Tracker

**What it answers:** "Are we on budget?"

**Shows:**
- Actual spending vs expected (line chart)
- Per-worker breakdown
- Spike alerts

**UI Component:**
```tsx
<SpendingTracker
  actual={[10, 25, 40, 55, 80]}
  projected={[10, 20, 30, 40, 50]}
  budget_limit={100}
  anomalies={[{ index: 4, reason: 'Retry spike' }]}
/>
```

### 2.3 Retry Log

**What it answers:** "What failed and why?"

**Shows:**
- Every retry with timestamp
- Reason for retry
- Whether it helped or made things worse
- Impact on completion

**UI Component:**
```tsx
<RetryLog
  retries={[
    {
      time: '10:23:45',
      reason: 'API timeout',
      attempt: 2,
      outcome: 'success',
      risk_change: -0.1  // Risk decreased
    }
  ]}
/>
```

### 2.4 Issues & Blockers

**What it answers:** "Why is this agent stuck?"

**Categories:**
- Waiting on other agents
- API failures
- Missing tools
- Out of budget
- Circular dependencies

**UI Component:**
```tsx
<IssuesBlockers
  issues={[
    {
      type: 'api',
      message: 'Stripe API returned 503',
      since: '5 min ago',
      action: 'Retry'
    },
    {
      type: 'budget',
      message: 'Token quota exhausted',
      since: '2 min ago',
      action: 'Request more'
    }
  ]}
/>
```

---

## Tab 3: Health

Checks if the agent is set up correctly.

### 3.1 Missing Tools

**Warning:** Agent needs tools it doesn't have.

**Example:**
> Agent wants to search documents but RAG tool is not installed.

**UI Display:**
```tsx
<HealthWarning
  severity="error"
  title="Missing Tools"
  message="This agent needs 'rag_search' but it's not available"
  action="Install the missing tool or update agent configuration"
/>
```

### 3.2 Unregistered Connections

**Warning:** Agent is connecting to things it didn't declare.

**Example:**
> Agent is calling Stripe API but didn't list it in permissions.

**UI Display:**
```tsx
<HealthWarning
  severity="warning"
  title="Unregistered Connection"
  message="Agent is calling 'api.stripe.com' but it's not in the allowed list"
  action="Add to permissions or remove the API call"
/>
```

### 3.3 No Workflow Defined

**Warning:** Agent has no clear plan for how to operate.

**Missing:**
- Step sequence
- Retry rules
- Budget limits
- Coordination method

**UI Display:**
```tsx
<HealthWarning
  severity="error"
  title="No Workflow Defined"
  message="This agent has no retry rules or step sequence defined"
  action="Define workflow before publishing"
/>
```

### 3.4 Purpose vs Tasks Conflict

**Warning:** Agent's purpose doesn't match what it's doing.

**Example:**
> Purpose says "internal processing only" but tasks include external API calls.

**UI Display:**
```tsx
<HealthWarning
  severity="warning"
  title="Purpose Conflict"
  message="Purpose says 'internal only' but Task 3 calls external APIs"
  action="Update purpose or remove conflicting tasks"
/>
```

---

## Implementation Plan

### Phase 1: Profile Tab (M16.1)

| Component | Extends M15.1.1 | New Feature |
|-----------|-----------------|-------------|
| PurposeCard | Aspiration section | Alignment score |
| PermissionsPanel | Where-to-Play | Violation detection |
| TaskChecklist | How-to-Win | Interactive checkboxes |
| CompletionScore | Fulfillment badge | Breakdown chart |

### Phase 2: Activity Tab (M16.2)

| Component | Backend Dependency | Effort |
|-----------|-------------------|--------|
| CostRiskOverview | Worker metrics API | Medium |
| SpendingTracker | Cost tracking data | Medium |
| RetryLog | Retry event logging | High |
| IssuesBlockers | Dependency graph | High |

### Phase 3: Health Tab (M16.3)

| Component | Backend Dependency | Effort |
|-----------|-------------------|--------|
| Missing Tools check | Skill registry | Low |
| Unregistered Connections | Runtime hooks | Medium |
| No Workflow check | Schema validation | Medium |
| Purpose Conflict | Semantic analysis | High |

---

## API Endpoints

### Activity APIs

```python
# Cost and risk data
GET /api/v1/agents/{id}/activity/costs
Response: { workers: [{ id, cost_level, risk_score, budget_pct }] }

# Spending history
GET /api/v1/agents/{id}/activity/spending?range=24h
Response: { actual: [...], projected: [...], spikes: [...] }

# Retry log
GET /api/v1/agents/{id}/activity/retries
Response: { retries: [{ time, reason, attempt, outcome }] }

# Current blockers
GET /api/v1/agents/{id}/activity/blockers
Response: { blockers: [{ type, message, since, action }] }
```

### Health APIs

```python
# Full health check
POST /api/v1/agents/{id}/health/check
Response: {
  healthy: boolean,
  warnings: [...],
  errors: [...],
  suggestions: [...]
}
```

---

## UI Components (New)

| Component | Tab | Purpose |
|-----------|-----|---------|
| `PurposeCard` | Profile | Shows agent purpose with alignment |
| `PermissionsPanel` | Profile | Lists what agent can access |
| `TaskChecklist` | Profile | Interactive task/test list |
| `CompletionScore` | Profile | Score with breakdown |
| `CostRiskOverview` | Activity | Worker cost/risk grid |
| `SpendingTracker` | Activity | Budget chart |
| `RetryLog` | Activity | Retry timeline |
| `IssuesBlockers` | Activity | Current problems |
| `HealthWarning` | Health | Warning/error cards |
| `HealthSummary` | Health | Overall health status |

---

## File Structure

```
src/pages/sba/
├── SBAInspectorPage.tsx          # Updated with 3 tabs
├── components/
│   ├── tabs/
│   │   ├── ProfileTab.tsx        # NEW
│   │   ├── ActivityTab.tsx       # NEW
│   │   └── HealthTab.tsx         # NEW
│   ├── profile/
│   │   ├── PurposeCard.tsx       # NEW
│   │   ├── PermissionsPanel.tsx  # NEW
│   │   ├── TaskChecklist.tsx     # NEW
│   │   └── CompletionScore.tsx   # NEW
│   ├── activity/
│   │   ├── CostRiskOverview.tsx  # NEW
│   │   ├── SpendingTracker.tsx   # NEW
│   │   ├── RetryLog.tsx          # NEW
│   │   └── IssuesBlockers.tsx    # NEW
│   ├── health/
│   │   ├── HealthWarning.tsx     # NEW
│   │   └── HealthSummary.tsx     # NEW
│   └── ... (existing M15.1.1 components)
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Health check coverage | 100% of agents |
| Issue detection accuracy | >95% |
| Time to see blocked agent | <5 seconds |
| Score calculation time | <1 second |

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-073 | M15.1.1 SBA Inspector UI (foundation) |
| PIN-072 | M15.1 SBA Foundations (schema) |
| PIN-071 | A2A Protocol |
| PIN-070 | Safety Layer |

---

## Conclusion

M16 transforms the agent inspector into a **full governance dashboard** with three clear tabs:

| Tab | Before M16 | After M16 |
|-----|------------|-----------|
| **Profile** | Basic info | Purpose + Permissions + Checklist + Score |
| **Activity** | None | Live costs, spending, retries, blockers |
| **Health** | Spawn-time only | Continuous validation with clear warnings |

**Simple labels. Clear actions. No jargon.**

---

**Status:** M16 COMPLETE
