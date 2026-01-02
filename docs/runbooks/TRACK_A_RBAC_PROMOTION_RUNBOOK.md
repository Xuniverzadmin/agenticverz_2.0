# Track A Runbook — RBACv2 Promotion via Neon + Synthetic Load

**PIN-274 | CI North Star Aligned | Authority-Grade**

---

## Objective (Locked)

Prove **RBACv2 is safe to enforce** using **coverage + stress**, not time or users.

**Non-negotiables**

* Real Neon DB (prod-grade semantics)
* RBACv1 = Enforcement, RBACv2 = Shadow
* v2 must NEVER be more permissive than v1

---

## Preconditions (DO NOT SKIP)

☑ Neon database reachable
☑ RBACv1 enforcement ON
☑ RBACv2 shadow mode ON
☑ Metrics enabled (Prometheus endpoint reachable)
☑ You have Neon credentials with write access

Verify:

```bash
echo $DATABASE_URL
```

---

## Step 0 — Safety Snapshot (Rollback Ready)

**Purpose:** Guaranteed rollback if anything goes wrong.

```bash
# Save current env flags
export RBAC_V1_ENFORCE=true
export RBAC_V2_SHADOW=true

# (Optional) Snapshot Neon branch
neonctl branch create --name rbacv2-pretrackA
```

**Hard rule:**
If rollback is unclear → STOP. Do not proceed.

---

## Step 1 — Seed Neon with Test Tenancy

**Purpose:** Real enterprise semantics (accounts, teams, roles).

```bash
PGPASSWORD=... psql \
  -h <neon-host> \
  -d nova_aos \
  -f scripts/load/seed_neon_test_data.sql
```

**Verify**

* ≥3 enterprises
* ≥2 teams per enterprise
* Mixed roles (admin, team_admin, developer, viewer, system)

If seeding fails → **STOP**

---

## Step 2 — Dry Run (Wiring Check)

**Target:** 50k requests
**Goal:** Validate pipeline, metrics, logging

```bash
DATABASE_URL="postgresql://..." \
PYTHONPATH=backend \
python3 scripts/load/rbac_synthetic_load.py \
  --requests 50000 \
  --parallel 4 \
  --output /tmp/rbac_dry.json
```

Analyze:

```bash
python3 scripts/load/analyze_rbac_results.py \
  --input /tmp/rbac_dry.json \
  --output /tmp/rbac_dry_report.json
```

### HARD STOP CONDITIONS

❌ Any `v2_more_permissive`
❌ Script errors / crashes
❌ Missing metrics

If hit → FIX → RESTART from Step 2

---

## Step 3 — Coverage Run (Semantic Proof)

**Target:** 250k requests
**Goal:** Full matrix × repetition

```bash
DATABASE_URL="postgresql://..." \
PYTHONPATH=backend \
python3 scripts/load/rbac_synthetic_load.py \
  --requests 250000 \
  --parallel 4 \
  --output /tmp/rbac_cov.json
```

Analyze:

```bash
python3 scripts/load/analyze_rbac_results.py \
  --input /tmp/rbac_cov.json \
  --output /tmp/rbac_cov_report.json
```

### Required Outcomes

* v2_more_permissive = **0**
* Discrepancy rate < **1%**
* 100% discrepancies classified:

  * expected_tightening
  * expected_loosening
  * bug
  * spec_gap

Unclassified discrepancy → **STOP**

---

## Step 4 — Stress Run (Concurrency Proof)

**Target:** 500k requests
**Goal:** Race + parallelism exposure

```bash
DATABASE_URL="postgresql://..." \
PYTHONPATH=backend \
python3 scripts/load/rbac_synthetic_load.py \
  --requests 500000 \
  --parallel 6 \
  --output /tmp/rbac_stress.json
```

Analyze:

```bash
python3 scripts/load/analyze_rbac_results.py \
  --input /tmp/rbac_stress.json \
  --output /tmp/rbac_stress_report.json
```

### HARD STOP CONDITIONS (ABSOLUTE)

🚨 **Any** `v2_more_permissive`
🚨 AuthorizationEngine error
🚨 Discrepancy rate ≥1%

---

## Step 5 — Promotion Readiness Check (Final Gate)

All must be **TRUE**:

| Check                         | Status |
| ----------------------------- | ------ |
| Total requests ≥ 800k         | ☐      |
| v2_more_permissive = 0        | ☐      |
| Discrepancy rate <1%          | ☐      |
| 100% discrepancies classified | ☐      |
| RBACv2 p95 latency acceptable | ☐      |
| Rollback tested               | ☐      |
| Human signoff                 | ☐      |

If any ☐ unchecked → **DO NOT PROMOTE**

---

## Step 6 — Promotion (Controlled)

```bash
# Flip enforcement (explicit, auditable)
export RBAC_V2_ENFORCE=true
export RBAC_V1_ENFORCE=false
```

Monitor immediately:

* `rbac_v1_v2_comparison_total`
* `rbac_v2_latency_seconds`
* Security alerts

---

## Rollback (Instant, No Debate)

If anything looks wrong:

```bash
export RBAC_V2_ENFORCE=false
export RBAC_V1_ENFORCE=true
```

(Optional Neon branch rollback if schema touched)

---

## Definition of DONE (Locked)

✔ RBACv2 promoted on Neon
✔ Zero permissive discrepancies
✔ Promotion recorded in PIN-274
✔ Track A closed
✔ Track B (CI closure) may resume

---

### Final Note (Blunt)

This runbook replaces:

* "Wait 7 days"
* "We'll see in prod"
* "Seems fine"

If this passes, **RBACv2 is prod-grade** by design, not hope.
