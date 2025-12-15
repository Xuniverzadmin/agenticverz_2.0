# AOS Console Wireframes

**Version:** 1.0.0
**Target URL:** https://agenticverz.com/console
**Created:** 2025-12-13

---

## Overview

This document contains detailed wireframes for all 10 pages of the AOS Console web application. Each wireframe includes visual structure, component placement, interactions, and responsive behavior.

---

## Global Layout Structure

```
+------------------------------------------------------------------+
|                        HEADER BAR (64px)                         |
| [Logo] [Dashboard] [Agents] [Jobs] [Blackboard] [Messages] [...] |
|                                        [Credits: 1,234] [Avatar] |
+------------------------------------------------------------------+
|        |                                                         |
|  NAV   |                    MAIN CONTENT                         |
| (240px)|                      (flex-1)                           |
|        |                                                         |
|  [...]  |                                                         |
|        |                                                         |
+--------+---------------------------------------------------------+
|                        STATUS BAR (32px)                         |
| [API: Connected] [Redis: OK] [DB: OK]        [v1.0.0] [UTC Time] |
+------------------------------------------------------------------+
```

---

## Page 1: Dashboard (Home)

**URL:** `https://agenticverz.com/console/`

### Purpose
Executive overview of system health, active jobs, and key metrics at a glance.

### Visual Layout

```
+------------------------------------------------------------------+
| HEADER                                                           |
+------------------------------------------------------------------+
| SIDEBAR |                                                        |
|         |  WELCOME BANNER                                        |
| [Home]  |  +---------------------------------------------------+ |
| [Agents]|  | Welcome back, {tenant_name}                       | |
| [Jobs]  |  | Last login: 2025-12-13 14:32 UTC                  | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  METRICS ROW (4 cards)                                 |
|         |  +------------+ +------------+ +------------+ +------+ |
|         |  | ACTIVE     | | COMPLETED  | | FAILED     | |CREDITS|
|         |  | JOBS       | | TODAY      | | TODAY      | |       |
|         |  |   [12]     | |   [847]    | |   [3]      | |[9,847]|
|         |  | +15% ▲     | | +23% ▲     | | -50% ▼     | |-2% ▼  |
|         |  +------------+ +------------+ +------------+ +------+ |
|         |                                                        |
|         |  +---------------------------+ +---------------------+ |
|         |  | ACTIVE JOBS TABLE         | | SYSTEM HEALTH       | |
|         |  +---------------------------+ +---------------------+ |
|         |  | Job ID    | Status | Prog | | API       [██████] | |
|         |  |-----------+--------+------| | Database  [██████] | |
|         |  | job_a1b2  | running| 45%  | | Redis     [██████] | |
|         |  | job_c3d4  | running| 12%  | | Workers   [████░░] | |
|         |  | job_e5f6  | pending| 0%   | |                     | |
|         |  | [View All Jobs →]         | | [View Metrics →]    | |
|         |  +---------------------------+ +---------------------+ |
|         |                                                        |
|         |  +---------------------------+ +---------------------+ |
|         |  | RECENT ACTIVITY           | | CREDIT USAGE (7d)   | |
|         |  +---------------------------+ +---------------------+ |
|         |  | 14:32 Job job_a1b2 started| |     ┌────────────┐  | |
|         |  | 14:30 Agent worker_3 reg  | |     │    ▄▄▄     │  | |
|         |  | 14:28 Invoke completed    | |     │   ▄████▄   │  | |
|         |  | 14:25 Job job_x9y8 done   | |     │  ▄██████▄  │  | |
|         |  | [View All Activity →]     | |     └────────────┘  | |
|         |  +---------------------------+ +---------------------+ |
+------------------------------------------------------------------+
| STATUS BAR                                                       |
+------------------------------------------------------------------+
```

### Components Used
- `<WelcomeBanner tenant={tenant} />`
- `<MetricCard title value trend />`
- `<ActiveJobsTable jobs={activeJobs} limit={5} />`
- `<SystemHealthPanel services={healthStatus} />`
- `<ActivityFeed events={recentEvents} limit={5} />`
- `<CreditUsageChart data={creditHistory} days={7} />`

### Interactions
- Click metric card → Navigate to relevant page
- Click job row → Navigate to Job Detail
- Click "View All" links → Navigate to full list pages
- Auto-refresh every 30 seconds

### Responsive Behavior
- **Desktop (>1200px):** 2-column grid layout
- **Tablet (768-1200px):** Single column, stacked cards
- **Mobile (<768px):** Collapsed sidebar, stacked cards, hamburger menu

---

## Page 2: Agents Console

**URL:** `https://agenticverz.com/console/agents`

### Purpose
Monitor all registered agent instances, their status, capabilities, and heartbeats.

### Visual Layout

