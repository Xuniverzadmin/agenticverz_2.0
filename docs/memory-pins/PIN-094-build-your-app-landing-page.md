# PIN-094: Build Your App - Landing Page Feature

**Date:** 2025-12-16
**Status:** COMPLETE
**Category:** Frontend / Landing Page / User Experience

---

## Summary

Implemented a human-centric "Build Your App" feature on the Agenticverz landing page. This provides a public-facing interface for users to describe their product idea and have AI agents generate a comprehensive business plan.

---

## Motivation

- Provide a self-service entry point for potential customers
- Demonstrate AOS capabilities without requiring authentication
- Translate complex agent orchestration into user-friendly UI
- Hide OS internals - show agents as "workers" not system components

---

## Implementation

### New Files

| File | Purpose |
|------|---------|
| `website/landing/src/pages/build/BuildYourApp.jsx` | Main feature component (~700 lines) |
| `/opt/agenticverz/apps/site/dist/.htaccess` | SPA fallback routing for React Router |

### Modified Files

| File | Changes |
|------|---------|
| `website/landing/src/App.jsx` | Added React Router, `/build` route, nav button |
| `website/landing/package.json` | Added `react-router-dom` dependency |

---

## Feature Architecture

### 3-State Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   INPUT     │ ──► │    PLAN     │ ──► │  EXECUTION  │
│   INTENT    │     │   REVIEW    │     │    VIEW     │
└─────────────┘     └─────────────┘     └─────────────┘
```

### State 1: Input & Intent

Collects user input without overwhelming with technical options:

| Field | Type | Purpose |
|-------|------|---------|
| Idea Description | Textarea | Main product concept |
| Problem Statement | Textarea | Problem being solved |
| Reference Products | 2x Input | Competitive benchmarks |
| Primary Audience | Select | Target user segment |
| Analysis Depth | Radio | Quick/Balanced/Deep |
| Constraints | Checkboxes | Content policy toggles |

### State 2: Plan Review & Approval

Displays AI-generated plan with approval gates:

- **Execution Plan**: Steps with stage/phase breakdown
- **Cost Estimate**: Token/credit budget
- **Timeline**: Expected completion stages
- **Marketing Plan**: Generated positioning

### State 3: Execution View

Real-time execution monitoring:

- **Progress Indicator**: Overall completion %
- **Agent Workforce Pane**: Collapsible list of working agents
- **Execution Logs**: Timestamped activity feed
- **Artifacts**: Generated deliverables (downloadable)

---

## Human-Centric UI Principles

Per the "Human-Centric UI Schema v3":

| Principle | Implementation |
|-----------|----------------|
| **No OS jargon** | Agents shown as "Research Team", "Strategy Team" |
| **Simple inputs** | Dropdowns, checkboxes, not JSON configs |
| **Approval gates** | User must approve plan before execution |
| **Progress transparency** | Real-time logs without technical noise |
| **Clear outcomes** | Download artifacts, not "view run results" |

---

## Technical Details

### API Integration

```javascript
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : '';  // Relative URL for production (proxied by Apache)

// Endpoint
POST ${API_BASE}/api/v1/workers/business-builder/run
```

### Apache Proxy Configuration

```apache
# In agenticverz.com.conf
ProxyPass        /api/v1 http://127.0.0.1:8000/api/v1
ProxyPassReverse /api/v1 http://127.0.0.1:8000/api/v1
```

### SPA Routing (.htaccess)

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteCond %{REQUEST_URI} !^/api/
  RewriteCond %{REQUEST_URI} !^/console
  RewriteRule ^(.*)$ /index.html [L]
</IfModule>
```

---

## Debug Logger

Enhanced console logging for troubleshooting:

```javascript
// Visibility test on load
console.warn('%c🟣 BUILD-APP DEBUG MODE ACTIVE 🟣',
  'background: #8b5cf6; color: white; font-size: 16px;');

// Component mount
console.warn('%c🚀 BuildYourApp MOUNTED',
  'background: #10b981; color: white;');

// API calls logged with console.warn for visibility
log('API', `📤 POST ${apiUrl}`, { payload });
log('API', `📥 Response status: ${response.status}`);
```

**Log Areas:**
- `INIT` - Module initialization
- `MOUNT` - Component lifecycle
- `ACTION` - User interactions
- `API` - Request/response details
- `STATE` - Flow state transitions
- `ERROR` - Error details

---

## Deployment

### Build & Deploy Commands

```bash
cd /root/agenticverz2.0/website/landing
npm run build
sudo cp -r dist/* /opt/agenticverz/apps/site/dist/
```

### Production URL

**https://agenticverz.com/build**

---

## Verification

| Check | Status |
|-------|--------|
| `/build` route returns HTTP 200 | ✅ |
| React Router SPA navigation works | ✅ |
| API proxy to backend works | ✅ |
| Debug logs appear in console | ✅ |
| Form submission triggers API call | ✅ |
| Apache proxy returns 202 on POST | ✅ |

---

## UI Components (Lucide Icons)

| Icon | Usage |
|------|-------|
| `Zap` | Generate Plan button |
| `Rocket` | Start Execution button |
| `Users` | Agent workforce indicator |
| `Brain` | AI thinking/processing |
| `CheckCircle` | Completed steps |
| `Loader2` | Loading spinner |
| `Download` | Artifact download |
| `Shield` | Constraints/safety |

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-086 | Business Builder Worker v0.2 (backend) |
| PIN-087 | Business Builder API Hosting |
| PIN-088 | Worker Execution Console (Console UI) |
| PIN-093 | Worker v0.3 Real MOAT Integration |

---

## Future Enhancements

1. **SSE Streaming**: Real-time execution updates via Server-Sent Events
2. **Authentication**: Optional login for saved projects
3. **Export Formats**: PDF/Notion/Google Docs export
4. **Templates**: Pre-filled idea templates by industry
5. **Collaboration**: Share plans with team members

---

*Created: 2025-12-16*
*Author: Claude Code*
