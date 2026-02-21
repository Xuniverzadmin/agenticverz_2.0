# HOC CUS API Ledger Wave 1 Audit

- Generated UTC: 2026-02-21T06:59:48Z
- Worktree: /tmp/hoc-clean-ledger-1771656914

## Commands

### Layer Boundaries
```bash
cd /tmp/hoc-clean-ledger-1771656914/backend && PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
- Exit code: 0
```text
============================================================
LAYER BOUNDARY CHECK
============================================================
Root: /tmp/hoc-clean-ledger-1771656914/backend

Checking FastAPI imports in domain code...
Checking upward imports (domain -> routes)...
Checking route file placement...
Checking observability query boundary...

============================================================
CLEAN: No layer boundary violations found
============================================================
```

### Layer Segregation Guard (hoc)
```bash
cd /tmp/hoc-clean-ledger-1771656914 && python3 scripts/ops/layer_segregation_guard.py --scope hoc
```
- Exit code: 0
```text
============================================================
LAYER SEGREGATION GUARD
Reference: DRIVER_ENGINE_PATTERN_LOCKED.md
Scope: hoc
============================================================

### Check 1: Engine DB Access Violations
Engines must not import sqlalchemy/sqlmodel or access DB directly

  ❌ app/hoc/fdr/ops/engines/founder_action_write_engine.py
     Line 46: ORM model import
     Line 108: session.rollback() call
  ❌ app/hoc/fdr/ops/engines/ops_incident_engine.py
     Line 280: session.execute() call
     Line 311: session.execute() call
  ❌ app/hoc/fdr/account/engines/explorer_engine.py
     Line 21: sqlalchemy import
     Line 22: sqlalchemy import
  ❌ app/hoc/fdr/logs/engines/timeline_engine.py
     Line 20: sqlalchemy import
     Line 21: sqlalchemy import
  ❌ app/hoc/fdr/logs/engines/review_engine.py
     Line 21: sqlalchemy import
     Line 22: sqlalchemy import
  ❌ app/hoc/fdr/incidents/engines/ops_incident_engine.py
     Line 280: session.execute() call
     Line 311: session.execute() call
  ❌ app/hoc/int/platform/engines/sandbox_engine.py
     Line 318: session.execute() call
  ❌ app/hoc/int/agent/engines/job_engine.py
     Line 23: sqlalchemy import
     Line 24: sqlalchemy import
     Line 299: session.execute() call
     Line 638: session.execute() call
  ❌ app/hoc/int/agent/engines/invoke_audit_engine.py
     Line 18: sqlalchemy import
     Line 19: sqlalchemy import
     Line 242: session.execute() call
     Line 296: session.execute() call
  ❌ app/hoc/int/agent/engines/worker_engine.py
     Line 16: sqlalchemy import
     Line 17: sqlalchemy import
     Line 100: session.execute() call
     Line 115: session.commit() call
     Line 121: session.execute() call
     Line 170: session.rollback() call
     Line 233: session.execute() call
     Line 267: session.execute() call
     Line 292: session.execute() call
     Line 304: session.commit() call
     Line 307: session.rollback() call
     Line 347: session.execute() call
     Line 369: session.execute() call
     Line 401: session.execute() call
     Line 419: session.commit() call
     Line 435: session.rollback() call
     Line 462: session.execute() call
     Line 488: session.execute() call
     Line 514: session.execute() call
     Line 531: session.execute() call
     Line 552: session.commit() call
     Line 556: session.rollback() call
     Line 574: session.execute() call
     Line 589: session.commit() call
     Line 603: session.rollback() call
  ❌ app/hoc/int/agent/engines/credit_engine.py
     Line 23: sqlalchemy import
     Line 24: sqlalchemy import
     Line 121: session.execute() call
     Line 212: session.execute() call
     Line 229: session.commit() call
     Line 247: session.rollback() call
     Line 295: session.execute() call
     Line 309: session.commit() call
     Line 318: session.rollback() call
     Line 343: session.execute() call
     Line 357: session.commit() call
     Line 375: session.rollback() call
     Line 418: session.execute() call
     Line 438: session.commit() call
     Line 447: session.rollback() call
  ❌ app/hoc/int/agent/engines/message_engine.py
     Line 21: sqlalchemy import
     Line 22: sqlalchemy import
     Line 127: session.execute() call
     Line 153: session.execute() call
     Line 167: session.commit() call
     Line 182: session.rollback() call
     Line 235: session.execute() call
     Line 296: session.execute() call
     Line 308: session.commit() call
     Line 311: session.rollback() call
  ❌ app/hoc/int/agent/engines/registry_engine.py
     Line 17: sqlalchemy import
     Line 18: sqlalchemy import
     Line 108: session.execute() call
     Line 134: session.commit() call
     Line 152: session.rollback() call
     Line 172: session.execute() call
     Line 188: session.commit() call
     Line 197: session.rollback() call
     Line 213: session.execute() call
     Line 225: session.commit() call
     Line 234: session.rollback() call
     Line 494: session.execute() call
  ❌ app/hoc/int/agent/engines/governance_engine.py
     Line 21: sqlalchemy import
     Line 22: sqlalchemy import
     Line 148: session.execute() call
     Line 171: session.execute() call
     Line 406: session.execute() call
     Line 469: session.execute() call
     Line 495: session.commit() call
     Line 520: session.execute() call
     Line 538: session.execute() call

### Check 2: Driver Business Logic Violations
Drivers must not contain policy/threshold/validation logic

  ❌ app/hoc/int/platform/drivers/memory_driver.py
```

### Capability Registry Enforcer (changed files)
- Exit code: 0
- Skipped: no changed .py files in current Wave 1 delta.

### OpenAPI Snapshot Check
```bash
cd /tmp/hoc-clean-ledger-1771656914 && python3 scripts/ci/check_openapi_snapshot.py
```
- Exit code: 0
```text
============================================================
CI GUARD: OpenAPI Snapshot Validity
============================================================

  [1/4] File exists: .openapi_snapshot.json
  [2/4] File non-empty: 695,560 bytes
  [3/4] Valid JSON
  [4/4] Has paths: 394 routes

============================================================
PASS: OpenAPI snapshot is valid
============================================================
```