```
+------------------------------------------------------------------+
| HEADER                                                           |
+------------------------------------------------------------------+
| SIDEBAR |                                                        |
|         |  PAGE HEADER                                           |
|         |  +---------------------------------------------------+ |
|         |  | Agents Console                    [+ Register New] | |
|         |  | Monitor and manage agent instances                 | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  FILTER BAR                                            |
|         |  +---------------------------------------------------+ |
|         |  | [Search agents...    ] [Status ▼] [Type ▼] [Clear] | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  AGENT STATS (3 cards)                                 |
|         |  +---------------+ +---------------+ +---------------+ |
|         |  | TOTAL AGENTS  | | ACTIVE NOW    | | STALE (>5min) | |
|         |  |      [47]     | |      [42]     | |      [5]      | |
|         |  +---------------+ +---------------+ +---------------+ |
|         |                                                        |
|         |  AGENTS TABLE                                          |
|         |  +---------------------------------------------------+ |
|         |  | □ | Agent ID       | Type      | Status | Last HB | |
|         |  |---+----------------+-----------+--------+---------| |
|         |  | □ | agent_orch_001 | orchestr  | ● act  | 2s ago  | |
|         |  | □ | agent_work_014 | worker    | ● act  | 5s ago  | |
|         |  | □ | agent_work_015 | worker    | ● act  | 8s ago  | |
|         |  | □ | agent_orch_002 | orchestr  | ○ idle | 45s ago | |
|         |  | □ | agent_work_003 | worker    | ◐ stale| 6m ago  | |
|         |  |---+----------------+-----------+--------+---------| |
|         |  | [◀ Prev] Page 1 of 5 [Next ▶] | [10|25|50] per pg | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  BULK ACTIONS (when selected)                          |
|         |  +---------------------------------------------------+ |
|         |  | 3 agents selected: [Deregister] [Send Message]    | |
|         |  +---------------------------------------------------+ |
+------------------------------------------------------------------+
```

### Agent Detail Drawer (slides from right)

```
+----------------------------------------+
| AGENT DETAIL                      [X] |
+----------------------------------------+
| Agent ID: agent_orch_001              |
| Type: orchestrator                     |
| Status: ● Active                       |
| Registered: 2025-12-13 10:00:00 UTC   |
| Last Heartbeat: 2s ago                |
+----------------------------------------+
| CAPABILITIES                           |
| ├─ agent_spawn (5 credits)            |
| ├─ agent_invoke (10 credits)          |
| ├─ blackboard_read (1 credit)         |
| ├─ blackboard_write (1 credit)        |
| └─ blackboard_lock (1 credit)         |
+----------------------------------------+
| CURRENT JOBS                           |
| • job_a1b2c3d4 (running)              |
| • job_e5f6g7h8 (pending)              |
+----------------------------------------+
| ACTIONS                                |
| [Send Message] [Deregister] [View Logs]|
+----------------------------------------+
```

### Components Used
- `<PageHeader title subtitle actions />`
- `<FilterBar filters={filterConfig} onFilter={handleFilter} />`
- `<StatCard title value variant />`
- `<AgentsTable agents={agents} onSelect={handleSelect} />`
- `<BulkActionBar selected={selected} actions={actions} />`
- `<AgentDetailDrawer agent={selectedAgent} open={drawerOpen} />`
- `<Pagination page={page} total={total} pageSize={pageSize} />`

### Interactions
- Click row → Open detail drawer
- Checkbox → Select for bulk actions
- Search → Filter agents by ID/type
- Status filter → Show only matching status
- "Register New" → Opens registration modal

### API Integration
```typescript
// Fetch agents
GET /api/v1/agents?status=active&type=worker&page=1&limit=25

// Register agent
POST /api/v1/agents/register
{ agent_name: string, agent_type: string, capabilities: string[] }

// Deregister agent
DELETE /api/v1/agents/{agent_id}

// Send heartbeat
POST /api/v1/agents/{agent_id}/heartbeat
```

---

## Page 3: Job Simulator

**URL:** `https://agenticverz.com/console/jobs/simulate`

### Purpose
Pre-execution simulation for jobs. Estimate credits, duration, and identify potential issues before running.

### Visual Layout

```
+------------------------------------------------------------------+
| HEADER                                                           |
+------------------------------------------------------------------+
| SIDEBAR |                                                        |
|         |  PAGE HEADER                                           |
|         |  +---------------------------------------------------+ |
|         |  | Job Simulator                                      | |
|         |  | Test your job configuration before execution       | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  +---------------------------+ +---------------------+ |
|         |  | CONFIGURATION PANEL       | | SIMULATION RESULTS  | |
|         |  +---------------------------+ +---------------------+ |
|         |  |                           | |                     | |
|         |  | Orchestrator Agent        | | FEASIBILITY         | |
|         |  | [Select agent...     ▼]  | | +------------------+| |
|         |  |                           | | | ✓ FEASIBLE       || |
|         |  | Worker Agent              | | | Can execute      || |
|         |  | [Select agent...     ▼]  | | +------------------+| |
|         |  |                           | |                     | |
|         |  | Task Description          | | COST ESTIMATE       | |
|         |  | +------------------------+| | +------------------+| |
|         |  | | Process customer data  || | | Credits: 205.00  || |
|         |  | | from uploaded CSV and  || | | Breakdown:       || |
|         |  | | generate reports...    || | | • Reserve: 50.00 || |
|         |  | +------------------------+| | | • Items: 100.00  || |
|         |  |                           | | | • Skills: 55.00  || |
|         |  | Items (JSON Array)        | | +------------------+| |
|         |  | +------------------------+| |                     | |
|         |  | | [                      || | TIME ESTIMATE       | |
|         |  | |   {"id": 1, "n": 10}, || | +------------------+| |
|         |  | |   {"id": 2, "n": 20}, || | | Duration: ~10min || |
|         |  | |   {"id": 3, "n": 15}  || | | P50: 8min        || |
|         |  | | ]                      || | | P95: 15min       || |
|         |  | +------------------------+| | +------------------+| |
|         |  |                           | |                     | |
|         |  | Parallelism               | | BUDGET CHECK        | |
|         |  | [====○====] 5             | | +------------------+| |
|         |  |                           | | | Balance: 9,847   || |
|         |  | Max Retries               | | | Required: 205    || |
|         |  | [1] [2] [●3] [4] [5]      | | | ✓ Sufficient     || |
|         |  |                           | | +------------------+| |
|         |  | +------------------------+| |                     | |
|         |  | | [Simulate] [Clear]     || | WARNINGS            | |
|         |  | +------------------------+| | +------------------+| |
|         |  |                           | | | ⚠ High parallel  || |
|         |  +---------------------------+ | |   may cause rate || |
|         |                                | |   limiting       || |
|         |                                | +------------------+| |
|         |                                |                     | |
|         |                                | [Run This Job →]    | |
|         |                                +---------------------+ |
+------------------------------------------------------------------+
```

