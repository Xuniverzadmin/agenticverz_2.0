# hoc_cus_logs_L5_engines_evidence_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/evidence_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Evidence Facade - Centralized access to evidence and export operations

## Intent

**Role:** Evidence Facade - Centralized access to evidence and export operations
**Reference:** PIN-470, GAP-104 (Evidence Chain API), GAP-105 (Evidence Export API)
**Callers:** L2 evidence.py API, SDK

## Purpose

Evidence Facade (L5 Domain Engine)

---

## Functions

### `get_evidence_facade() -> EvidenceFacade`
- **Async:** No
- **Docstring:** Get the evidence facade instance.  This is the recommended way to access evidence operations
- **Calls:** EvidenceFacade

## Classes

### `EvidenceType(str, Enum)`
- **Docstring:** Evidence types.

### `ExportFormat(str, Enum)`
- **Docstring:** Export formats.

### `ExportStatus(str, Enum)`
- **Docstring:** Export status.

### `EvidenceLink`
- **Docstring:** A link in an evidence chain.
- **Methods:** to_dict
- **Class Variables:** id: str, evidence_type: str, timestamp: str, hash: str, previous_hash: Optional[str], data: Dict[str, Any]

### `EvidenceChain`
- **Docstring:** An evidence chain.
- **Methods:** to_dict
- **Class Variables:** id: str, tenant_id: str, run_id: Optional[str], created_at: str, root_hash: str, link_count: int, links: List[EvidenceLink], metadata: Dict[str, Any]

### `VerificationResult`
- **Docstring:** Result of chain verification.
- **Methods:** to_dict
- **Class Variables:** valid: bool, chain_id: str, links_verified: int, errors: List[str]

### `EvidenceExport`
- **Docstring:** Evidence export request.
- **Methods:** to_dict
- **Class Variables:** id: str, tenant_id: str, chain_id: str, format: str, status: str, created_at: str, completed_at: Optional[str], download_url: Optional[str], error: Optional[str]

### `EvidenceFacade`
- **Docstring:** Facade for evidence chain and export operations.
- **Methods:** __init__, list_chains, get_chain, create_chain, add_evidence, verify_chain, _create_link, _hash_data, create_export, get_export, list_exports

## Attributes

- `logger` (line 63)
- `_facade_instance: Optional[EvidenceFacade]` (line 554)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

L2 evidence.py API, SDK

## Export Contract

```yaml
exports:
  functions:
    - name: get_evidence_facade
      signature: "get_evidence_facade() -> EvidenceFacade"
  classes:
    - name: EvidenceType
      methods: []
    - name: ExportFormat
      methods: []
    - name: ExportStatus
      methods: []
    - name: EvidenceLink
      methods: [to_dict]
    - name: EvidenceChain
      methods: [to_dict]
    - name: VerificationResult
      methods: [to_dict]
    - name: EvidenceExport
      methods: [to_dict]
    - name: EvidenceFacade
      methods: [list_chains, get_chain, create_chain, add_evidence, verify_chain, create_export, get_export, list_exports]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
