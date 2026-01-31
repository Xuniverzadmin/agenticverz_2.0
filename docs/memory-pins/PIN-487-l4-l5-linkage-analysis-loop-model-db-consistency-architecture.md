# PIN-487: L4-L5 Linkage Analysis + Loop Model + DB Consistency Architecture

**Status:** ✅ COMPLETE
**Created:** 2026-01-28
**Category:** Architecture

---

## Summary

## L4-L5 Linkage Analysis, Loop Model, and DB Consistency Architecture

### Part 1: Current L4 <-> L5 Import Audit (2026-01-28)

Full audit of how hoc_spine (L4) connects to domain engines (L5) today.

#### CORRECT — L2 -> L4 (8 calls)
These go through spine properly:
- api/cus/policies/lifecycle.py -> hoc_spine.services.lifecycle_facade
- api/cus/policies/retrieval.py -> hoc_spine.services.retrieval_facade
- api/cus/policies/compliance.py -> hoc_spine.services.compliance_facade
- api/cus/policies/monitors.py -> hoc_spine.services.monitors_facade
- api/cus/policies/scheduler.py -> hoc_spine.services.scheduler_facade
- api/cus/policies/alerts.py -> hoc_spine.services.alerts_facade
- api/cus/policies/guard.py -> hoc_spine.drivers.guard_write_driver
- api/cus/policies/workers.py -> hoc_spine.drivers.worker_write_service_async

#### CORRECT — L4 -> L5 (6 calls)
Spine reaching down into domain engines:
- orchestrator/run_governance_facade.py -> policies.L5_engines.lessons_engine
- orchestrator/run_governance_facade.py -> incidents.L5_engines.policy_violation_service
- drivers/transaction_coordinator.py -> incidents.L5_engines.incident_driver
- drivers/transaction_coordinator.py -> logs.L5_engines.trace_facade
- authority/contracts/contract_engine.py -> policies.L5_engines.eligibility_engine
- orchestrator/__init__.py -> policies.L5_engines.eligibility_engine

#### ACCEPTABLE — L5 -> hoc_spine services (30 calls)
Domain engines using shared utilities:
- utc_now(), generate_uuid(), audit_store, runtime_switch, profile_policy_mode, cus_credential_service

#### VIOLATION — L2 -> L5 DIRECT (54 violations)
API endpoints bypass spine entirely. All should route through L4 orchestrator.
Major violators:
- api/cus/policies/ (24 violations) — policies.py, governance.py, policy_layer.py, policy_limits_crud.py, policy_rules_crud.py, rate_limits.py, simulate.py, cus_enforcement.py, guard.py
- api/cus/policies/ cross-domain (8) — importing from analytics, logs, integrations, account, incidents engines
- api/cus/incidents/ (4) — importing from logs, incidents engines
- api/cus/activity/ (4) — importing from activity engines
- api/cus/overview/ (1) — importing from overview engines
- api/cus/integrations/ (1) — importing from activity engines
- api/cus/recovery/ (1) — importing from incidents engines

#### VIOLATION — Cross-Domain L5 -> L5/L6 (24 violations)
Domains reaching into each other:
- Policies -> logs L6 (audit_ledger_service_async, 3 files), incidents L6 (lessons_driver), controls L6 (policy_limits_driver, limits_read_driver), apis L6 (keys_driver), incidents L5 (recovery_rule_engine)
- Incidents -> policies L5 (lessons_engine), logs L5 (audit_ledger_service)
- Activity -> controls L5 (threshold_engine), controls L6 (threshold_driver)
- Integrations -> logs L5, incidents L5, api_keys L5
- Controls -> activity L6 (run_signal_service)

#### PROBLEMATIC — L5 -> L4 Reaching Up (3 calls)
Domain engines calling orchestrator (should be inverted):
- cost_bridges_engine -> orchestrator.create_incident_from_cost_anomaly_sync
- activity/__init__ -> orchestrator.run_governance_facade
- eligibility_engine -> orchestrator

### Summary Table

| Category | Count | Status |
|----------|-------|--------|
| L4->L5 Orchestrator Calls | 6 | CORRECT |
| L2->L5 Direct Imports | 54 | VIOLATION |
| L2->L4 Facade Imports | 8 | CORRECT |
| Cross-Domain L5/L6 Imports | 24 | VIOLATION |
| L5->L4 Utility Imports | 30 | ACCEPTABLE |
| L5->L4 Reaching Up | 3 | PROBLEMATIC |

---

### Part 2: The Loop Model for Systematic Resolution

#### What is a Loop
One loop = one operation, fully vertical:
L2 endpoint -> L4 registry.resolve() -> L4 executor -> L5 engine.method() -> L6 driver -> L7 model -> DB
Each loop is a contract: given this input at L2, this row exists in L7. Testable. Deterministic.

#### Infrastructure Built Per Loop
- Loop 1 builds: Registry (C2) + Executor (C3) + test harness
- Loop 5 builds: Coordinator (C4) for cross-domain deps
- Each subsequent loop: adds one registry entry, tests one vertical path

#### Loop Progression

| Loop | Operation | New Infrastructure | Cross-Domain |
|------|-----------|-------------------|--------------|
| 1 | api_keys.list | Registry + Executor + test harness | None |
| 2 | api_keys.freeze | Write path through executor | None |
| 3 | account.get_tenant | Second domain proves registry scales | None |
| 4 | incidents.list | Third domain | None |
| 5 | overview.highlights | First cross-domain — needs Coordinator | incidents + policies + activity |