### Components Used
- `<ConfigPanel>`
  - `<AgentSelect agents={orchestrators} label="Orchestrator" />`
  - `<AgentSelect agents={workers} label="Worker" />`
  - `<TextArea name="task" rows={4} />`
  - `<JsonEditor name="items" schema={itemsSchema} />`
  - `<Slider name="parallelism" min={1} max={20} />`
  - `<SegmentedControl name="maxRetries" options={[1,2,3,4,5]} />`
- `<SimulationResults>`
  - `<FeasibilityBadge feasible={result.feasible} />`
  - `<CostBreakdown costs={result.estimated_credits} />`
  - `<TimeEstimate duration={result.estimated_duration_seconds} />`
  - `<BudgetCheck balance={balance} required={required} />`
  - `<WarningsList warnings={result.warnings} />`
  - `<RisksList risks={result.risks} />`

### Interactions
- Fill form → Enable "Simulate" button
- Click "Simulate" → POST to /api/v1/jobs/simulate
- Results appear in right panel with animation
- "Run This Job" → Navigate to Job Runner with pre-filled config
- "Clear" → Reset form and results

### API Integration
```typescript
POST /api/v1/jobs/simulate
{
  orchestrator_agent: string,
  worker_agent: string,
  task: string,
  items: Array<{ id: string, [key: string]: any }>,
  parallelism: number,
  max_retries: number
}

Response:
{
  feasible: boolean,
  estimated_credits: number,
  estimated_duration_seconds: number,
  budget_check: { sufficient: boolean, balance: number, required: number },
  warnings: string[],
  risks: string[]
}
```

---

## Page 4: Job Runner

**URL:** `https://agenticverz.com/console/jobs/run`

### Purpose
Create and execute parallel jobs, monitor real-time progress, and manage job lifecycle.

### Visual Layout

```
+------------------------------------------------------------------+
| HEADER                                                           |
+------------------------------------------------------------------+
| SIDEBAR |                                                        |
|         |  PAGE HEADER                                           |
|         |  +---------------------------------------------------+ |
|         |  | Job Runner                         [Simulate First]| |
|         |  | Create and monitor parallel job execution          | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  TABS: [Create New] [Active Jobs] [History]            |
|         |                                                        |
|         |  ===== CREATE NEW TAB =====                            |
|         |  +---------------------------------------------------+ |
|         |  | JOB CONFIGURATION                                  | |
|         |  +---------------------------------------------------+ |
|         |  | Orchestrator: [agent_orch_001 ▼]                   | |
|         |  | Worker: [agent_worker_pool ▼]                      | |
|         |  | Task: [Process batch data...               ]      | |
|         |  | Items: [Upload JSON] or [Paste JSON]               | |
|         |  | +------------------------------------------------+ | |
|         |  | | { "items": [{"id": 1}, {"id": 2}, ...] }       | | |
|         |  | +------------------------------------------------+ | |
|         |  | Parallelism: [====●====] 10                        | |
|         |  | Credit Reserve: 500.00 (auto-calculated)           | |
|         |  |                                                    | |
|         |  | [← Back to Simulate] [Create Job]                  | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  ===== ACTIVE JOBS TAB =====                           |
|         |  +---------------------------------------------------+ |
|         |  | job_a1b2c3d4                           [● RUNNING] | |
|         |  +---------------------------------------------------+ |
|         |  | Progress: [████████████░░░░░░░░] 60% (30/50)       | |
|         |  | Started: 2025-12-13 14:00:00 | Elapsed: 5m 32s    | |
|         |  | Credits Used: 120.00 / 250.00 reserved            | |
|         |  |                                                    | |
|         |  | ITEM STATUS                                        | |
|         |  | ✓ Completed: 28  ● Processing: 2  ○ Pending: 18  | |
|         |  | ✗ Failed: 2                                       | |
|         |  |                                                    | |
|         |  | LIVE FEED                                          | |
|         |  | 14:05:32 Item item_029 completed (worker_014)     | |
|         |  | 14:05:30 Item item_028 completed (worker_015)     | |
|         |  | 14:05:28 Item item_030 claimed by worker_014      | |
|         |  | 14:05:27 Item item_027 completed (worker_016)     | |
|         |  |                                                    | |
|         |  | [Cancel Job] [View Details]                        | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  +---------------------------------------------------+ |
|         |  | job_e5f6g7h8                           [○ PENDING] | |
|         |  +---------------------------------------------------+ |
|         |  | Items: 100 | Parallelism: 5 | Reserved: 500.00    | |
|         |  | Queued at: 2025-12-13 14:05:00                    | |
|         |  | [Start Now] [Cancel]                               | |
|         |  +---------------------------------------------------+ |
+------------------------------------------------------------------+
```

