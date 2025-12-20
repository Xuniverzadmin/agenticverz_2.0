# PIN-088: Worker Execution Console - Real-Time Split-Pane UI (Enhanced)

**Status:** COMPLETE
**Date:** 2024-12-16
**Milestone:** M20+
**Depends On:** PIN-087 (Business Builder Worker API Hosting)

---

## Overview

This PIN documents the implementation of the **Worker Execution Console**, a comprehensive real-time UI for monitoring and interacting with Workers. The console provides:

- **Worker Studio Home Page** - Landing page explaining workers and deterministic OS
- **5-Pane Execution Console** - Real-time monitoring with artifact preview
- **Multi-Worker Support** - Dropdown to switch between workers
- **Run History** - View and replay previous executions
- **Export Functionality** - Download traces as JSON, TXT, or CSV
- **Light/Dark Mode** - Full theme support
- **Real-Time Artifact Preview** - Watch generated content assemble live

## Architecture

### Worker Studio Structure

```
/workers                    → Worker Studio Home (landing page)
/workers/console           → Execution Console (5-pane UI)
/workers/console?worker=X  → Console with specific worker selected
/workers/console?replay=Y  → Console replaying run Y
```

### 5-Pane Layout

```
┌─────────────────────┬─────────────────────┬──────────────────────────┐
│  Execution Timeline │   Live Log Stream   │                          │
│     (Left-Top)      │   (Center-Top)      │    Artifact Preview      │
│                     │                     │     (Right - Full)       │
│  ○ Preflight  ✓     │  [INFO] Validating  │                          │
│  ◉ Research   ...   │  [DEBUG] CARE route │   ┌──────────────────┐   │
│  ○ Strategy         │  [WARN] Failure     │   │  landing.html    │   │
│  ○ Copy             │  [INFO] Recovery    │   │                  │   │
│  ○ UX               │                     │   │  LIVE PREVIEW    │   │
│  ○ Consistency      │                     │   │                  │   │
├─────────────────────┼─────────────────────┤   │  Watch content   │   │
│  Routing Dashboard  │ Failures & Recovery │   │  assemble in     │   │
│    (Left-Bottom)    │  (Center-Bottom)    │   │  real-time!      │   │
│                     │                     │   │                  │   │
│  Complexity: 45%    │  Event | Engine     │   └──────────────────┘   │
│  Drift: 12%         │  failure  M9        │                          │
│  Artifacts: 3       │  recovery M10       │   tabs: html | md | json │
│                     │  policy   M19       │                          │
└─────────────────────┴─────────────────────┴──────────────────────────┘
```

## Features

### 1. Worker Studio Home Page (`/workers`)

**Purpose:** Landing page that explains workers and provides quick access.

**Features:**
- Explains what workers are and why they're deterministic
- Shows available workers with status (available, coming_soon, beta)
- Displays moat badges for each worker (M9, M10, M15, M17, M18, M19, M20)
- Recent run history with replay buttons
- System health status
- Quick CTA to launch execution console

**Components:**
- `WorkerStudioHome.tsx` - Main landing page
- Feature cards explaining machine-native principles
- Worker cards with moat badges
- Recent runs list with status indicators

### 2. Multi-Worker Dropdown

**Location:** Top-left of execution console

**Features:**
- Dropdown showing all available workers
- Status badges (Available, Coming Soon, Beta)
- Description for each worker
- Disabled state for unavailable workers
- URL parameter support (`?worker=business-builder`)

**Workers Defined:**
| Worker | Status | Moats |
|--------|--------|-------|
| Business Builder | Available | M9, M10, M15, M17, M18, M19, M20 |
| Code Debugger | Coming Soon | M9, M10, M17, M19 |
| Repo Fixer | Coming Soon | M9, M10, M17, M18, M19 |

### 3. Run History Panel

**Location:** Top-right dropdown (History icon with badge)

**Features:**
- Shows last 10 runs
- Success/failure/pending status icons
- Task description (truncated)
- Execution time
- Click to replay
- Refresh button
- Timestamp

### 4. Replay Functionality

**Two modes:**

1. **History Replay:** Click run in history panel → loads run_id → streams events
2. **Token Replay:** Click "Replay" button after completion → uses M4 Golden Replay token

**Implementation:**
```typescript
// History replay (view previous run)
const handleReplay = (historyRunId: string) => {
  setRunId(historyRunId);
  setSearchParams({ worker: selectedWorker, replay: historyRunId });
};

// Token replay (re-execute deterministically)
const handleReplayWithToken = async () => {
  const response = await replayWorkerRun(state.replayToken);
  setRunId(response.run_id);
};
```

### 5. Export Trace

**Formats:**
- **JSON:** Full structured data with all events
- **TXT:** Human-readable formatted trace
- **CSV:** Log events in spreadsheet format

**Export includes:**
- Run ID, task, status
- All stages with timing
- All log events
- Routing decisions
- Policy events
- Drift events
- Recovery events
- Artifacts list
- Token/latency metrics
- Export timestamp

