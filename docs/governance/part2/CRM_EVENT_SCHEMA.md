# CRM Event Schema Specification

**Status:** RATIFIED
**Effective:** 2026-01-04
**Reference:** part2-design-v1, PART2_CRM_WORKFLOW_CHARTER.md
**Layer:** L8 (Meta / Schema Definition)

---

## Purpose

This document defines the canonical schema for CRM events entering the Part-2
governance workflow. CRM events are **workflow initiators**, not authority sources.

The schema defines:
- Event envelope structure
- Required and optional fields
- Source attribution
- Deduplication semantics
- Severity normalization (input hints only)

---

## Constitutional Constraint

> **CRM events are INPUT, not DECISIONS.**
>
> This schema defines what data is captured at ingestion.
> It does NOT encode authority, eligibility, or execution semantics.
> Those belong to downstream components (Validator, Eligibility Engine, Founder Review).

---

## Event Envelope

Every CRM event MUST include an envelope with these fields:

```yaml
CRMEventEnvelope:
  # Identity
  event_id: UUID                    # Unique event identifier (system-generated)
  schema_version: "1.0.0"           # Schema version for compatibility

  # Classification
  event_type: ENUM                  # Type of event (see Event Types)
  source: ENUM                      # Source system (see Sources)

  # Timing
  source_timestamp: TIMESTAMP       # When event was created at source (ISO8601)
  received_at: TIMESTAMP            # When system received event (system-generated)

  # Deduplication
  idempotency_key: STRING           # Client-provided key for deduplication (required)
```

---

## Event Types

Events are classified by type. This is metadata, not authority.

| Type | Description | Workflow Entry |
|------|-------------|----------------|
| `issue` | Problem report or request | Creates issue_event |
| `feedback` | Customer feedback (no action required) | Creates issue_event |
| `alert` | System-generated alert | Creates issue_event |
| `escalation` | Explicit escalation request | Creates issue_event + notification |

**Note:** `event_type` is INPUT classification. The Validator determines `issue_type`.

### Event Type Authority Constraint

> `event_type` affects **routing and urgency only**, never eligibility, approval, or execution scope.

| event_type | Allowed Effect |
|------------|----------------|
| `issue` | Normal flow |
| `feedback` | Normal flow |
| `alert` | Prioritization hint only |
| `escalation` | Prioritization hint only |

**No branching logic authority.** Event type MUST NOT influence eligibility decisions,
approval requirements, or contract scope. Any implementation that treats event_type
as authority is in violation of Part-2 governance.

---

## Sources

Events originate from defined sources. This enables attribution and confidence weighting.

| Source | Description | Trust Weight |
|--------|-------------|--------------|
| `crm_feedback` | CRM platform feedback | Low (0.05) |
| `support_ticket` | Support system tickets | Medium (0.10) |
| `ops_alert` | Operations monitoring alerts | High (0.20) |
| `manual` | Manual submission via API | Neutral (0.00) |
| `integration` | Third-party integration | Variable |

---

## Source Attribution

Every event MUST include source attribution:

```yaml
SourceAttribution:
  # Source system identity
  source_system: STRING             # Name of originating system (e.g., "zendesk", "pagerduty")
  source_reference: STRING          # ID in source system (e.g., ticket #12345)

  # Submitter (optional but recommended)
  submitter_type: ENUM              # "human", "system", "integration"
  submitter_id: STRING (optional)   # Identifier of submitter (not PII)
  submitter_context: STRING (opt)   # Role or context (e.g., "customer", "support_agent")
```

---

## Payload Structure

The payload contains the actual issue content:

```yaml
Payload:
  # Required
  subject: STRING                   # Brief title (max 200 chars)
  body: STRING                      # Full content (max 10000 chars)

  # Optional structured data
  structured_data: JSONB (optional) # Machine-readable payload from source

  # Optional context
  tenant_context:
    tenant_id: UUID (optional)      # Tenant if known
    project_id: UUID (optional)     # Project if applicable
    environment: STRING (optional)  # "production", "staging", etc.

  # Optional attachments (references only, not binary)
  attachments:
    - type: STRING                  # "log", "screenshot", "trace", etc.
      reference: STRING             # URL or ID to retrieve
      size_bytes: INTEGER (opt)     # Size for processing decisions
```

---

## Input Hints

Hints are **suggestions from the source**, not authoritative.
The Validator determines actual classification.

```yaml
InputHints:
  # Structural semantics marker (REQUIRED)
  _semantics: NON_AUTHORITATIVE     # Explicit marker: hints have no authority

  # Severity suggestion (source's assessment)
  severity_hint: ENUM (optional)    # "critical", "high", "medium", "low"

  # Affected capabilities (if source knows)
  capability_hints: STRING[] (opt)  # Capability names source believes affected

  # Priority suggestion
  priority_hint: ENUM (optional)    # "urgent", "normal", "low"

  # Category suggestion
  category_hint: STRING (optional)  # Free-text category from source
```

### Hints Authority Constraint

**Invariant:** Hints do NOT override Validator verdicts. They are INPUT, not AUTHORITY.

