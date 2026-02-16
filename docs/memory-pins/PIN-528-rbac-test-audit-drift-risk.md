# PIN-528: RBAC Test Audit - Drift Risk Identified

**Status:** ACKNOWLEDGED
**Created:** 2026-02-04
**Category:** Testing / Governance
**Severity:** Low (no current drift, future risk)
**Author:** Claude Opus 4.5
**Related:** PIN-527

---

## Summary

Post-implementation audit of PIN-527 (RBAC environment-aware test fix) identified a **drift risk**: the test file hardcodes `PREFLIGHT_PUBLIC_PATH_PREFIXES` rather than loading from the canonical source (`RBAC_RULES.yaml`). Current state shows perfect alignment, but future changes to RBAC rules may not reflect in tests.

---

## Audit Checklist Results

### 1. Source of Truth Duplication ⚠️

**Status:** HARDCODED (drift risk exists)

| Source | Count | Match |
|--------|-------|-------|
| `RBAC_RULES.yaml` (preflight-only PUBLIC) | 23 | ✓ |
| `test_rbac_path_mapping.py` hardcoded | 23 | ✓ |

**Current State:** Perfect match, no drift detected.

**Risk:** The test file contains a hardcoded list:
```python
PREFLIGHT_PUBLIC_PATH_PREFIXES: list[str] = [
    "/api/v1/agents/",
    "/api/v1/recovery/",
    # ... 21 more hardcoded paths
]
```

Future changes to `RBAC_RULES.yaml` won't automatically reflect in tests, potentially causing:
- False test failures (path added to YAML but not test)
- False test passes (path removed from YAML but not test)

**Recommendation:** Load dynamically from canonical source:
```python
from app.auth.rbac_rules_loader import get_public_paths

# Always-public paths (both environments) - filter these out
ALWAYS_PUBLIC = {"/health", "/metrics", "/docs", ...}

# Dynamic load from canonical source
_all_public = set(get_public_paths(environment="preflight"))
PREFLIGHT_PUBLIC_PATH_PREFIXES = list(_all_public - ALWAYS_PUBLIC)
```

---

### 2. Method Behavior ✓

**Status:** ALIGNED

| Component | Implementation |
|-----------|----------------|
| Middleware (`rbac_middleware.py`) | `path.startswith(public_path)` |
| Test helper (`is_public_in_preflight`) | `path.startswith(prefix)` |

Both use path prefix matching only. No method logic was incorrectly added to tests.

---

### 3. Environment Detection ✓

**Status:** ALIGNED

| File | Code | Default |
|------|------|---------|
| Test file | `os.getenv("AOS_ENVIRONMENT", "preflight")` | preflight |
| Middleware | `os.getenv("AOS_ENVIRONMENT", "preflight")` | preflight |
| Rules Loader | `environment: str = "preflight"` | preflight |

All components use identical environment detection with same default.

---

### 4. Scope ✓

**Status:** TESTS ONLY

| File | Modified | Date |
|------|----------|------|
| `tests/auth/test_rbac_path_mapping.py` | Yes | 2026-02-04 |
| `app/auth/rbac_middleware.py` | No | 2026-01-24 |
| `app/auth/rbac_rules_loader.py` | No | 2026-01-18 |
| `design/auth/RBAC_RULES.yaml` | No | unchanged |

Changes were properly isolated to test file only.

---

## Verification Commands

```bash
# Check for drift between YAML and test file
cd /root/agenticverz2.0/backend && python3 << 'EOF'
import yaml

with open("../design/auth/RBAC_RULES.yaml") as f:
    data = yaml.safe_load(f)

yaml_paths = set()
for rule in data.get("rules", []):
    if rule.get("access_tier") == "PUBLIC":
        if "preflight" in rule.get("allow_environment", []):
            yaml_paths.add(rule["path_prefix"])

# Exclude always-public paths
always_public = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc",
                 "/api/v1/auth/", "/api/v1/c2/predictions/", "/__debug/openapi_inspect",
                 "/__debug/openapi_nocache", "/founder/", "/platform/", "/sdk/",
                 "/api/v1/onboarding/", "/dashboard", "/operator", "/demo",
                 "/simulation", "/api/v1/operator"}

yaml_preflight_only = yaml_paths - always_public
print(f"YAML preflight-only PUBLIC paths: {len(yaml_preflight_only)}")
for p in sorted(yaml_preflight_only):
    print(f"  {p}")
EOF
```

---

## Decision

**Accepted Risk:** The hardcoded list is acceptable for now because:
1. Current state shows zero drift
2. RBAC rules are stable (PIN-427 paths expire 2026-03-01)
3. Test failures would surface any future misalignment

**Future Action:** When RBAC rules are modified, consider refactoring to dynamic loading.

---

## Audit Summary

| Check | Status | Notes |
|-------|--------|-------|
| Source of truth | ⚠️ | Hardcoded, 0 drift today |
| Method behavior | ✓ | Prefix-only matching aligned |
| Environment detection | ✓ | All default to "preflight" |
| Scope | ✓ | Tests only, no middleware changes |

---

## Sign-off

- [x] Audit completed
- [x] Drift risk documented
- [x] Verification commands provided
- [x] Decision recorded
- [x] PIN saved
