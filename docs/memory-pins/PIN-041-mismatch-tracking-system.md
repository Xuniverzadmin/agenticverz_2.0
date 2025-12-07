# PIN-041: Mismatch Tracking System

**Status:** COMPLETE
**Created:** 2025-12-06
**Category:** Observability / Incident Management
**Exclusivity:** This PIN describes the authoritative replay mismatch tracking system

---

## Overview

Replay mismatch tracking system for detecting and managing determinism failures in AOS trace replays. Integrates with GitHub Issues and Slack for operator notification.

---

## Database Schema

**Table:** `aos_trace_mismatches`

```sql
CREATE TABLE aos_trace_mismatches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    reported_by TEXT,
    step_index INTEGER,
    reason TEXT NOT NULL,
    expected_hash TEXT,
    actual_hash TEXT,
    details JSONB DEFAULT '{}',
    notification_sent BOOLEAN DEFAULT FALSE,
    issue_url TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolved_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
```

**Migration:** `014_create_trace_mismatches.py`

**Metrics View:** `aos_mismatch_metrics`
- `mismatches_1h` - Count in last hour
- `mismatches_24h` - Count in last 24 hours
- `unresolved_count` - Open mismatches
- `pending_notification_count` - Awaiting notification

---

## API Endpoints

### Report Mismatch

```http
POST /api/v1/traces/{trace_id}/mismatch
```

Request:
```json
{
  "step_index": 3,
  "reason": "output_mismatch",
  "expected_hash": "abc123",
  "actual_hash": "def456",
  "details": {"field": "response_body"}
}
```

Response:
```json
{
  "mismatch_id": "uuid",
  "trace_id": "trace_123",
  "status": "recorded",
  "notified": "github",  // or "slack" or "none"
  "issue_url": "https://github.com/.../issues/42"
}
```

### List Mismatches

```http
GET /api/v1/traces/{trace_id}/mismatches
```

### Resolve Mismatch

```http
POST /api/v1/traces/{trace_id}/mismatches/{mismatch_id}/resolve?resolution_note=Fixed%20in%20v1.2
```

RBAC: Requires `admin` or `operator` role.

### Bulk Report (Multiple Mismatches → Single Issue)

```http
POST /api/v1/traces/mismatches/bulk-report?mismatch_ids=id1&mismatch_ids=id2&github_issue=true
```

Creates one GitHub issue for multiple related mismatches.

---

## Notification Integrations

### GitHub Issues

Environment:
```bash
GITHUB_TOKEN=ghp_xxx
GITHUB_REPO=Xuniverzadmin/agenticverz2.0
```

Labels applied: `replay-mismatch`, `aos`, `automated`

Issue format:
```markdown
## Replay Mismatch Detected

**Trace ID:** `trace_123`
**Step Index:** 3
**Reason:** output_mismatch
...
```

### Slack

Environment:
```bash
SLACK_MISMATCH_WEBHOOK=https://hooks.slack.com/services/...
```

Fallback if GitHub unavailable. Posts to configured channel.

---

## Workflow

1. **Detection:** Replay engine detects hash mismatch
2. **Report:** POST to `/traces/{id}/mismatch`
3. **Persist:** Stored in `aos_trace_mismatches`
4. **Notify:** GitHub issue OR Slack message
5. **Triage:** Operator reviews via API or dashboard
6. **Resolve:** POST to `/resolve` with optional note
7. **Close:** If GitHub issue exists, comment added

---

## Exclusivity Notes

This is the **single source of truth** for mismatch tracking. Do not:
- Create alternative mismatch tracking tables
- Add separate notification systems for mismatches
- Store mismatch data in trace records (reference only)

All mismatch logic flows through `traces.py` mismatch endpoints.

---

## Testing

```bash
# Test mismatch reporting (requires running backend)
curl -X POST http://localhost:8000/api/v1/traces/test-trace/mismatch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"step_index": 0, "reason": "test", "details": {}}'

# List mismatches
curl http://localhost:8000/api/v1/traces/test-trace/mismatches \
  -H "Authorization: Bearer $TOKEN"
```

---

## Related

- PIN-039: M8 Implementation Progress (parent)
- PIN-014: Trace mismatches migration