### Job Detail Modal

```
+----------------------------------------------------------+
| JOB DETAIL: job_a1b2c3d4                            [X]  |
+----------------------------------------------------------+
| Status: ● RUNNING                                         |
| Created: 2025-12-13 14:00:00 UTC                         |
| Orchestrator: agent_orch_001                              |
| Worker: agent_worker_pool                                 |
| Task: Process batch data for customer segmentation       |
+----------------------------------------------------------+
| PROGRESS                                                  |
| [████████████████░░░░░░░░░░░░░░] 60%                     |
| Completed: 30 | Processing: 2 | Pending: 15 | Failed: 3  |
+----------------------------------------------------------+
| CREDITS                                                   |
| Reserved: 250.00 | Spent: 120.00 | Remaining: 130.00     |
+----------------------------------------------------------+
| ITEMS TABLE                                               |
| +------------------------------------------------------+ |
| | Item ID  | Status     | Worker       | Duration     | |
| |----------+------------+--------------+--------------| |
| | item_001 | ✓ complete | worker_014   | 2.3s         | |
| | item_002 | ✓ complete | worker_015   | 1.8s         | |
| | item_003 | ✗ failed   | worker_016   | 0.5s (err)   | |
| | item_004 | ● process  | worker_014   | ...          | |
| | item_005 | ○ pending  | —            | —            | |
| +------------------------------------------------------+ |
| [Show All 50 Items]                                      |
+----------------------------------------------------------+
| [Cancel Job] [Export Results] [View Logs]                |
+----------------------------------------------------------+
```

### Components Used
- `<TabGroup tabs={['Create New', 'Active Jobs', 'History']} />`
- `<JobConfigForm onSubmit={createJob} />`
- `<ActiveJobCard job={job}>`
  - `<ProgressBar value={progress} max={total} />`
  - `<ItemStatusSummary counts={statusCounts} />`
  - `<LiveFeed events={jobEvents} />`
- `<JobDetailModal job={selectedJob} />`
- `<ItemsTable items={jobItems} />`

### Real-time Updates
- WebSocket connection for live job updates
- Progress bar animates in real-time
- Live feed shows item completions/failures
- Status badges update automatically

### API Integration
```typescript
// Create job
POST /api/v1/jobs
{
  orchestrator_agent: string,
  worker_agent: string,
  task: string,
  items: Array<object>,
  parallelism: number
}

// Get job status
GET /api/v1/jobs/{job_id}

// Cancel job
POST /api/v1/jobs/{job_id}/cancel

// WebSocket for real-time updates
WS wss://agenticverz.com/ws/jobs/{job_id}
```

---

## Page 5: Blackboard Explorer

**URL:** `https://agenticverz.com/console/blackboard`

### Purpose
Browse, search, and manage Redis blackboard key-value storage used for agent coordination.

### Visual Layout

```
+------------------------------------------------------------------+
| HEADER                                                           |
+------------------------------------------------------------------+
| SIDEBAR |                                                        |
|         |  PAGE HEADER                                           |
|         |  +---------------------------------------------------+ |
|         |  | Blackboard Explorer                    [+ Add Key] | |
|         |  | Shared state storage for agent coordination        | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  SEARCH & FILTER                                       |
|         |  +---------------------------------------------------+ |
|         |  | [Search keys...        ] [Pattern: job_* ▼] [🔍]  | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  STATS ROW                                             |
|         |  +-------------+ +-------------+ +-------------+       |
|         |  | TOTAL KEYS  | | WITH LOCKS  | | EXPIRING    |       |
|         |  |    [847]    | |    [12]     | |  [34] <1hr  |       |
|         |  +-------------+ +-------------+ +-------------+       |
|         |                                                        |
|         |  KEY-VALUE TABLE                                       |
|         |  +---------------------------------------------------+ |
|         |  | Key                | Value      | TTL    | Lock   | |
|         |  |--------------------+------------+--------+--------| |
|         |  | job_a1b2:counter   | 47         | 2h 30m | —      | |
|         |  | job_a1b2:status    | "running"  | 2h 30m | —      | |
|         |  | job_a1b2:lock_proc | {"owner":} | 5m     | 🔒     | |
|         |  | job_c3d4:counter   | 102        | 1h 15m | —      | |
|         |  | shared:rate_limit  | 45         | ∞      | —      | |
|         |  |--------------------+------------+--------+--------| |
|         |  | [◀] Page 1 of 17 [▶]                    [25 ▼]    | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  KEY DETAIL PANEL (when selected)                      |
|         |  +---------------------------------------------------+ |
|         |  | Key: job_a1b2:counter                              | |
|         |  | Type: Integer                                      | |
|         |  | Value: 47                                          | |
|         |  | TTL: 2 hours 30 minutes                           | |
|         |  | Created: 2025-12-13 12:00:00 UTC                  | |
|         |  | Last Modified: 2025-12-13 14:05:32 UTC            | |
|         |  |                                                    | |
|         |  | HISTORY (last 10 changes)                         | |
|         |  | 14:05:32 → 47 (increment +1)                      | |
|         |  | 14:05:30 → 46 (increment +1)                      | |
|         |  | 14:05:28 → 45 (increment +1)                      | |
|         |  |                                                    | |
|         |  | [Edit] [Increment] [Delete] [Refresh]             | |
|         |  +---------------------------------------------------+ |
+------------------------------------------------------------------+
```

