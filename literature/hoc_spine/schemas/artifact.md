# artifact.py

**Path:** `backend/app/hoc/cus/hoc_spine/schemas/artifact.py`  
**Layer:** L4 — HOC Spine (Schema)  
**Component:** Schemas

---

## Placement Card

```
File:            artifact.py
Lives in:        schemas/
Role:            Schemas
Inbound:         API routes, engines
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Artifact API schemas (pure Pydantic DTOs)
Violations:      none
```

## Purpose

Artifact API schemas (pure Pydantic DTOs)

## Import Analysis

**External:**
- `pydantic`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `_utc_now() -> datetime`

UTC timestamp (inlined to keep schemas pure — no service imports).

## Classes

### `ArtifactType(str, Enum)`

Type of artifact produced by a run.

### `StorageBackend(str, Enum)`

Where the artifact is stored.

### `Artifact(BaseModel)`

An artifact produced by a run or step.

Artifacts capture outputs, files, and data produced
during execution for later retrieval and analysis.

#### Methods

- `is_inline() -> bool` — Check if content is stored inline.
- `has_content() -> bool` — Check if artifact has content available.
- `get_inline_content() -> Optional[Any]` — Get inline content if available.

### `ArtifactReference(BaseModel)`

Lightweight reference to an artifact.

Used when you need to reference an artifact without
loading its full content.

#### Methods

- `from_artifact(artifact: Artifact) -> 'ArtifactReference'` — Create reference from full artifact.

## Domain Usage

**Callers:** API routes, engines

## Export Contract

```yaml
exports:
  functions:
    - name: _utc_now
      signature: "_utc_now() -> datetime"
      consumers: ["orchestrator"]
  classes:
    - name: ArtifactType
      methods: []
      consumers: ["orchestrator"]
    - name: StorageBackend
      methods: []
      consumers: ["orchestrator"]
    - name: Artifact
      methods:
        - is_inline
        - has_content
        - get_inline_content
      consumers: ["orchestrator"]
    - name: ArtifactReference
      methods:
        - from_artifact
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['pydantic']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

