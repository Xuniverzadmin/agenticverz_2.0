# PIN-035: SDK Package Registry (PyPI + npm)

**Serial:** PIN-035
**Title:** SDK Package Registry (PyPI + npm)
**Category:** SDK / Developer Experience
**Status:** PUBLISHED
**Created:** 2025-12-05
**Updated:** 2025-12-05

---

## Executive Summary

Set up official AOS SDK packages for Python (PyPI) and JavaScript/TypeScript (npm) with automated CI/CD publishing workflows triggered by Git tags.

---

## Problem Statement

Prior to this implementation:
- SDKs existed but were not publishable to package registries
- No standardized installation (`pip install` / `npm install`)
- No version management or release automation
- No TypeScript type definitions for JS SDK
- No CLI tool for Python SDK

---

## Solution

### Packages

| Package | Registry | Name | Language |
|---------|----------|------|----------|
| Python SDK | PyPI | `aos-sdk` | Python 3.8+ |
| JS/TS SDK | npm | `@agenticverz/aos-sdk` | Node 18+ |

### Architecture

```
sdk/
├── python/
│   ├── pyproject.toml       # Modern Python packaging
│   ├── aos_sdk/
│   │   ├── __init__.py      # Version + exports
│   │   ├── client.py        # AOSClient class
│   │   ├── cli.py           # CLI entrypoint
│   │   └── py.typed         # Type hints marker
│   └── README.md
│
└── js/
    └── aos-sdk/
        ├── package.json     # npm package config
        ├── tsconfig.json    # TypeScript config
        ├── src/
        │   ├── index.ts     # Exports
        │   ├── client.ts    # AOSClient class
        │   └── types.ts     # Type definitions
        └── README.md
```

---

## Implementation Details

### Python SDK (`aos-sdk`)

**Installation:**
```bash
pip install aos-sdk
```

**Features:**
- Machine-native APIs: `simulate()`, `query()`, `get_capabilities()`
- Agent workflow APIs: `create_agent()`, `post_goal()`, `poll_run()`
- CLI: `aos version`, `aos capabilities`, `aos skills`
- Both `requests` and `httpx` supported
- Full type hints (`py.typed`)
- Python 3.8-3.12 compatible

**Example:**
```python
from aos_sdk import AOSClient

client = AOSClient(api_key="...", base_url="http://localhost:8000")
caps = client.get_capabilities()
result = client.simulate([{"skill": "http_call", "params": {"url": "..."}}])
```

### JavaScript SDK (`@agenticverz/aos-sdk`)

**Installation:**
```bash
npm install @agenticverz/aos-sdk
```

**Features:**
- Machine-native APIs with full TypeScript types
- ESM and CommonJS dual builds
- Node 18+ (native fetch)
- Type definitions included

**Example:**
```typescript
import { AOSClient, Capabilities } from '@agenticverz/aos-sdk';

const client = new AOSClient({ apiKey: '...', baseUrl: 'http://localhost:8000' });
const caps: Capabilities = await client.getCapabilities();
const result = await client.simulate([{ skill: 'http_call', params: { url: '...' } }]);
```

### CI/CD Workflows

**Python SDK (`.github/workflows/publish-python-sdk.yml`):**
- Trigger: `python-sdk-v*` tags
- Builds with `python -m build`
- Tests installation in clean venv
- Publishes to PyPI via `twine`
- Matrix tests on Python 3.8-3.12

**JS SDK (`.github/workflows/publish-js-sdk.yml`):**
- Trigger: `js-sdk-v*` tags
- Builds with `tsup`
- Type checks and lints
- Publishes to npm with provenance
- Matrix tests on Node 18, 20, 22

### Release Procedure

```bash
# Python SDK release
git tag python-sdk-v0.1.0
git push origin python-sdk-v0.1.0

# JS SDK release
git tag js-sdk-v0.1.0
git push origin js-sdk-v0.1.0
```

