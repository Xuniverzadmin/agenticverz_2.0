The platform does not give the LLM direct access to assets.

### Knowledge Plane (Platform-controlled access)

A plane is the platform’s controlled view of one or more assets:
- sanitized / normalized
- indexed
- tenant-isolated
- policy-gated

Policies refer to **planes**, not assets.

---

## 4) Onboarding Lifecycle (REGISTER → VERIFY → INGEST → INDEX → CLASSIFY → ACTIVATE → GOVERN)

This is a staged lifecycle, not a simple `status` field.

1. **REGISTER**
   - capture identity `(tenant, type, name)`
   - store a connector binding (by reference, not secrets)
2. **VERIFY**
   - validate credentials/ownership and read-only access
3. **INGEST**
   - extract documents/records, normalize, chunk, hash
4. **INDEX**
   - build retrieval indexes (vector/keyword/hybrid)
5. **CLASSIFY**
   - sensitivity, schema, allowed uses
6. **ACTIVATE**
   - plane becomes eligible for runtime access
   - default posture remains **deny-by-default** at policy level
7. **GOVERN**
   - evidence, audit, revocation/offboarding

**Invariant:** no skipping steps. Activation requires governance gates.

---

## 5) Policy Surface: Knowledge Access (Deny-By-Default)

RAG access belongs under *authorization*, not under monitoring.

Canonical policy shape (example):

```json
{
  "knowledge_access": {
    "mode": "DENY_BY_DEFAULT",
    "allowed_planes": ["docs:internal_wiki", "vector:public_docs"],
    "denied_planes": ["sql:customer_private"],
    "query_constraints": {
      "max_documents": 5,
      "max_tokens": 2000,
      "allow_semantic_search": true,
      "allow_sql": false
    },
    "logging": {
      "log_queries": true,
      "log_results_metadata": true,
      "log_raw_documents": false
    }
  }
}
```

Hard invariants:
- missing plane = blocked
- denied overrides allowed
- binding moment must be explicit (recommended: bind at run start)

---

## 6) Runtime Enforcement (What Actually Happens)

At every retrieval attempt:

1. `plane_id` is resolved by the runtime (not by the LLM).
2. policy is checked against `knowledge_access` snapshot.
3. connector/retriever is resolved for the plane.
4. evidence is emitted regardless of allow/deny outcome.

If a plane is not allowed → hard block with a structured violation.

---

## 7) Audit & Evidence (SOC2-Defensible)

Each access should record:
- `run_id`, `step_index`
- `plane_id`
- `policy_snapshot_id`
- `query_hash` (redaction-safe)
- `document_ids` / provenance metadata
- token count, latency

The point of evidence is to support the question:

> “Can we prove months later that this run could not have accessed a specific dataset?”

---

## 8) Authority Boundaries (System Rule)

Recorded decisions:
- hoc_spine is **system runtime** for customer-domain components (policies, account, integrations, logs).
- Audience surfaces (**CUS / INT / FDR**) are separate and must be wired intentionally; hoc_spine is not an “audience” surface.
- hoc_spine is the authority for lifecycle transitions.
- CUS domains may provide capabilities (connectors, ingestion jobs) but must not own the authority.

This prevents split-brain state machines and ensures a single audit trail.

---

## 9) Current Code Reality (Gap)

Today, parts of the plane registry and evidence stores are in-memory (non-durable).
The refactor plan (V2) moves this to Postgres and unifies the plane contract under hoc_spine.

Reference plan:
- `docs/architecture/hoc/KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_PLAN_V2.md`