### Add/Edit Key Modal

```
+------------------------------------------+
| ADD NEW KEY                         [X] |
+------------------------------------------+
| Key Name                                 |
| [job_xyz:my_counter                   ] |
|                                          |
| Value Type                               |
| (●) String  ( ) Integer  ( ) JSON       |
|                                          |
| Value                                    |
| [initial_value                        ] |
|                                          |
| TTL (Time to Live)                      |
| [  3600  ] seconds  □ No expiration     |
|                                          |
| [Cancel] [Save Key]                      |
+------------------------------------------+
```

### Components Used
- `<SearchBar placeholder="Search keys..." onSearch={handleSearch} />`
- `<PatternSelect patterns={['job_*', 'shared:*', 'lock:*']} />`
- `<StatCard title value />`
- `<KeyValueTable data={keys} onSelect={handleSelect} />`
- `<KeyDetailPanel selectedKey={key}>`
  - `<KeyMetadata key={key} />`
  - `<ValueEditor value={key.value} type={key.type} />`
  - `<KeyHistory history={keyHistory} />`
- `<AddKeyModal open={addOpen} onSave={handleSave} />`

### Interactions
- Click row → Show detail panel
- Search → Filter by key pattern
- "Add Key" → Open modal
- "Increment" → Atomic increment (for integer keys)
- "Delete" → Confirm and delete key
- Real-time TTL countdown display

### API Integration
```typescript
// List keys (with pattern)
GET /api/v1/blackboard?pattern=job_*&page=1&limit=25

// Read key
GET /api/v1/blackboard/{key}

// Write key
PUT /api/v1/blackboard/{key}
{ value: any, ttl_seconds?: number }

// Increment
POST /api/v1/blackboard/{key}/increment
{ amount: number }

// Delete key
DELETE /api/v1/blackboard/{key}
```

---

## Page 6: Messaging Inspector

**URL:** `https://agenticverz.com/console/messages`

### Purpose
Monitor agent-to-agent P2P messaging, message status, and delivery latency.

### Visual Layout

```
+------------------------------------------------------------------+
| HEADER                                                           |
+------------------------------------------------------------------+
| SIDEBAR |                                                        |
|         |  PAGE HEADER                                           |
|         |  +---------------------------------------------------+ |
|         |  | Messaging Inspector                 [+ Send Message]| |
|         |  | Monitor P2P communication between agents           | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  FILTER BAR                                            |
|         |  +---------------------------------------------------+ |
|         |  | From: [All ▼] To: [All ▼] Status: [All ▼] [Search]| |
|         |  | Time Range: [Last 1 hour ▼]         [Apply Filter]| |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  LATENCY STATS                                         |
|         |  +-------------+ +-------------+ +-------------+       |
|         |  | P50 LATENCY | | P95 LATENCY | | P99 LATENCY |       |
|         |  |   [45ms]    | |   [120ms]   | |   [450ms]   |       |
|         |  +-------------+ +-------------+ +-------------+       |
|         |                                                        |
|         |  MESSAGE FLOW VISUALIZATION                            |
|         |  +---------------------------------------------------+ |
|         |  |  agent_001 ──────────────────► agent_002          | |
|         |  |      │                              │              | |
|         |  |      │    ┌─────────────────┐      │              | |
|         |  |      └───►│   agent_003    │◄─────┘              | |
|         |  |           └─────────────────┘                      | |
|         |  |                   │                                | |
|         |  |                   ▼                                | |
|         |  |            agent_004                               | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  MESSAGES TABLE                                        |
|         |  +---------------------------------------------------+ |
|         |  | Time     | From → To        | Type    | Status   | |
|         |  |----------+------------------+---------+----------| |
|         |  | 14:05:32 | orch_01→work_14  | invoke  | ● deliv  | |
|         |  | 14:05:30 | work_14→orch_01  | response| ● deliv  | |
|         |  | 14:05:28 | orch_01→work_15  | invoke  | ◐ pend   | |
|         |  | 14:05:25 | work_15→orch_01  | response| ● deliv  | |
|         |  +---------------------------------------------------+ |
+------------------------------------------------------------------+
```

### Message Detail Drawer

```
+----------------------------------------+
| MESSAGE DETAIL                    [X] |
+----------------------------------------+
| Message ID: msg_a1b2c3d4e5f6          |
| Type: invoke                           |
| Status: ● Delivered                    |
+----------------------------------------+
| ROUTING                                |
| From: agent_orch_001                   |
| To: agent_worker_014                   |
| Sent: 2025-12-13 14:05:32.123 UTC     |
| Delivered: 2025-12-13 14:05:32.168 UTC|
| Latency: 45ms                          |
+----------------------------------------+
| PAYLOAD                                |
| {                                      |
|   "invoke_id": "inv_xyz",             |
|   "action": "process_item",           |
|   "data": {                           |
|     "item_id": "item_029",            |
|     "params": {...}                   |
|   }                                    |
| }                                      |
+----------------------------------------+
| RESPONSE (if applicable)              |
| {                                      |
|   "status": "success",                |
|   "result": {...}                     |
| }                                      |
+----------------------------------------+
```

