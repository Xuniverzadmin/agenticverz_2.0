# PIN-515: Production Wiring Contract — Policy Runtime Validator Injection

**Status:** ✅ COMPLETE
**Created:** 2026-02-03
**Category:** Architecture
**Predecessor:** PIN-514 (Runtime Convergence)

---

## Summary

Created documentation for the fail-closed validator injection points in the policy runtime. Operators now have a contract specifying:
- What must be wired in each environment
- What happens when nothing is wired
- How to wire permissive vs strict validators

---

## Purpose

The policy runtime implements fail-closed semantics for enforcement intents (EXECUTE, ROUTE, ESCALATE). Without explicit validator wiring, these intents are blocked.

This contract documents:
1. The three injection points and their protocols
2. Intent type classification (enforcement vs observability)
3. Environment-specific wiring requirements
4. Code examples for tests and production

---

## Key Contract Points

### Injection Points

| Point | Protocol | Default (None) |
|-------|----------|----------------|
| `intent_validator` | `PolicyIntentValidator` | BLOCK enforcement |
| `emission_sink` | `Callable[[dict], Awaitable]` | Structured logging |
| `policy_validator` | `PolicyCheckValidator` | deny (False) |

### Intent Classification

**Enforcement** (require validator):
- EXECUTE, ROUTE, ESCALATE

**Observability** (pass without validator):
- ALLOW, DENY, LOG, ALERT

### Environment Matrix

| Environment | Validator | Sink |
|-------------|-----------|------|
| Unit tests | Permissive | None |
| Integration | Real/stub | Test |
| Staging | Real M19 | Real M18 |
| Production | Real M19 | Real M18 |

---

## Files Created

| File | Purpose |
|------|---------|
| `docs/contracts/POLICY_RUNTIME_WIRING_CONTRACT.md` | Full wiring contract |
| `docs/memory-pins/PIN-515-production-wiring-contract.md` | This PIN |

---

## Related PINs

- **PIN-514**: Runtime Convergence (eliminated dual copies)
- **PIN-513**: Topology Completion & Hygiene
