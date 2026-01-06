# App-Shell Scope Contract

**Status:** NORMATIVE
**Effective:** 2026-01-06
**Reference:** PIN-319 (Frontend Realignment)

---

## Purpose

This document defines the **bounded responsibilities** of `app-shell/`.
Violations of this contract require explicit approval and PIN documentation.

---

## Allowed Responsibilities

### 1. Authentication Entry
- `LoginPage` - authentication entry point
- Token acquisition and storage
- Auth state management

### 2. Legal / Informational Pages
- `CreditsPage` - billing/credits display
- Terms of Service (if added)
- Privacy Policy (if added)

### 3. Routing & Audience Resolution
- Central router (`routes/index.tsx`)
- Audience detection (customer vs founder)
- Route guards (`ProtectedRoute`, `FounderRoute`, `OnboardingRoute`)
- Redirect logic

### 4. Shared Infrastructure
- UI components (`components/`)
- API clients (`api/`)
- Utilities (`lib/`, `utils/`)
- Stores (`stores/`)
- Types (`types/`)

### 5. Product Shells
- `products/ai-console/` - Customer console product

---

## Forbidden Responsibilities

### 1. Onboarding Logic
- **NO** onboarding flow pages
- **NO** tenant setup workflows
- **NO** first-run wizards
- Location: `website/onboarding/`

### 2. Business Workflows
- **NO** agent management
- **NO** execution monitoring
- **NO** policy configuration
- **NO** incident handling

### 3. Product-Specific UI
- **NO** founder-specific pages
- **NO** ops console pages
- **NO** SBA inspector
- **NO** replay/scenario tools
- Location: `website/fops/`

### 4. Founder/Customer Feature Logic
- **NO** founder-only features in shared code
- **NO** audience-specific business logic in shared components
- API clients must be audience-classified (see R2-1)

---

## Page Budget

`app-shell/src/pages/` is limited to:

| Page | Purpose | Status |
|------|---------|--------|
| `auth/LoginPage.tsx` | Authentication entry | ALLOWED |
| `credits/CreditsPage.tsx` | Billing display | ALLOWED |

**Any addition requires:**
1. Explicit justification
2. PIN documentation
3. Update to this contract

---

## Enforcement

### CI Checks
- Page budget validation (R1-2)
- Import boundary checks (R2-2)
- Directory ownership rules (G-1)

### Manual Review
- PRs touching `app-shell/src/pages/` require scope review
- New pages require contract amendment

---

## Violation Response

If a violation is detected:

1. **BLOCK** - CI fails or PR blocked
2. **DOCUMENT** - Create PIN explaining the violation
3. **RESOLVE** - Either:
   - Move code to correct location (`fops/`, `onboarding/`)
   - Amend this contract with justification

---

## References

- PIN-319: Frontend Realignment
- `docs/contracts/ONBOARDING_TO_APP_SHELL.md`
- `docs/inventories/FRONTEND_API_AUDIENCE_MAP.md`