---

## Vault Integration

Package registry tokens stored in Vault at `agenticverz/package-registry`:
- `PYPI_API_TOKEN` - PyPI publish token
- `NPM_TOKEN` - npm publish token
- `TEST_PYPI_API_TOKEN` - TestPyPI for dry runs

To update tokens:
```bash
./scripts/ops/vault/rotate_secret.sh package-registry PYPI_API_TOKEN "pypi-xxx"
```

---

## Verification

### Acceptance Criteria

| Criteria | Status | Evidence |
|----------|--------|----------|
| Python SDK installs | ✅ | `pip install -e .` succeeds |
| Python SDK imports work | ✅ | `from aos_sdk import AOSClient` |
| Python CLI works | ✅ | `aos version` returns 0.1.0 |
| JS SDK builds | ✅ | `npm run build` produces dist/ |
| JS CJS import works | ✅ | `require()` loads correctly |
| TypeScript types included | ✅ | `.d.ts` files in dist/ |
| CI workflows created | ✅ | 2 workflow files added |
| Vault path created | ✅ | `agenticverz/package-registry` |

### Test Results

```bash
# Python SDK
$ source /tmp/test_sdk_venv/bin/activate
$ python -c "from aos_sdk import AOSClient, __version__; print(__version__)"
0.1.0
$ aos version
aos-sdk 0.1.0

# JS SDK
$ node -e "const { AOSClient, VERSION } = require('./dist/index.js'); console.log(VERSION)"
0.1.0
```

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `sdk/python/pyproject.toml` | Python package configuration |
| `sdk/python/aos_sdk/__init__.py` | Package exports + version |
| `sdk/python/aos_sdk/client.py` | AOSClient implementation |
| `sdk/python/aos_sdk/cli.py` | CLI entrypoint |
| `sdk/python/aos_sdk/py.typed` | Type hints marker |
| `sdk/python/README.md` | PyPI documentation |
| `sdk/js/aos-sdk/package.json` | npm package configuration |
| `sdk/js/aos-sdk/tsconfig.json` | TypeScript configuration |
| `sdk/js/aos-sdk/src/index.ts` | Package exports |
| `sdk/js/aos-sdk/src/client.ts` | AOSClient implementation |
| `sdk/js/aos-sdk/src/types.ts` | TypeScript type definitions |
| `sdk/js/aos-sdk/README.md` | npm documentation |
| `.github/workflows/publish-python-sdk.yml` | PyPI CI/CD |
| `.github/workflows/publish-js-sdk.yml` | npm CI/CD |

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-033 | M8-M14 Roadmap (SDK Packaging is M8 task) |
| PIN-034 | Vault Secrets (tokens stored in Vault) |
| PIN-005 | Machine-Native Architecture (SDK implements) |

---

## Published Packages

### Live on PyPI
**URL:** https://pypi.org/project/aos-sdk/0.1.0/
```bash
pip install aos-sdk
```

### Live on npm
**URL:** https://www.npmjs.com/package/@agenticverz/aos-sdk
```bash
npm install @agenticverz/aos-sdk
```

### Verified Working
- Python SDK installs from PyPI
- `aos version` CLI command works
- npm package installs
- CJS/ESM imports work
- TypeScript types included

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-05 | PIN-035 created |
| 2025-12-05 | Python SDK `aos_sdk` package created |
| 2025-12-05 | JS SDK `@agenticverz/aos-sdk` package created |
| 2025-12-05 | CI/CD workflows for both registries |
| 2025-12-05 | Vault path `package-registry` created |
| 2025-12-05 | Both SDKs tested and verified |
| 2025-12-05 | **PUBLISHED to PyPI:** https://pypi.org/project/aos-sdk/0.1.0/ |
| 2025-12-05 | **PUBLISHED to npm:** @agenticverz/aos-sdk@0.1.0 |
| 2025-12-05 | Verified: pip install and npm install work from public registries |
