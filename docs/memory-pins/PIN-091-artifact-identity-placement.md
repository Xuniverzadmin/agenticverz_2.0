# PIN-091: Artifact Identity & Placement Guarantees

**Status:** DOCTRINE
**Created:** 2025-12-16
**Category:** Operations / Deployment
**Trigger:** Blank page incident (wrong dist in wrong location)

---

## Principle

Every deployable artifact MUST declare its identity. Deployment MUST validate identity matches destination. Failures are hard stops, never warnings.

---

## Requirements

### 1. Fingerprint Requirement

All web artifacts must include identity metadata:

```html
<meta name="app-role" content="{role}" />
```

Current roles:
| Role | Artifact | Deploy Path |
|------|----------|-------------|
| `site-root` | Landing page | `/opt/agenticverz/apps/site/dist/` |
| `console-app` | AOS Console | `/opt/agenticverz/apps/console/dist/` |

Future evolution (when needed):
```html
<meta name="artifact-id" content="agenticverz.console.web.v1" />
```

### 2. Source → Destination Mapping

| Source | Destination | Base Path | Identity |
|--------|-------------|-----------|----------|
| `website/landing/dist/` | `/opt/agenticverz/apps/site/dist/` | `/` | `site-root` |
| `website/aos-console/console/dist/` | `/opt/agenticverz/apps/console/dist/` | `/console/` | `console-app` |

### 3. Deployment Validation

Script: `scripts/ops/deploy_website.sh`

Checks:
- Source build exists
- Fingerprint present and correct
- Base path alignment (no `/console/` in root, `/console/` required in console)
- Post-deploy verification
- Smoke test (title + JS load)

### 4. Fail Hard Principle

```
WRONG ARTIFACT → HARD STOP → NO DEPLOY
```

No warnings. No "deploy anyway" flags. No manual overrides.

---

## Compliance

Future deployables MUST:
1. Add fingerprint to source template
2. Add entry to mapping table
3. Add validation to deploy script
4. Add smoke check

---

## Smoke Checks

Post-deploy, verify user-visible correctness:

| Path | Check | Pass Criteria |
|------|-------|---------------|
| `/` | Title | Contains "Agenticverz" |
| `/` | JS load | HTTP 200, content-type JavaScript |
| `/console/` | Title | Contains "Console" |
| `/console/` | JS load | HTTP 200, content-type JavaScript |

---

## Files

| File | Purpose |
|------|---------|
| `scripts/ops/deploy_website.sh` | Deployment with validation |
| `website/landing/index.html` | `app-role="site-root"` |
| `website/aos-console/console/index.html` | `app-role="console-app"` |

---

*This is doctrine, not a milestone. All deployable artifacts must comply.*
