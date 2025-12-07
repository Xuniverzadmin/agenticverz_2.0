# SDK Packaging Checklist (M8)

**Goal:** `pip install aos-sdk` and `npm install @agenticverz/aos-sdk` work
**Status:** ✅ **COMPLETE (2025-12-05)**

---

## Summary

Both SDKs are published and working on public registries.

| SDK | Package | Version | Registry |
|-----|---------|---------|----------|
| Python | `aos-sdk` | 0.1.0 | [pypi.org/project/aos-sdk](https://pypi.org/project/aos-sdk/) |
| JS/TS | `@agenticverz/aos-sdk` | 0.1.0 | [npmjs.com/package/@agenticverz/aos-sdk](https://www.npmjs.com/package/@agenticverz/aos-sdk) |

---

## Python SDK

| Item | Status |
|------|--------|
| Location | `sdk/python/aos_sdk/` |
| Tests | ✅ 10/10 passing |
| Machine-native methods | ✅ Implemented |
| pyproject.toml | ✅ Created |
| CLI (`aos`) | ✅ Working |
| PyPI published | ✅ v0.1.0 |

### Install & Verify

```bash
pip install aos-sdk
aos version
python -c "from aos_sdk import AOSClient; print('OK')"
```

---

## JS/TS SDK

| Item | Status |
|------|--------|
| Location | `sdk/js/aos-sdk/` |
| Tests | ✅ Smoke tests passing |
| Machine-native methods | ✅ Implemented |
| TypeScript types | ✅ Included |
| package.json | ✅ Created |
| npm published | ✅ v0.1.0 |

### Install & Verify

```bash
npm install @agenticverz/aos-sdk
node -e "const {AOSClient} = require('@agenticverz/aos-sdk'); console.log('OK')"
```

---

## CI Workflows

| Workflow | Trigger | Status |
|----------|---------|--------|
| `publish-python-sdk.yml` | Tag `python-sdk-v*` | ✅ Created |
| `publish-js-sdk.yml` | Tag `js-sdk-v*` | ✅ Created |

### Release New Version

```bash
# Python
git tag python-sdk-v0.2.0 && git push origin python-sdk-v0.2.0

# JS
git tag js-sdk-v0.2.0 && git push origin js-sdk-v0.2.0
```

---

## Registry Tokens

Stored in HashiCorp Vault at `agenticverz/package-registry`:

| Secret | Purpose |
|--------|---------|
| `PYPI_API_TOKEN` | PyPI publish |
| `NPM_TOKEN` | npm publish |

---

## Completion Evidence

| Check | Result |
|-------|--------|
| `pip install aos-sdk` | ✅ Works |
| `npm install @agenticverz/aos-sdk` | ✅ Works |
| CLI `aos version` | ✅ Returns version |
| Python import | ✅ AOSClient imports |
| JS import | ✅ CJS/ESM both work |
| TypeScript types | ✅ Included in package |

---

## Related Documentation

- PIN-035: SDK Package Registry
- `sdk/python/README.md`
- `sdk/js/aos-sdk/README.md`

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-05 | Python SDK v0.1.0 published to PyPI |
| 2025-12-05 | JS SDK v0.1.0 published to npm |
| 2025-12-05 | CI workflows created for tagged releases |
| 2025-12-05 | Registry tokens stored in Vault |
| 2025-12-06 | Checklist marked COMPLETE |