#### Selection Criteria for Loop Order
Zero cross-domain deps first, simplest L6, fewest L7 tables:
- api_keys: 1 L2->L5 violation, 0 cross-domain, 1 table (ApiKey)
- account: 3 L2->L5 violations, 0 cross-domain, 2 tables (Tenant, User)
- overview: 1 L2->L5 violation, 0 cross-domain (reads only), 0 tables (aggregates)

#### What Each Loop Proves
- Adds one registry entry (deterministic — resolves or doesn't)
- Tests one full vertical path (semantic — operation has business meaning)
- Runs against real DB (no mocks, no simulations)
- Catches broken L5->L6->L7 wiring immediately

#### How Violations Get Fixed
- 54 L2->L5 violations: fixed naturally as each operation wires through registry. L2 changes from "import L5_engine" to "execute(domain.operation)"
- 24 cross-domain violations: exposed when registering operations. Registry forces explicit cross_domain_deps declaration. Coordinator fetches data instead of L5 importing cross-domain.

---

### Part 3: DB Consistency Architecture

#### The Question
For operations like policy.lessons_learned that need data from multiple domains (tenant from account, llm_runs from activity, incidents from incidents), should there be separate databases per domain with a master canonical DB for sync?

#### The Answer: Single Database, Spine Mediates

Separate DBs would break the system:
1. Cross-DB joins become impossible
2. Transaction boundaries break — can't atomically write to incident.db AND activity.db
3. Sync becomes a distributed systems problem (eventual consistency, message queues, reconciliation)
4. The "master canonical DB" is literally what single PostgreSQL already provides

#### What AOS Already Has (Correct)
```
PostgreSQL (nova_aos) — single database
  tenants, users, api_keys, runs, incidents,
  policy_rules, policy_limits, lessons_learned, ...
  ALL IN ONE DATABASE, ONE TRANSACTION BOUNDARY
```
PostgreSQL guarantees ACID — when a transaction commits, ALL writes are consistent.

#### The Real Problem: Read Path, Not DB Structure
The problem isn't database architecture. It's that L5 engines reach across domains to read data:
- lessons_engine imports incidents.L6_drivers.lessons_driver (cross-domain violation)
- lessons_engine imports logs.L6_drivers.audit_ledger (cross-domain violation)

#### The Solution: L4 Spine Mediates Cross-Domain Reads
```
1. L2 receives request: "generate lessons for tenant X"
2. L4 executor resolves: operation = "policies.generate_lessons"
3. L4 coordinator fetches cross-domain context:
   - FROM activity: recent runs (success, failure, near-threshold)
   - FROM incidents: related incidents
   - FROM account: tenant config
4. L4 passes COMPLETE context to L5 lessons_engine
5. L5 has everything it needs — no cross-domain imports
6. L5 calls its OWN L6 driver to write lessons_learned rows
7. All in ONE database, ONE transaction
```

#### The Consistency Guarantee
```
Single PostgreSQL DB
  -> Single Session (transaction)
    -> L4 spine opens session
      -> reads from activity tables     (same session)
      -> reads from incident tables     (same session)
      -> reads from account tables      (same session)
      -> passes all data to L5
      -> L5 computes lessons
      -> L5 calls L6 to write lessons   (same session)
      -> L4 COMMITS                     (atomic — all or nothing)
```
If any read or write fails -> rollback -> nothing changes -> no inconsistency.
This is why topology says "L4 owns transaction boundaries" and driver comments say "NO COMMIT — L4 coordinator owns transaction boundary."

#### When You WOULD Split Databases
Only at scale where:
- Single DB can't handle throughput (millions of req/sec)
- Geographic distribution needed (US/EU data sovereignty)
- Willing to accept eventual consistency
AOS is nowhere near this threshold. Single PostgreSQL handles this cleanly.

#### Loop Test Example for Cross-Domain Operation
```python
def test_loop_lessons_learned(test_session):
    # Arrange: insert test data across domains (same DB, same session)
    tenant = create_tenant(test_session)
    run = create_run(test_session, tenant_id=tenant.id, status="failed")
    incident = create_incident(test_session, tenant_id=tenant.id)

    # Act: execute through spine
    result = execute(
        operation="policies.generate_lessons",
        tenant_id=tenant.id,
        params={},
        session=test_session,
    )

    # Assert: lessons exist, reference correct data
    lessons = test_session.query(LessonLearned).filter_by(tenant_id=tenant.id).all()
    assert len(lessons) > 0
    assert lessons[0].source_run_id == run.id

    # Rollback — test isolation, no DB pollution
```
One DB. One session. One transaction. Full consistency. Testable.

### Key Architectural Principles Established
1. Single PostgreSQL database = master canonical DB (already exists)
2. L4 owns transaction boundaries (session open/commit/rollback)
3. L6 drivers NEVER commit (NO COMMIT rule already in driver headers)
4. Cross-domain data flows through L4 coordinator, not L5 imports
5. Each loop proves one vertical slice against real DB
6. Loop progression: isolated domains first, cross-domain after coordinator exists

### References
- PIN-484: HOC Topology V2.0.0 Ratification
- PIN-485: V2.0.0 Migration Complete
- PIN-486: L3 Adapters Absorbed
- V2_MIGRATION_MANIFEST.md: Part 2 Construction items C2-C6
- HOC_LAYER_TOPOLOGY_V2.0.0.md: L4 executor, registry, coordinator specs

---

## Details

[Add details here]
