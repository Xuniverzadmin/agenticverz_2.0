## Description

<!-- Brief description of changes -->

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Infrastructure/ops change
- [ ] Documentation update

## Checklist

- [ ] I have read the contributing guidelines
- [ ] My code follows the project's style
- [ ] I have added tests that prove my fix/feature works
- [ ] All new and existing tests pass locally
- [ ] I have updated documentation if needed

---

## M10/Infrastructure Changes

<!-- Complete this section if your PR touches M10, metrics, alerts, or ops scripts -->

### Runbook Reference

<!-- Link to relevant runbook section that documents this change -->
- Runbook: `docs/runbooks/_____.md#section`

### Metrics Impact

- [ ] This PR does NOT touch metrics
- [ ] This PR adds/modifies metrics AND includes test in `tests/test_m10_metrics.py`

### Staging Gate (Required for M10 changes)

- [ ] Not applicable (no M10 changes)
- [ ] Staging report JSON attached below
- [ ] All 10 P1 checks PASS

<details>
<summary>Staging Report (if applicable)</summary>

```json
{
  "paste": "m10_staging_report.json here"
}
```

</details>

---

## Deploy Ownership (Required for production deploys)

<!-- See docs/runbooks/DEPLOY_OWNERSHIP.md -->

- [ ] Not a production deploy
- [ ] **Owner:** @___
- [ ] **Deploy Window:** YYYY-MM-DD HH:MM to YYYY-MM-DD HH:MM UTC
- [ ] Owner confirmed available for 48h stabilization

---

## Related Issues/PINs

<!-- Link any related issues or memory PINs -->
- Fixes #
- Related PIN: PIN-0XX
