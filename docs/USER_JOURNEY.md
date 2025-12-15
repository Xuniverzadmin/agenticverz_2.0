# AOS User Journey Walkthrough

**Version:** 1.0
**Last Updated:** 2025-12-13

This guide walks through the complete user journey from first login to running production agent workflows.

---

## Journey Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER JOURNEY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ONBOARDING     2. EXPLORATION     3. FIRST WORKFLOW         │
│  ────────────      ─────────────      ─────────────────         │
│  • Get API Key     • View Dashboard   • Create Agent            │
│  • Login           • Check Skills     • Build Plan              │
│  • Set Up          • Understand       • Simulate                │
│                      Costs            • Execute                 │
│                                                                  │
│  4. ITERATION      5. SCALING         6. PRODUCTION             │
│  ───────────       ─────────          ──────────────            │
│  • Review Results  • Multiple Agents  • Monitor Metrics         │
│  • Handle Errors   • Budget Mgmt      • Handle Failures         │
│  • Optimize        • Recovery         • Continuous Ops          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Onboarding (Day 1)

### Step 1.1: Obtain Credentials
**Goal:** Get your API key and console access

**Actions:**
1. Sign up at https://agenticverz.com/signup
2. Verify email
3. Receive API key via email
4. Store key securely (password manager recommended)

**Time:** 5 minutes

---

### Step 1.2: First Login
**Goal:** Access the console and verify connection

**Actions:**
1. Navigate to https://agenticverz.com/console/login
2. Enter your API key in the input field
3. Click "Connect"
4. Verify status bar shows "Connected"

**What you'll see:**
```
┌─────────────────────────────────────────┐
│  AOS Console Login                       │
├─────────────────────────────────────────┤
│                                          │
│  API Key                                 │
│  ┌────────────────────────────────────┐ │
│  │ aos_beta_xxxxxxxxxxxxxxxxxxxxxxxx  │ │
│  └────────────────────────────────────┘ │
│                                          │
│  [  Connect  ]                           │
│                                          │
└─────────────────────────────────────────┘
```

**Time:** 2 minutes

---

### Step 1.3: Initial Setup
**Goal:** Familiarize yourself with the interface

**Dashboard Overview:**
```
┌─────────────────────────────────────────────────────────────────┐
│ AOS Console                              [Theme] [User] [Logout]│
├────────────┬────────────────────────────────────────────────────┤
│            │                                                     │
│ Dashboard  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐│
│ Agents     │  │ Agents  │  │  Jobs   │  │ Budget  │  │  RPS   ││
│ Jobs       │  │    5    │  │   23    │  │ $4.50   │  │  150   ││
│ Blackboard │  └─────────┘  └─────────┘  └─────────┘  └────────┘│
│ Messaging  │                                                     │
│ Credits    │  Recent Activity                                    │
│ Metrics    │  ─────────────────────────────────────────────────  │
│            │  • agent-001 completed job #45 (2 min ago)          │
│            │  • Simulation passed for workflow "data-fetch"      │
│            │  • agent-002 started (5 min ago)                    │
│            │                                                     │
└────────────┴────────────────────────────────────────────────────┘
```

**Time:** 10 minutes

---

## Phase 2: Exploration (Day 1-2)

### Step 2.1: Discover Available Skills
**Goal:** Understand what your agents can do

**Actions:**
1. From Dashboard, view "Available Skills" section
2. Or use API: `GET /api/v1/runtime/capabilities`

**Skills Available:**
| Skill | Purpose | Cost | Latency |
|-------|---------|------|---------|
| `http_call` | Make HTTP requests | 0¢ | ~500ms |
| `llm_invoke` | Call LLM (Claude) | 5¢ | ~2000ms |
| `json_transform` | Process JSON with JQ | 0¢ | ~10ms |
| `fs_read` | Read files | 0¢ | ~50ms |
| `fs_write` | Write files | 0¢ | ~100ms |
| `webhook_send` | Send webhooks | 0¢ | ~300ms |
| `email_send` | Send emails | 1¢ | ~500ms |

**Time:** 15 minutes

---

### Step 2.2: Understand Cost Model
**Goal:** Know what you'll pay before executing

**Key Concepts:**
- **Budget:** Set per-job limit (e.g., 100 cents)
- **Cost estimate:** Calculated before execution
- **Actual cost:** Deducted after completion

**Cost Formula:**
```
Total Cost = Σ (skill_cost × invocations)

Example:
  1 × http_call (0¢) + 2 × llm_invoke (5¢ each) + 1 × email_send (1¢)
  = 0 + 10 + 1 = 11¢
```

**Time:** 10 minutes

---

## Phase 3: First Workflow (Day 2-3)

### Step 3.1: Create Your First Agent
**Goal:** Have an agent ready to execute work

**Via Console:**
1. Navigate to Agents page
2. Click "Create Agent"
3. Fill form:
   - Name: `my-first-agent`
   - Type: `worker`
   - Description: `Test agent`
4. Click Create

**Via API:**
```bash
curl -X POST https://agenticverz.com/api/v1/agents \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-first-agent",
    "type": "worker",
    "description": "Test agent"
  }'
```

**Expected Response:**
```json
{
  "id": "agent-abc123",
  "name": "my-first-agent",
  "type": "worker",
  "status": "idle",
  "created_at": "2025-12-13T10:00:00Z"
}
```

**Time:** 5 minutes

---

### Step 3.2: Build Your First Plan
**Goal:** Define what the agent will do

**Example: Fetch and Summarize GitHub Profile**