### Components Used
- `<FilterBar>`
  - `<AgentSelect name="from" />`
  - `<AgentSelect name="to" />`
  - `<StatusSelect options={['pending', 'delivered', 'read']} />`
  - `<TimeRangeSelect options={['1h', '6h', '24h', '7d']} />`
- `<LatencyStatsRow p50={p50} p95={p95} p99={p99} />`
- `<MessageFlowGraph agents={agents} messages={messages} />`
- `<MessagesTable messages={messages} onSelect={handleSelect} />`
- `<MessageDetailDrawer message={selectedMessage} />`

### Real-time Features
- Live message stream via WebSocket
- NOTIFY-based instant updates
- Latency histogram updates every 5 seconds

### API Integration
```typescript
// List messages
GET /api/v1/messages?from={agent_id}&to={agent_id}&status=delivered&limit=50

// Get agent inbox
GET /api/v1/agents/{agent_id}/messages

// Send message
POST /api/v1/agents/{agent_id}/messages
{ type: string, payload: object }

// WebSocket for live messages
WS wss://agenticverz.com/ws/messages
```

---

## Page 7: Credit & Audit Console

**URL:** `https://agenticverz.com/console/credits`

### Purpose
Monitor credit balance, view transaction ledger, and audit invoke history.

### Visual Layout

```
+------------------------------------------------------------------+
| HEADER                                                           |
+------------------------------------------------------------------+
| SIDEBAR |                                                        |
|         |  PAGE HEADER                                           |
|         |  +---------------------------------------------------+ |
|         |  | Credit & Audit Console              [+ Add Credits]| |
|         |  | Track spending and audit agent activity            | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  BALANCE OVERVIEW                                      |
|         |  +---------------------------------------------------+ |
|         |  |                                                    | |
|         |  |  CURRENT BALANCE                    MONTHLY SPEND  | |
|         |  |  ╔═══════════════╗                  ╔════════════╗ | |
|         |  |  ║   9,847.50   ║                  ║  3,152.50  ║ | |
|         |  |  ║   credits     ║                  ║  this month ║ | |
|         |  |  ╚═══════════════╝                  ╚════════════╝ | |
|         |  |                                                    | |
|         |  |  Reserved: 1,200.00 | Available: 8,647.50         | |
|         |  |                                                    | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  TABS: [Ledger] [Invoke Audit] [Usage Analytics]       |
|         |                                                        |
|         |  ===== LEDGER TAB =====                                |
|         |  +---------------------------------------------------+ |
|         |  | Time     | Type      | Amount   | Balance | Job   | |
|         |  |----------+-----------+----------+---------+-------| |
|         |  | 14:05:32 | charge    | -10.00   | 9847.50 | job_x | |
|         |  | 14:05:30 | charge    | -10.00   | 9857.50 | job_x | |
|         |  | 14:05:00 | reserve   | -500.00  | 9867.50 | job_y | |
|         |  | 14:00:00 | refund    | +150.00  | 10367.5 | job_z | |
|         |  | 13:55:00 | topup     | +1000.00 | 10217.5 | —     | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  ===== INVOKE AUDIT TAB =====                          |
|         |  +---------------------------------------------------+ |
|         |  | Invoke ID  | Caller→Target | Duration | Credits  | |
|         |  |------------+---------------+----------+----------| |
|         |  | inv_a1b2c3 | orch→work_14  | 964ms    | 10.00    | |
|         |  | inv_d4e5f6 | orch→work_15  | 1.2s     | 10.00    | |
|         |  | inv_g7h8i9 | work→orch     | 45ms     | 10.00    | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  ===== USAGE ANALYTICS TAB =====                       |
|         |  +---------------------------------------------------+ |
|         |  |  CREDIT USAGE (30 days)                           | |
|         |  |  ┌────────────────────────────────────────────┐   | |
|         |  |  │▄   ▄▄  ▄▄▄ ▄▄  █▄ ██▄███████████▄▄▄▄▄    │   | |
|         |  |  └────────────────────────────────────────────┘   | |
|         |  |                                                    | |
|         |  |  BY SKILL              BY JOB TYPE                 | |
|         |  |  ┌──────────┐          ┌──────────┐               | |
|         |  |  │ invoke   │ 45%      │ batch    │ 60%           | |
|         |  |  │ spawn    │ 30%      │ realtime │ 25%           | |
|         |  |  │ bb_write │ 15%      │ adhoc    │ 15%           | |
|         |  |  │ other    │ 10%      └──────────┘               | |
|         |  |  └──────────┘                                      | |
|         |  +---------------------------------------------------+ |
+------------------------------------------------------------------+
```

### Components Used
- `<BalanceCard balance={balance} reserved={reserved} />`
- `<MonthlySpendCard amount={monthlySpend} />`
- `<TabGroup tabs={['Ledger', 'Invoke Audit', 'Usage Analytics']} />`
- `<LedgerTable entries={ledgerEntries} />`
- `<InvokeAuditTable audits={invokeAudits} />`
- `<UsageChart data={usageData} days={30} />`
- `<SkillBreakdownPie data={skillUsage} />`
- `<JobTypeBreakdownPie data={jobTypeUsage} />`

### Interactions
- Click ledger entry → Show transaction detail
- Click invoke → Show invoke detail with timeline
- Export ledger → Download CSV
- Filter by date range, type, job_id

