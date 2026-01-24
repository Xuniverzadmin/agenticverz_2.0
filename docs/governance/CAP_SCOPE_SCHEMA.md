# CAP Scope Schema

**Status:** PROPOSED (Optional Enhancement)
**Created:** 2026-01-05
**Reference:** PIN-314

---

## Purpose

Define file ownership by capability (CAP) to enable:
1. Pre-push hooks to validate only relevant CAP files
2. Clear ownership boundaries for multi-contributor work
3. STOP conditions when ambiguous ownership is detected

---

## Schema: `.cap_scope.yaml`

```yaml
# .cap_scope.yaml - Placed in directory root or project root
version: "1.0"

# Default CAP for all files in this scope
default_cap: CAP-001

# File pattern overrides
patterns:
  - glob: "backend/app/auth/**"
    cap: CAP-006
    owner: platform

  - glob: "backend/app/predictions/**"
    cap: CAP-004
    owner: platform

  - glob: "website/app-shell/src/pages/fdr/**"
    cap: CAP-005
    owner: founder

# Explicit multi-CAP files (require human decision on changes)
multi_cap:
  - path: "backend/app/api/guard.py"
    caps: [CAP-001, CAP-009]
    resolution: HUMAN_REQUIRED
```

---

## Behavior

### Normal Case (Single CAP)

When a file matches exactly one CAP:
- Pre-push hook runs validations for that CAP only
- No ambiguity warning

### Multi-CAP Case

When a file matches multiple CAPs:
1. Hook emits warning: `AMBIGUOUS_OWNERSHIP: {file} matches {caps}`
2. Resolution determined by `multi_cap.resolution`:
   - `HUMAN_REQUIRED`: Hook halts, requires explicit bypass
   - `PRIMARY_WINS`: Uses first listed CAP
   - `SKIP`: No CAP-specific validation

### No Match Case

When a file matches no defined pattern:
- Falls back to `default_cap`
- If `default_cap` is not set, file is `UNSCOPED`

---

## Integration with Pre-Push Hook

### Environment Variable

```bash
# Optional: Override CAP detection
export WORKING_CAP=CAP-006
```

### Hook Logic (Pseudo-code)

```bash
# In ci_consistency_check.sh

detect_cap_scope() {
    local file="$1"

    # Check .cap_scope.yaml if exists
    if [[ -f ".cap_scope.yaml" ]]; then
        cap=$(python3 scripts/ops/cap_scope.py resolve "$file")
        echo "$cap"
    else
        echo "UNSCOPED"
    fi
}

check_cap_ownership() {
    local files="$1"

    for file in $files; do
        cap=$(detect_cap_scope "$file")
        if [[ "$cap" == "AMBIGUOUS" ]]; then
            log_warning "AMBIGUOUS_OWNERSHIP: $file"
            return 1  # STOP - human decision needed
        fi
    done
    return 0
}
```

---

## STOP Conditions

The hook MUST halt and require human intervention when:

| Condition | Trigger | Resolution |
|-----------|---------|------------|
| AMBIGUOUS_OWNERSHIP | File matches multiple CAPs | Human confirms intended CAP |
| CROSS_CAP_COMMIT | Single commit touches files from 3+ CAPs | Human confirms scope |
| UNREGISTERED_CAP | File references unknown CAP-XXX | Update registry first |

---

## Future Work

1. **G-3.1**: Create `scripts/ops/cap_scope.py` resolver
2. **G-3.2**: Integrate into `ci_consistency_check.sh`
3. **G-3.3**: Add STOP conditions for ambiguous ownership

---

## Related

- [CAPABILITY_REGISTRY.yaml](../capabilities/CAPABILITY_REGISTRY.yaml) — Authoritative capability definitions
- [PRE_PUSH_SCOPE_CONTRACT.md](PRE_PUSH_SCOPE_CONTRACT.md) — Hook scope governance
- [PIN-314](../memory-pins/PIN-314-pre-push-governance-fixes.md) — Pre-Push Governance Fixes
