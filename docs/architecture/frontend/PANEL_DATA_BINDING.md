# Panel Data Binding Architecture

**Status:** ACTIVE
**Created:** 2026-01-20
**Reference:** `PANEL_CREATION_PLAN.md`, `FRONTEND_PROJECTION_ARCHITECTURE.md`

---

## 1. Overview

Panels are **independent UI components** that display data based on their topic and O-level depth.

| Layer | Concern | Source |
|-------|---------|--------|
| **Panel Structure** | Which panels exist, where | V2 Constitution, ui_projection_lock.json |
| **Data Shape** | What shape data takes | O-level (O1-O5) |
| **Data Source** | Where data comes from | TBD (decoupled) |

**Current Focus:** Panel → Topic → Data Shape (binding deferred)

---

## 2. Panel to Topic Mapping

Panels are fixed to topics from the V2 Constitution:

```
Domain → Subdomain → Topic → Panel(s)
```

### 2.1 Panel Identity

Each panel is identified by:

| Field | Source | Example |
|-------|--------|---------|
| `panel_id` | ui_projection_lock.json | `ACT-LLM-LIVE` |
| `domain` | V2 Constitution | `Activity` |
| `subdomain` | V2 Constitution | `llm_runs` |
| `topic` | V2 Constitution | `live` |

### 2.2 Panel Metadata (from ui_projection_types.ts)

```typescript
interface Panel {
  panel_id: string;
  panel_name: string;
  topic: string | null;
  subdomain: string | null;

  // Display
  render_mode: RenderMode;    // FLAT | TREE | GRID | TABLE | CARD | LIST
  visibility: Visibility;
  enabled: boolean;
  short_description: string | null;

  // Structure
  controls: Control[];
  content_blocks: ContentBlock[];

  // Classification
  panel_class: PanelClass;    // execution | interpretation
  binding_status: BindingStatus;
}
```

---

## 3. Data Shape by O-Level

Each panel displays data according to its O-level depth.

### 3.1 O-Level Summary

| O-Level | Purpose | Data Shape | Component |
|---------|---------|------------|-----------|
| **O1** | Summary | Counts, status, metrics | Card, Metric |
| **O2** | List | Collection with pagination | Table, Grid |
| **O3** | Detail | Single entity, full info | DetailView |
| **O4** | Context | Relationships, timeline | Links, Timeline |
| **O5** | Evidence | Raw proof, traces | Code, Trace |

### 3.2 O1 — Summary Data

```typescript
interface O1Data {
  // Counts
  total: number;
  active?: number;

  // Status indicator
  status: 'healthy' | 'warning' | 'critical';

  // Metrics for display
  metrics?: Array<{
    label: string;
    value: number | string;
    trend?: 'up' | 'down' | 'flat';
  }>;

  // Timestamp
  as_of: string;
}
```

### 3.3 O2 — List Data

```typescript
interface O2Data<T> {
  items: T[];

  pagination: {
    total: number;
    page: number;
    page_size: number;
  };

  // Applied state
  filters_applied?: Record<string, string>;
  sort?: { field: string; direction: 'asc' | 'desc' };
}
```

### 3.4 O3 — Detail Data

```typescript
interface O3Data<T> {
  entity: T;

  // Available actions
  actions?: Array<{
    action: string;
    label: string;
    enabled: boolean;
  }>;
}
```

### 3.5 O4 — Context Data

```typescript
interface O4Data {
  source: { id: string; type: string };

  // Relationships
  related: Array<{
    id: string;
    type: string;
    title: string;
    link: string;
  }>;

  // Timeline
  timeline?: Array<{
    timestamp: string;
    event: string;
  }>;
}
```

### 3.6 O5 — Evidence Data

```typescript
interface O5Data {
  source: { id: string; type: string };

  // Raw data
  trace?: {
    trace_id: string;
    steps: Array<{
      step_number: number;
      timestamp: string;
      type: string;
    }>;
  };

  // Export options
  exports?: Array<{
    format: 'json' | 'csv';
    url: string;
  }>;
}
```

---

## 4. Panel Component Pattern

### 4.1 Component Structure

```typescript
// Each panel component receives:
interface PanelProps {
  panelId: string;
  topic: string;
  oLevel: 1 | 2 | 3 | 4 | 5;
}

// Panel fetches its own data based on topic + oLevel
function ActivityLivePanel({ panelId, topic, oLevel }: PanelProps) {
  const { data, isLoading } = usePanelData(topic, oLevel);

  if (isLoading) return <LoadingSkeleton />;

  // Render based on O-level
  switch (oLevel) {
    case 1: return <SummaryCard data={data} />;
    case 2: return <DataTable data={data} />;
    case 3: return <DetailView data={data} />;
    default: return <EmptyState />;
  }
}
```

### 4.2 Data Fetching (Decoupled)

```typescript
// Hook fetches data by topic + oLevel
// Actual endpoint resolution is abstracted
function usePanelData(topic: string, oLevel: number) {
  return useQuery({
    queryKey: ['panel', topic, oLevel],
    queryFn: () => fetchPanelData(topic, oLevel),
  });
}

// Endpoint mapping (simple for now)
function fetchPanelData(topic: string, oLevel: number) {
  const endpoint = getPanelEndpoint(topic, oLevel);
  return fetch(endpoint).then(r => r.json());
}
```

---

## 5. Panel Registration

### 5.1 PanelContentRegistry

```typescript
// src/components/panels/PanelContentRegistry.tsx
export const PANEL_COMPONENTS: Record<string, React.ComponentType<PanelProps>> = {
  // Activity domain
  'ACT-LLM-LIVE': ActivityLivePanel,
  'ACT-LLM-COMP': ActivityCompletedPanel,

  // Incidents domain
  'INC-EV-ACT': IncidentsActivePanel,
  'INC-EV-RES': IncidentsResolvedPanel,

  // ... more panels
};

export function renderPanel(panelId: string, props: PanelProps) {
  const Component = PANEL_COMPONENTS[panelId];
  if (!Component) {
    return <EmptyState message={`Panel ${panelId} not implemented`} />;
  }
  return <Component {...props} />;
}
```

---

## 6. What Changes by O-Level

| Aspect | O1 | O2 | O3 | O4 | O5 |
|--------|----|----|----|----|-----|
| **Data Shape** | Aggregates | Collections | Single Entity | Relations | Raw |
| **Controls** | Refresh | Filter, Sort, Page | Actions | Navigate | Export |
| **Component** | Card | Table/Grid | DetailView | Timeline | Code |
| **Pagination** | No | Yes | No | No | No |

---

## 7. File Locations

| File | Purpose |
|------|---------|
| `design/v2_constitution/ui_projection_lock.json` | Panel definitions |
| `src/contracts/ui_projection_types.ts` | TypeScript types |
| `src/contracts/ui_projection_loader.ts` | Load projection |
| `src/components/panels/PanelContentRegistry.tsx` | Panel → Component map |

---

## 8. Deferred Concerns

The following are **not part of this spec** (to be designed later):

| Concern | Status |
|---------|--------|
| Capability binding | Deferred |
| SDSR observation | Deferred |
| AURORA registry lookup | Deferred |
| Binding status enforcement | Deferred |

Panels should work with mock/static data first, then binding strategy decided based on how panels look and behave.