### API Integration
```typescript
// Get balance
GET /api/v1/credits/balance

// Get ledger entries
GET /api/v1/credits/ledger?page=1&limit=50&type=charge

// Get invoke audit trail
GET /api/v1/invocations/audit?caller={agent_id}&page=1&limit=50

// Add credits (admin)
POST /api/v1/credits/topup
{ amount: number, note: string }
```

---

## Page 8: Metrics Overview

**URL:** `https://agenticverz.com/console/metrics`

### Purpose
Visualize system metrics, Prometheus data, and operational health dashboards.

### Visual Layout

```
+------------------------------------------------------------------+
| HEADER                                                           |
+------------------------------------------------------------------+
| SIDEBAR |                                                        |
|         |  PAGE HEADER                                           |
|         |  +---------------------------------------------------+ |
|         |  | Metrics Overview                     [⚙ Configure] | |
|         |  | System health and performance monitoring           | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  TIME RANGE SELECTOR                                   |
|         |  +---------------------------------------------------+ |
|         |  | [15m] [1h] [6h] [24h] [7d] | Custom: [__|__] - [__]| |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  HEALTH STATUS                                         |
|         |  +------------+ +------------+ +------------+ +------+ |
|         |  | API SERVER | | DATABASE   | | REDIS      | |WORKERS|
|         |  | ● Healthy  | | ● Healthy  | | ● Healthy  | |●42/45 |
|         |  | 99.9% up   | | 15ms p95   | | 2ms p95    | |3 stale|
|         |  +------------+ +------------+ +------------+ +------+ |
|         |                                                        |
|         |  JOBS METRICS                                          |
|         |  +---------------------------------------------------+ |
|         |  | Jobs Created / Completed / Failed (24h)           | |
|         |  | ┌──────────────────────────────────────────────┐  | |
|         |  | │  ─── created  ─── completed  ─── failed      │  | |
|         |  | │      ╱╲        ╱╲                             │  | |
|         |  | │     ╱  ╲      ╱  ╲    ╱╲                     │  | |
|         |  | │    ╱    ╲    ╱    ╲  ╱  ╲                   │  | |
|         |  | │ ──╱──────╲──╱──────╲╱────╲─────────────────  │  | |
|         |  | └──────────────────────────────────────────────┘  | |
|         |  +---------------------------------------------------+ |
|         |                                                        |
|         |  +---------------------------+ +---------------------+ |
|         |  | ITEMS THROUGHPUT          | | CREDIT FLOW         | |
|         |  +---------------------------+ +---------------------+ |
|         |  | ┌───────────────────────┐ | | Reserved: 12,500    | |
|         |  | │ 847 items/hour avg    │ | | Spent: 8,234        | |
|         |  | │ Peak: 1,234 items/hr  │ | | Refunded: 1,156     | |
|         |  | └───────────────────────┘ | | Net: 7,078          | |
|         |  +---------------------------+ +---------------------+ |
|         |                                                        |
|         |  +---------------------------+ +---------------------+ |
|         |  | INVOKE LATENCY (P95)      | | MESSAGE LATENCY     | |
|         |  +---------------------------+ +---------------------+ |
|         |  | ┌───────────────────────┐ | | ┌─────────────────┐ | |
|         |  | │         ▄▄▄▄▄▄       │ | | │     ▄▄▄▄       │ | |
|         |  | │        ▄██████▄      │ | | │    ▄████▄      │ | |
|         |  | │       ▄████████▄     │ | | │   ▄██████▄     │ | |
|         |  | │ ▄▄▄▄▄████████████▄▄▄▄│ | | │ ▄▄████████▄▄▄▄ │ | |
|         |  | └───────────────────────┘ | | └─────────────────┘ | |
|         |  | Current: 1.2s | Avg: 0.9s | | P50: 45ms P95: 120ms| |
|         |  +---------------------------+ +---------------------+ |
+------------------------------------------------------------------+
```

### Components Used
- `<TimeRangeSelector range={range} onSelect={handleSelect} />`
- `<HealthStatusCard service="api" status={apiHealth} />`
- `<MetricLineChart metrics={['created', 'completed', 'failed']} />`
- `<ThroughputGauge current={throughput} peak={peakThroughput} />`
- `<CreditFlowSummary reserved={reserved} spent={spent} refunded={refunded} />`
- `<LatencyHistogram data={latencyData} percentiles={[50, 95, 99]} />`

### Prometheus Metrics Displayed
```
m12_jobs_created_total
m12_jobs_completed_total
m12_jobs_failed_total
m12_items_claimed_total
m12_items_completed_total
m12_credits_reserved_total
m12_credits_spent_total
m12_credits_refunded_total
m12_invoke_duration_seconds
m12_message_latency_seconds
```

### API Integration
```typescript
// Get metrics summary
GET /api/v1/metrics/summary?range=24h

// Prometheus query proxy
GET /api/v1/metrics/query?query=m12_jobs_created_total&start={}&end={}

// Get health status
GET /health
```

---

## Page 9: Login Page

**URL:** `https://agenticverz.com/console/login`

### Purpose
Secure authentication entry point for AOS Console.

### Visual Layout