> Any downstream component that treats hints as decisions is in violation of Part-2 governance and must fail CI.

Hints may be used by the Validator as **input signals** for confidence weighting,
but the Validator's verdict is the sole classification authority. No component
downstream of ingestion may branch on hint values for eligibility, approval, or execution.

---

## Complete Schema

```yaml
CRMEvent:
  # Envelope (required)
  envelope:
    event_id: UUID
    schema_version: "1.0.0"
    event_type: ENUM(issue, feedback, alert, escalation)
    source: ENUM(crm_feedback, support_ticket, ops_alert, manual, integration)
    source_timestamp: TIMESTAMP
    received_at: TIMESTAMP
    idempotency_key: STRING

  # Attribution (required)
  attribution:
    source_system: STRING
    source_reference: STRING
    submitter_type: ENUM(human, system, integration)
    submitter_id: STRING (optional)
    submitter_context: STRING (optional)

  # Payload (required)
  payload:
    subject: STRING (max 200)
    body: STRING (max 10000)
    structured_data: JSONB (optional)
    tenant_context:
      tenant_id: UUID (optional)
      project_id: UUID (optional)
      environment: STRING (optional)
    attachments: ARRAY (optional)

  # Hints (optional, NON_AUTHORITATIVE)
  hints:
    _semantics: NON_AUTHORITATIVE   # Explicit: hints have no authority
    severity_hint: ENUM (optional)
    capability_hints: STRING[] (optional)
    priority_hint: ENUM (optional)
    category_hint: STRING (optional)
```

---

## Deduplication Semantics

### Primary Deduplication

Events are deduplicated by `idempotency_key`:

```
Rule: Same idempotency_key within 24 hours = duplicate
Action: Return existing event_id, do not create new issue
```

### Idempotency Window Expiration

After the 24-hour window expires:

```
Rule: Same idempotency_key after 24 hours = new issue with recurrence link
Action: Create new issue, link to previous via recurrence_of field
```

This ensures:
- True duplicates (retries) are collapsed within the window
- Recurring issues (same problem reappearing) are tracked as separate issues
- Audit trail maintains linkage between related issues

### Secondary Deduplication

Cross-reference deduplication by source:

```
Rule: Same (source_system, source_reference) = likely duplicate
Action: Link to existing issue if status allows, else create new
```

### Deduplication Response

```yaml
DeduplicationResult:
  is_duplicate: BOOLEAN
  existing_event_id: UUID (if duplicate)
  existing_issue_id: UUID (if duplicate)
  duplicate_reason: ENUM(idempotency_key, source_reference, content_hash)
  recurrence_of: UUID (if post-window recurrence)
```

---

## Ingestion Flow

```
CRM Event (JSON)
    ↓
┌───────────────────────────────┐
│  Schema Validation (L8)       │  ← Validates against this schema
│  - Required fields present    │
│  - Field types correct        │
│  - Lengths within limits      │
└───────────────────────────────┘
    ↓
┌───────────────────────────────┐
│  Deduplication Check (L6)     │  ← Checks for duplicates
│  - Idempotency key lookup     │
│  - Source reference lookup    │
└───────────────────────────────┘
    ↓
┌───────────────────────────────┐
│  Issue Event Creation (L6)    │  ← Creates issue_events record
│  - Assigns issue_id           │
│  - Sets status = RECEIVED     │
│  - Stores raw event           │
└───────────────────────────────┘
    ↓
┌───────────────────────────────┐
│  Validator Queue (L5)         │  ← Enqueues for validation
│  - Async processing           │
│  - Does NOT block ingestion   │
└───────────────────────────────┘
```

---

## Database Mapping

CRM events are stored in `issue_events`:

```sql
CREATE TABLE issue_events (
    -- Identity
    issue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL UNIQUE,

    -- Envelope
    schema_version TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    source_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    idempotency_key TEXT NOT NULL,

    -- Attribution
    source_system TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    submitter_type TEXT NOT NULL,
    submitter_id TEXT,
    submitter_context TEXT,

    -- Payload (stored as JSONB for flexibility)
    payload JSONB NOT NULL,

    -- Hints (stored as JSONB)
    hints JSONB,

    -- Status
    status TEXT NOT NULL DEFAULT 'RECEIVED',
    status_reason TEXT,

    -- Recurrence tracking (for post-window duplicates)
    recurrence_of UUID REFERENCES issue_events(issue_id),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Deduplication (within 24h window)
    -- Note: idempotency_key uniqueness is time-bounded, enforced at application level
    -- UNIQUE (idempotency_key) removed - handled by app logic with window
    UNIQUE (source_system, source_reference)
);

-- Indexes
CREATE INDEX idx_issue_events_status ON issue_events(status);
CREATE INDEX idx_issue_events_source ON issue_events(source);
CREATE INDEX idx_issue_events_received ON issue_events(received_at);
CREATE INDEX idx_issue_events_source_ref ON issue_events(source_system, source_reference);
CREATE INDEX idx_issue_events_idempotency ON issue_events(idempotency_key, received_at);
CREATE INDEX idx_issue_events_recurrence ON issue_events(recurrence_of) WHERE recurrence_of IS NOT NULL;
```

