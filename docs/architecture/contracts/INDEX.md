# Architecture Contracts Index

**Status:** ENFORCED
**Effective:** 2026-01-17
**Reference:** PIN-LIM Post-Implementation Design Fix

---

## Purpose

These contracts close the degrees of freedom that lead to implementation errors.
They convert implicit assumptions into explicit, machine-verifiable rules.

---

## Contracts

| Contract | Scope | Enforcement |
|----------|-------|-------------|
| [NAMING.md](./NAMING.md) | Field names, schemas, enums | CI check |
| [MIGRATIONS.md](./MIGRATIONS.md) | Alembic lineage, DB target | CI check |
| [RUNTIME_VS_API.md](./RUNTIME_VS_API.md) | Layer boundaries, adapters | CI check |
| [AUTH_STATE.md](./AUTH_STATE.md) | Auth checks, tenant state | Runtime |
| [ROUTER_WIRING.md](./ROUTER_WIRING.md) | Router registration | CI check |
| [AUTHORITY_CONTRACT.md](./AUTHORITY_CONTRACT.md) | DB, auth, tenant authority | Runtime |

---

## Operational Documents

| Document | Purpose |
|----------|---------|
| [PREFLIGHT_CI_CHECKLIST.md](./PREFLIGHT_CI_CHECKLIST.md) | CI check suite documentation |
| [CLAUDE_CONTRIBUTION_PROTOCOL.md](./CLAUDE_CONTRIBUTION_PROTOCOL.md) | LLM-safe contribution guide |

---

## Preflight Scripts

| Script | Contract | Location |
|--------|----------|----------|
| `check_naming_contract.py` | NAMING.md | `scripts/preflight/` |
| `check_alembic_parent.py` | MIGRATIONS.md | `scripts/preflight/` |
| `check_runtime_api_boundary.py` | RUNTIME_VS_API.md | `scripts/preflight/` |
| `check_router_registry.py` | ROUTER_WIRING.md | `scripts/preflight/` |
| `run_all_checks.sh` | All | `scripts/preflight/` |

---

## Continuous Validation (Real-Time)

| Component | Purpose | Location |
|-----------|---------|----------|
| `continuous_validator.py` | File watcher daemon | `scripts/preflight/` |
| `validator_dashboard.py` | Real-time status UI | `scripts/preflight/` |
| `validator` | Convenience command | `scripts/preflight/` |
| `validator.service` | Systemd unit file | `scripts/preflight/` |
| `setup_continuous_validation.sh` | One-time setup | `scripts/preflight/` |

---

## Quick Commands

```bash
# Run all preflight checks (one-time)
./scripts/preflight/run_all_checks.sh

# Run individual checks
python scripts/preflight/check_naming_contract.py
python scripts/preflight/check_alembic_parent.py --all
python scripts/preflight/check_runtime_api_boundary.py
python scripts/preflight/check_router_registry.py

# Continuous validation (real-time)
validator start       # Start watching files
validator dashboard   # Interactive status UI
validator watch       # Compact watch mode
validator status      # Quick status check
validator stop        # Stop watching

# Systemd service (auto-start on boot)
validator service enable
validator service start
```

---

## Contract Change Process

1. **Identify gap** — Incident or pattern reveals missing rule
2. **Draft contract update** — Add rule with rationale
3. **Update preflight script** — Add detection for violation
4. **Test locally** — Verify script catches violations
5. **PR with both** — Contract + script change together
6. **CI enforces** — All future code checked

---

## Design Principles

1. **Contracts are declarative** — Rules, not prose
2. **Scripts are mechanical** — No judgment, pure detection
3. **Violations are blocking** — No "warnings" that become permanent
4. **Patterns guide Claude** — Structure > instructions
5. **Silence is a bug** — Unspecified = error-prone
