# Quarantined Frontend Clients

**Reference:** PIN-322 (L2-L2.1 Progressive Activation), PIN-323 (Audit Reinforcement)
**Quarantined:** 2026-01-06
**Status:** BLOCKED - Do not use in active code paths

---

## Why These Files Are Quarantined

These files invoke backend capabilities that are **not frontend-invocable** per the Capability Registry.

### Blocked API Clients

| File | Capability | Reason |
|------|------------|--------|
| `api/agents.ts` | CAP-008 (Multi-Agent) | SDK-only capability |
| `api/blackboard.ts` | CAP-008 (Multi-Agent) | SDK-only capability |
| `api/credits.ts` | CAP-008 (Multi-Agent) | SDK-only capability |
| `api/messages.ts` | CAP-008 (Multi-Agent) | SDK-only capability |
| `api/jobs.ts` | CAP-008 (Multi-Agent) | SDK-only capability |
| `api/worker.ts` | CAP-012 (Workflow Engine) | Internal capability |

### Blocked Type Files

| File | Reason |
|------|--------|
| `types/blackboard.ts` | Types for blocked capability |
| `types/worker.ts` | Types for blocked capability |

### Blocked Hooks

| File | Reason |
|------|--------|
| `hooks/useWorkerStream.ts` | Depends on blocked worker.ts |

---

## Resolution Options

1. **Remove entirely** - If these features are not needed for L1 launch
2. **Migrate to SDK** - Move these invocations to SDK usage pattern
3. **Promote to frontend-invocable** - Update CAPABILITY_REGISTRY.yaml if legitimately needed

---

## Do Not

- Import these files from active code paths
- Re-export these modules through index files
- Copy functionality to new files (that would bypass governance)

---

## References

- PIN-322: L2 ↔ L2.1 Progressive Activation
- PIN-323: L2 ↔ L2.1 Audit Reinforcement
- `docs/capabilities/CAPABILITY_REGISTRY.yaml`
- `docs/contracts/L2_L21_BINDINGS.yaml`