```
+------------------------------------------------------------------+
|                                                                  |
|                                                                  |
|                    ╔═══════════════════════════╗                 |
|                    ║                           ║                 |
|                    ║      [AOS Logo]           ║                 |
|                    ║                           ║                 |
|                    ║   Agentic Operating       ║                 |
|                    ║        System             ║                 |
|                    ║                           ║                 |
|                    ╠═══════════════════════════╣                 |
|                    ║                           ║                 |
|                    ║   Email                   ║                 |
|                    ║   [                    ]  ║                 |
|                    ║                           ║                 |
|                    ║   Password                ║                 |
|                    ║   [                    ]  ║                 |
|                    ║                           ║                 |
|                    ║   □ Remember me           ║                 |
|                    ║                           ║                 |
|                    ║   [     Sign In      ]    ║                 |
|                    ║                           ║                 |
|                    ║   ─────── or ───────      ║                 |
|                    ║                           ║                 |
|                    ║   [🔐 Sign in with SSO]   ║                 |
|                    ║                           ║                 |
|                    ║   [Forgot password?]      ║                 |
|                    ║                           ║                 |
|                    ╚═══════════════════════════╝                 |
|                                                                  |
|                    Don't have an account?                        |
|                    [Request Access]                              |
|                                                                  |
|                    ─────────────────────                         |
|                    © 2025 Agenticverz                            |
|                    [Privacy] [Terms]                             |
|                                                                  |
+------------------------------------------------------------------+
```

### Components Used
- `<Logo size="large" />`
- `<Input type="email" name="email" label="Email" />`
- `<Input type="password" name="password" label="Password" />`
- `<Checkbox name="remember" label="Remember me" />`
- `<Button variant="primary" fullWidth>Sign In</Button>`
- `<Divider text="or" />`
- `<SSOButton provider="enterprise" />`
- `<Link href="/forgot-password">Forgot password?</Link>`
- `<Link href="/request-access">Request Access</Link>`

### Authentication Flow
1. User enters credentials
2. POST to /api/v1/auth/login
3. Receive JWT token + refresh token
4. Store in httpOnly cookies
5. Redirect to /console/

### API Integration
```typescript
// Login
POST /api/v1/auth/login
{ email: string, password: string, remember: boolean }

// SSO redirect
GET /api/v1/auth/sso/redirect?provider=enterprise

// Token refresh
POST /api/v1/auth/refresh
```

---

## Page 10: Global Navigation & Header

**Component:** Persistent across all pages

### Header Layout

```
+------------------------------------------------------------------+
| [AOS]  Dashboard  Agents  Jobs ▼  Blackboard  Messages  Credits  |
|                                                                  |
|                          [🔔 3] [Credits: 9,847] [👤 Admin ▼]    |
+------------------------------------------------------------------+

Jobs Dropdown:
+------------------+
| Simulator        |
| Runner           |
| History          |
+------------------+

User Dropdown:
+------------------+
| Profile          |
| Settings         |
| API Keys         |
| ──────────────── |
| Documentation    |
| Support          |
| ──────────────── |
| Sign Out         |
+------------------+
```

### Sidebar Layout (Collapsed on mobile)

```
+------------------+
| [≡] AOS Console  |
+------------------+
| ◉ Dashboard      |
| ○ Agents         |
| ○ Jobs           |
|   ├ Simulator    |
|   ├ Runner       |
|   └ History      |
| ○ Blackboard     |
| ○ Messages       |
| ○ Credits        |
| ○ Metrics        |
+------------------+
| TENANT           |
| [Production ▼]   |
+------------------+
| [⚙ Settings]     |
| [📖 Docs]        |
+------------------+
```

### Components Used
- `<Header>`
  - `<Logo />`
  - `<NavLinks items={navItems} />`
  - `<NotificationBell count={unreadCount} />`
  - `<CreditBadge balance={balance} />`
  - `<UserMenu user={currentUser} />`
- `<Sidebar collapsed={isMobile}>`
  - `<NavItem icon="dashboard" label="Dashboard" href="/" />`
  - `<NavItem icon="agents" label="Agents" href="/agents" />`
  - `<NavGroup label="Jobs" items={jobsItems} />`
  - `<TenantSelector tenants={tenants} current={currentTenant} />`
- `<StatusBar>`
  - `<ServiceStatus services={healthStatus} />`
  - `<VersionBadge version={appVersion} />`
  - `<ClockDisplay timezone="UTC" />`

### Responsive Behavior
- **Desktop:** Full header + sidebar visible
- **Tablet:** Collapsed sidebar, hamburger toggle
- **Mobile:** Hidden sidebar, bottom nav, hamburger menu

---

## Responsive Breakpoints

| Breakpoint | Width | Layout Changes |
|------------|-------|----------------|
| Mobile | <768px | Bottom nav, stacked cards, hamburger menu |
| Tablet | 768-1200px | Collapsed sidebar, 2-column grid |
| Desktop | >1200px | Full sidebar, multi-column layouts |

---

## Accessibility Requirements

- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader labels on all interactive elements
- Focus indicators visible
- Color contrast ratio 4.5:1 minimum
- Skip navigation links
- ARIA landmarks and roles

---

## Animation Guidelines

- Page transitions: 200ms ease-out
- Modal/drawer: 300ms slide-in
- Button hover: 150ms
- Loading spinners: 1s rotation
- Progress bars: Smooth interpolation
- Real-time updates: Fade-in highlight

---

## Document Revision

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-13 | Initial wireframes for all 10 pages |