```json
{
  "plan": [
    {
      "skill": "http_call",
      "params": {
        "url": "https://api.github.com/users/octocat",
        "method": "GET"
      }
    },
    {
      "skill": "json_transform",
      "params": {
        "jq": "{name: .name, repos: .public_repos, followers: .followers}"
      }
    },
    {
      "skill": "llm_invoke",
      "params": {
        "prompt": "Summarize this GitHub user profile in one sentence: {{previous_output}}"
      }
    }
  ],
  "budget_cents": 100
}
```

**Time:** 10 minutes

---

### Step 3.3: Simulate Before Executing
**Goal:** Verify plan is feasible and affordable

**Via Console:**
1. Navigate to Jobs page
2. Click "Simulate Job"
3. Paste your plan JSON
4. Review results

**Via API:**
```bash
curl -X POST https://agenticverz.com/api/v1/runtime/simulate \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": [...your plan...],
    "budget_cents": 100
  }'
```

**Simulation Result:**
```json
{
  "feasible": true,
  "estimated_cost_cents": 5,
  "estimated_duration_ms": 2510,
  "step_estimates": [
    {"skill_id": "http_call", "estimated_cost_cents": 0, "estimated_latency_ms": 500},
    {"skill_id": "json_transform", "estimated_cost_cents": 0, "estimated_latency_ms": 10},
    {"skill_id": "llm_invoke", "estimated_cost_cents": 5, "estimated_latency_ms": 2000}
  ],
  "budget_remaining_cents": 95,
  "budget_sufficient": true,
  "risks": []
}
```

**Decision point:** If `feasible: true` and `budget_sufficient: true`, proceed to execution.

**Time:** 5 minutes

---

### Step 3.4: Execute the Workflow
**Goal:** Run the plan and get results

**Via API:**
```bash
curl -X POST https://agenticverz.com/api/v1/runs \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-abc123",
    "plan": [...your plan...],
    "budget_cents": 100
  }'
```

**Response:**
```json
{
  "run_id": "run-xyz789",
  "status": "running",
  "started_at": "2025-12-13T10:05:00Z"
}
```

**Check Status:**
```bash
curl https://agenticverz.com/api/v1/runs/run-xyz789 \
  -H "X-API-Key: $API_KEY"
```

**Time:** 5 minutes

---

## Phase 4: Iteration (Week 1)

### Step 4.1: Review Results
**Goal:** Understand what happened

**Successful Run Output:**
```json
{
  "run_id": "run-xyz789",
  "status": "completed",
  "result": {
    "output": "Octocat is a prolific GitHub user with 8 public repositories and over 9,000 followers.",
    "steps_completed": 3,
    "total_cost_cents": 5
  },
  "completed_at": "2025-12-13T10:05:03Z"
}
```

**Time:** 5 minutes

---

### Step 4.2: Handle Errors
**Goal:** Learn to debug failed runs

**Common Failure Patterns:**
1. **Budget exceeded:** Increase budget or reduce steps
2. **Skill unavailable:** Check capabilities endpoint
3. **Rate limited:** Wait and retry with backoff
4. **External failure:** HTTP target unreachable

**Debugging Flow:**
```
Run Failed
    │
    ▼
Check run status
    │
    ├─► budget_exceeded → Increase budget
    │
    ├─► rate_limited → Wait, retry
    │
    ├─► skill_error → Check skill params
    │
    └─► external_error → Check target URL
```

**Time:** 30 minutes (learning)

---

### Step 4.3: Optimize Workflows
**Goal:** Reduce cost and latency

**Optimization Tips:**
1. **Batch operations:** Fewer LLM calls = lower cost
2. **Cache results:** Use blackboard for shared data
3. **Parallel steps:** Independent steps can run concurrently
4. **Right-size prompts:** Shorter prompts = faster/cheaper

**Time:** Ongoing

---

## Phase 5: Scaling (Week 2+)

### Step 5.1: Multiple Agents
**Goal:** Distribute work across agents

**Agent Types:**
- **Orchestrator:** Plans and delegates
- **Worker:** Executes specific tasks
- **Specialist:** Domain-specific skills

**Time:** 1 hour setup

---

### Step 5.2: Budget Management
**Goal:** Control spending across agents

**Strategies:**
1. Set per-agent daily limits
2. Set per-job maximum budgets
3. Monitor via Credits page
4. Set alerts for threshold breaches

**Time:** 30 minutes setup

---

## Phase 6: Production (Month 1+)

### Step 6.1: Monitor Metrics
**Goal:** Ensure healthy operations

**Key Metrics:**
- Success rate (target: >99%)
- Average latency (target: <3s)
- Error rate (target: <1%)
- Cost per job (optimize continuously)

**Time:** Ongoing

---

### Step 6.2: Handle Failures
**Goal:** Recover gracefully from issues

**Recovery Process:**
1. Check `/api/v1/recovery/candidates`
2. Review failure patterns
3. Fix root cause
4. Retry or compensate

**Time:** As needed

---

## Summary Checklist

### First Day
- [ ] Obtained API key
- [ ] Logged into console
- [ ] Explored dashboard
- [ ] Reviewed available skills
- [ ] Understood cost model

### First Week
- [ ] Created first agent
- [ ] Built first workflow plan
- [ ] Ran successful simulation
- [ ] Executed first run
- [ ] Handled first error

### First Month
- [ ] Optimized workflows
- [ ] Set up multiple agents
- [ ] Implemented budget controls
- [ ] Established monitoring
- [ ] Running in production

---

## Next Steps

1. **Read:** [AOS Test Handbook](./AOS_TEST_HANDBOOK.md)
2. **Practice:** [Beta Test Scenarios](./BETA_INSTRUCTIONS.md)
3. **Troubleshoot:** [Error Playbook](./ERROR_PLAYBOOK.md)
4. **Understand:** [Architecture Overview](./ARCHITECTURE_OVERVIEW.md)