---

## Issue Status Lifecycle

Issue events have their own status lifecycle (before becoming contracts):

| Status | Description | Next States |
|--------|-------------|-------------|
| `RECEIVED` | Event received, pending validation | `VALIDATING`, `INVALID` |
| `VALIDATING` | Validator analyzing | `VALIDATED`, `VALIDATION_FAILED` |
| `VALIDATED` | Validator produced verdict | (feeds Eligibility) |
| `VALIDATION_FAILED` | Validator could not process | Terminal |
| `INVALID` | Schema or content invalid | Terminal |

**Note:** This is the ISSUE lifecycle, not the CONTRACT lifecycle.
Issues that pass validation feed into the Contract state machine.

---

## Validation Rules

### Required Field Validation

| Field | Rule | Error |
|-------|------|-------|
| `envelope.event_id` | Valid UUID | `INVALID_EVENT_ID` |
| `envelope.idempotency_key` | Non-empty, max 256 chars | `INVALID_IDEMPOTENCY_KEY` |
| `envelope.event_type` | In allowed enum | `INVALID_EVENT_TYPE` |
| `envelope.source` | In allowed enum | `INVALID_SOURCE` |
| `attribution.source_system` | Non-empty, max 100 chars | `INVALID_SOURCE_SYSTEM` |
| `attribution.source_reference` | Non-empty, max 256 chars | `INVALID_SOURCE_REF` |
| `payload.subject` | Non-empty, max 200 chars | `INVALID_SUBJECT` |
| `payload.body` | Non-empty, max 10000 chars | `INVALID_BODY` |

### Content Validation

| Rule | Description |
|------|-------------|
| No executable content | `payload.body` must not contain scripts |
| No PII in identifiers | `submitter_id` must not be email/phone |
| Valid tenant reference | If `tenant_id` provided, must exist |
| Timestamp sanity | `source_timestamp` must be within 7 days of now |

---

## Error Responses

```yaml
IngestionError:
  error_code: ENUM
  field: STRING (which field failed)
  message: STRING (human-readable)
  event_id: UUID (if assigned)

ErrorCodes:
  - SCHEMA_VALIDATION_FAILED
  - DUPLICATE_EVENT
  - INVALID_FIELD
  - PAYLOAD_TOO_LARGE
  - RATE_LIMITED
  - INTERNAL_ERROR
```

---

## API Endpoint (Reference)

```
POST /api/v1/governance/events

Request:
  Content-Type: application/json
  X-AOS-Key: <api_key>
  X-Idempotency-Key: <idempotency_key>

  Body: CRMEvent (as defined above)

Response (success):
  201 Created
  {
    "event_id": "uuid",
    "issue_id": "uuid",
    "status": "RECEIVED",
    "is_duplicate": false
  }

Response (duplicate):
  200 OK
  {
    "event_id": "existing-uuid",
    "issue_id": "existing-uuid",
    "status": "...",
    "is_duplicate": true,
    "duplicate_reason": "idempotency_key"
  }

Response (error):
  400 Bad Request / 422 Unprocessable Entity
  {
    "error_code": "...",
    "field": "...",
    "message": "..."
  }
```

---

## What This Schema Does NOT Define

The following are explicitly OUT OF SCOPE for this schema:

| Item | Owner | Reference |
|------|-------|-----------|
| Issue type classification | Validator (L4) | VALIDATOR_LOGIC.md |
| Severity determination | Validator (L4) | VALIDATOR_LOGIC.md |
| Eligibility decisions | Eligibility Engine (L4) | ELIGIBILITY_RULES.md |
| Contract creation | Contract Service (L4) | SYSTEM_CONTRACT_OBJECT.md |
| Approval authority | Founder Review (Human) | FOUNDER_REVIEW_SEMANTICS.md |
| Health evaluation | PlatformHealthService (L4) | Phase-1 contracts |

### Explicitly Forbidden at Ingestion

The following are **explicitly forbidden** during CRM event ingestion:

| Forbidden Action | Reason |
|------------------|--------|
| Contract instantiation | Contracts require validation + eligibility |
| Contract state transitions | State machine belongs to Contract Service |
| Eligibility pre-evaluation | Must go through Validator first |
| Direct system mutations | CRM is input only, not execution |
| Health signal writes | Health authority is PlatformHealthService |

> **Invariant:** CRM ingestion MUST NOT create or mutate contracts directly.
>
> Any "fast path" that bypasses Validator → Eligibility → Founder Review
> is a Part-2 governance violation.

---

## Attestation

This schema defines the canonical input format for Part-2 CRM workflow initiation.
It is a **workflow initiator schema**, not an authority schema.

Implementation must:
1. Validate all events against this schema
2. Reject events that do not conform
3. Store raw events for audit
4. Not assume authority from input hints

---

## References

- Tag: `part2-design-v1`
- PART2_CRM_WORKFLOW_CHARTER.md (Step 1: Issue Receipt)
- VALIDATOR_LOGIC.md (ValidatorInput definition)
- SYSTEM_CONTRACT_OBJECT.md (issue_id FK reference)
