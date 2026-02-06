# hoc_cus_logs_L6_drivers_capture

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L6_drivers/capture.py` |
| Layer | L6 — Domain Driver |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Taxonomy evidence capture service (ctx-aware) — L6 DOES NOT COMMIT

## Intent

**Role:** Taxonomy evidence capture service (ctx-aware) — L6 DOES NOT COMMIT
**Reference:** PIN-470, Evidence Architecture v1.1, ExecutionContext Specification v1.1, TRANSACTION_BYPASS_REMEDIATION_CHECKLIST.md
**Callers:** L5 engines (must provide session, must own transaction boundary)

## Purpose

Taxonomy Evidence Capture Service (v1.1)

---

## Functions

### `_assert_context_exists(ctx: ExecutionContext, evidence_type: str) -> None`
- **Async:** No
- **Docstring:** Hard guard: Fail fast if context is None.  Phase-1 Closure (PIN-405):
- **Calls:** EvidenceContextError, error

### `_record_capture_failure(session: Session, run_id: str, evidence_type: str, failure_reason: str, error_message: Optional[str], resolution: Optional[str]) -> None`
- **Async:** No
- **Docstring:** Record an evidence capture failure for later integrity reporting.  Watch-out #3: Best-effort evidence failures must surface in integrity.
- **Calls:** debug, execute, get, now, text, uuid4

### `_hash_content(content: str) -> str`
- **Async:** No
- **Docstring:** Generate SHA256 fingerprint of content.
- **Calls:** encode, hexdigest, sha256

### `capture_environment_evidence(session: Session, ctx: ExecutionContext) -> Optional[str]`
- **Async:** No
- **Docstring:** Capture environment evidence (Class H) at run creation.  Called once per run, immediately after run is persisted.
- **Calls:** _assert_context_exists, _record_capture_failure, assert_valid_for_evidence, execute, info, now, str, text, warning

### `capture_activity_evidence(session: Session, ctx: ExecutionContext) -> Optional[str]`
- **Async:** No
- **Docstring:** Capture activity evidence (Class B) before/after LLM calls.  TAXONOMY RULE: Activity evidence is only for externally consequential
- **Calls:** _assert_context_exists, _record_capture_failure, assert_valid_for_evidence, debug, execute, now, str, text, warning

### `capture_provider_evidence(session: Session, ctx: ExecutionContext) -> Optional[str]`
- **Async:** No
- **Docstring:** Capture provider evidence (Class G) after LLM provider response.  Called AFTER each provider interaction.
- **Calls:** _assert_context_exists, _record_capture_failure, assert_valid_for_evidence, debug, execute, now, str, text, warning

### `capture_policy_decision_evidence(session: Session, ctx: ExecutionContext) -> Optional[str]`
- **Async:** No
- **Docstring:** Capture policy decision evidence (Class D) during policy evaluation.  This bridges operational decision records to governance taxonomy.
- **Calls:** _assert_context_exists, _record_capture_failure, assert_valid_for_evidence, debug, execute, now, str, text, uuid4, warning

### `compute_integrity(run_id: str) -> Dict[str, Any]`
- **Async:** No
- **Docstring:** Compute integrity payload by examining evidence tables.  v1.1: Delegates to compute_integrity_v2 which uses the split architecture
- **Calls:** compute_integrity_v2, debug

### `capture_integrity_evidence(session: Session, run_id: str) -> Optional[str]`
- **Async:** No
- **Docstring:** Capture integrity evidence (Class J) at terminal state.  Called EXACTLY ONCE when run reaches terminal state.
- **Calls:** compute_integrity, copy, dumps, execute, get, info, now, str, text, warning

### `hash_prompt(prompt: str) -> str`
- **Async:** No
- **Docstring:** Generate SHA256 fingerprint of prompt content.
- **Calls:** _hash_content

## Classes

### `EvidenceContextError(Exception)`
- **Docstring:** Hard failure when evidence capture is attempted without ExecutionContext.
- **Methods:** __init__

### `CaptureFailureReason`
- **Docstring:** Standard failure reasons for integrity evidence.

### `FailureResolution`
- **Docstring:** Resolution semantics for capture failures.

## Attributes

- `logger` (line 75)
- `_FAILURE_RESOLUTION_MAP` (line 171)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.core.execution_context`, `app.evidence.integrity`, `sqlalchemy`, `sqlalchemy.exc`, `sqlmodel` |

## Callers

L5 engines (must provide session, must own transaction boundary)

## Export Contract

```yaml
exports:
  functions:
    - name: capture_environment_evidence
      signature: "capture_environment_evidence(session: Session, ctx: ExecutionContext) -> Optional[str]"
    - name: capture_activity_evidence
      signature: "capture_activity_evidence(session: Session, ctx: ExecutionContext) -> Optional[str]"
    - name: capture_provider_evidence
      signature: "capture_provider_evidence(session: Session, ctx: ExecutionContext) -> Optional[str]"
    - name: capture_policy_decision_evidence
      signature: "capture_policy_decision_evidence(session: Session, ctx: ExecutionContext) -> Optional[str]"
    - name: compute_integrity
      signature: "compute_integrity(run_id: str) -> Dict[str, Any]"
    - name: capture_integrity_evidence
      signature: "capture_integrity_evidence(session: Session, run_id: str) -> Optional[str]"
    - name: hash_prompt
      signature: "hash_prompt(prompt: str) -> str"
  classes:
    - name: EvidenceContextError
      methods: []
    - name: CaptureFailureReason
      methods: []
    - name: FailureResolution
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