### 6. Real-Time Artifact Preview (CRITICAL)

**Purpose:** Creates the "wow moment" - users watch content being generated live.

**Component:** `ArtifactPreview.tsx`

**Features:**
- Tabs for each artifact (landing.html, positioning.md, etc.)
- Real-time content updates as artifacts are generated
- Preview modes:
  - HTML: Live iframe rendering
  - Markdown: Formatted prose
  - JSON: Syntax highlighted
  - Code: Syntax highlighted
- Source view toggle
- Copy to clipboard
- Download individual artifact
- Expand to full screen
- Character count
- Stage attribution

**Event Handling:**
```typescript
case 'artifact_created':
  // Store artifact metadata
  artifacts.push({ name, type, stage_id });

  // If content included, store for preview
  if (data.content) {
    artifactContents[`${name}.${type}`] = {
      name, type, content, stage_id, timestamp
    };
  }
```

### 7. Light/Dark Mode

**Implementation:**
- Toggle button in top-right (Sun/Moon icons)
- Persists via document.documentElement class toggle
- All components support `dark:` Tailwind variants
- Proper contrast ratios maintained

## Files Created/Modified

### New Files

```
website/aos-console/console/src/pages/workers/
├── WorkerStudioHome.tsx          # Landing page
├── WorkerExecutionConsole.tsx    # Enhanced 5-pane console
├── index.ts                      # Updated exports
└── components/
    ├── ArtifactPreview.tsx       # Real-time artifact viewer
    ├── ExecutionTimeline.tsx     # Stage progress
    ├── LiveLogStream.tsx         # Log viewer
    ├── RoutingDashboard.tsx      # CARE routing display
    ├── FailuresRecoveryPanel.tsx # M9/M10/M18/M19 events
    └── index.ts                  # Component exports
```

### Modified Files

```
website/aos-console/console/src/
├── types/worker.ts               # Added ArtifactContent, stream prop
├── hooks/useWorkerStream.ts      # Added artifactContents state
├── routes/index.tsx              # Added Worker Studio routes
└── components/layout/Sidebar.tsx # Already has Workers link
```

## Routes

| Route | Component | Purpose |
|-------|-----------|---------|
| `/workers` | WorkerStudioHome | Landing page |
| `/workers/console` | WorkerExecutionConsole | Execution UI |
| `/workers/console?worker=X` | WorkerExecutionConsole | With worker selected |
| `/workers/console?replay=Y` | WorkerExecutionConsole | Replaying run Y |
| `/workers/history` | WorkerStudioHome | Scrolls to history |

## Type Updates

```typescript
// Added to types/worker.ts
export interface ArtifactContent {
  name: string;
  type: string;
  content: string;
  stage_id: string;
  timestamp?: string;
}

export interface WorkerExecutionState {
  // ... existing fields
  artifactContents: Record<string, ArtifactContent>;
  replayToken?: Record<string, unknown>;
}

export interface WorkerDefinition {
  id: string;
  name: string;
  description: string;
  status: 'available' | 'coming_soon' | 'beta';
  moats: string[];
}

export interface RunHistoryItem {
  run_id: string;
  task: string;
  status: string;
  success: boolean | null;
  created_at: string;
  total_latency_ms: number | null;
  worker_id?: string;
}
```

## User Flow

1. **Discovery:** User visits `/workers` → sees landing page explaining workers
2. **Selection:** User clicks "Run Worker" on Business Builder card
3. **Configuration:** User enters task description, optionally configures brand JSON
4. **Execution:** User clicks "Run" → console connects to SSE stream
5. **Monitoring:** User watches:
   - Timeline progress (stages completing)
   - Live logs (agent output)
   - Routing decisions (CARE engine)
   - Failures/recoveries (M9/M10)
   - **Artifacts assembling in real-time** (wow moment)
6. **Completion:** Run finishes → user can:
   - Download artifacts
   - Export trace (JSON/TXT/CSV)
   - Replay execution (M4 Golden Replay)
   - Start new run

## Enterprise Features

- **Export Trace:** JSON/TXT/CSV for audit trails
- **Run History:** View and replay past executions
- **Deterministic Replay:** M4 Golden Replay via token
- **Dark Mode:** Professional appearance

## Future Enhancements

1. **PDF Export:** Add PDF format for formal reports
2. **Artifact Comparison:** Side-by-side diff of replayed artifacts
3. **Team Sharing:** Share run links with teammates
4. **Webhooks:** Notify on completion
5. **API Key Management:** Per-worker API keys

---

## References

- PIN-087: Business Builder Worker API Hosting
- PIN-086: Business Builder Worker v0.2 Architecture
- PIN-075: M17 CARE Routing Engine
- PIN-076: M18 CARE-L SBA Evolution
- PIN-078: M19 Policy Layer
- PIN-084: M20 Policy Compiler & Runtime
