# HOC Customer Domain Documentation Index

**Location:** `backend/app/hoc/cus/docs/`
**Last Updated:** 2026-01-26

---

## Folder Structure

```
hoc/cus/docs/
├── INDEX.md                 # This file
├── domain-locks/            # Domain lock/freeze documents
├── audits/                  # Audit reports and BLCA reports
├── analysis/                # Domain analysis reports
├── authority/               # Authority maps and boundaries
└── contracts/               # Rules, contracts, and post-audit docs
```

---

## 1. Domain Locks (`domain-locks/`)

Frozen specifications defining domain boundaries and inventories.

| Document | Domain | Status |
|----------|--------|--------|
| [ACCOUNT_DOMAIN_LOCK_FINAL.md](domain-locks/ACCOUNT_DOMAIN_LOCK_FINAL.md) | account | LOCKED |
| [ACTIVITY_DOMAIN_LOCK_FINAL.md](domain-locks/ACTIVITY_DOMAIN_LOCK_FINAL.md) | activity | LOCKED |
| [ANALYTICS_DOMAIN_LOCK.md](domain-locks/ANALYTICS_DOMAIN_LOCK.md) | analytics | LOCKED |
| [ANALYTICS_DOMAIN_LOCK_FINAL.md](domain-locks/ANALYTICS_DOMAIN_LOCK_FINAL.md) | analytics | LOCKED |
| [API_KEYS_DOMAIN_LOCK_FINAL.md](domain-locks/API_KEYS_DOMAIN_LOCK_FINAL.md) | api_keys | LOCKED |
| [CONTROLS_DOMAIN_LOCK_FINAL.md](domain-locks/CONTROLS_DOMAIN_LOCK_FINAL.md) | controls | DRAFT |
| [GENERAL_DOMAIN_LOCK_FINAL.md](domain-locks/GENERAL_DOMAIN_LOCK_FINAL.md) | general | LOCKED |
| [INCIDENTS_DOMAIN_LOCK_FINAL.md](domain-locks/INCIDENTS_DOMAIN_LOCK_FINAL.md) | incidents | LOCKED |
| [INTEGRATIONS_DOMAIN_LOCK_FINAL.md](domain-locks/INTEGRATIONS_DOMAIN_LOCK_FINAL.md) | integrations | LOCKED |
| [LOGS_DOMAIN_LOCK_FINAL.md](domain-locks/LOGS_DOMAIN_LOCK_FINAL.md) | logs | LOCKED |
| [OVERVIEW_DOMAIN_LOCK_FINAL.md](domain-locks/OVERVIEW_DOMAIN_LOCK_FINAL.md) | overview | LOCKED |
| [POLICIES_DOMAIN_LOCK_FINAL.md](domain-locks/POLICIES_DOMAIN_LOCK_FINAL.md) | policies | LOCKED |

---

## 2. Audit Reports (`audits/`)

Layer validation and domain audit findings.

| Document | Scope | Type |
|----------|-------|------|
| [HOC_CUSTOMER_DOMAIN_AUDIT_2026-01-24.md](audits/HOC_CUSTOMER_DOMAIN_AUDIT_2026-01-24.md) | All domains | Executive summary |
| [HOC_account_detailed_audit_report.md](audits/HOC_account_detailed_audit_report.md) | account | Detailed audit |
| [HOC_activity_deep_audit_report.md](audits/HOC_activity_deep_audit_report.md) | activity | Deep audit |
| [HOC_analytics_detailed_audit_report.md](audits/HOC_analytics_detailed_audit_report.md) | analytics | Detailed audit |
| [HOC_api_keys_detailed_audit_report.md](audits/HOC_api_keys_detailed_audit_report.md) | api_keys | Detailed audit |
| [HOC_general_audit_domain.md](audits/HOC_general_audit_domain.md) | general | Domain audit |
| [HOC_general_deep_audit_report.md](audits/HOC_general_deep_audit_report.md) | general | Deep audit |
| [HOC_incidents_deep_audit_report.md](audits/HOC_incidents_deep_audit_report.md) | incidents | Deep audit |
| [HOC_integrations_detailed_audit_report.md](audits/HOC_integrations_detailed_audit_report.md) | integrations | Detailed audit |
| [HOC_logs_detailed_audit_report.md](audits/HOC_logs_detailed_audit_report.md) | logs | Detailed audit |
| [HOC_overview_detailed_audit_report.md](audits/HOC_overview_detailed_audit_report.md) | overview | Detailed audit |
| [HOC_policies_deep_audit_report.md](audits/HOC_policies_deep_audit_report.md) | policies | Deep audit |
| [HOC_policies_detailed_audit_report.md](audits/HOC_policies_detailed_audit_report.md) | policies | Detailed audit |
| [INCIDENTS_BLCA_REPORT.md](audits/INCIDENTS_BLCA_REPORT.md) | incidents | BLCA report |

---

## 3. Analysis Reports (`analysis/`)

Domain structure and extraction analysis.

| Document | Domain | Purpose |
|----------|--------|---------|
| [API_KEYS_DOMAIN_ANALYSIS_REPORT.md](analysis/API_KEYS_DOMAIN_ANALYSIS_REPORT.md) | api_keys | Structure analysis |
| [INCIDENTS_DOMAIN_ANALYSIS_REPORT.md](analysis/INCIDENTS_DOMAIN_ANALYSIS_REPORT.md) | incidents | Structure analysis |

---

## 4. Authority Maps (`authority/`)

Layer authority and boundary definitions.

| Document | Domain | Purpose |
|----------|--------|---------|
| [ANALYTICS_AUTHORITY_MAP.md](authority/ANALYTICS_AUTHORITY_MAP.md) | analytics | Engine authority inventory |

---

## 5. Contracts & Rules (`contracts/`)

Domain-specific rules and contracts.

| Document | Domain | Type |
|----------|--------|------|
| [ACTIVITY_DTO_RULES.md](contracts/ACTIVITY_DTO_RULES.md) | activity | DTO rules |
| [ANALYTICS_POST_AUDIT.md](contracts/ANALYTICS_POST_AUDIT.md) | analytics | Post-audit findings |

---

## Document Categories

| Category | Purpose | Location |
|----------|---------|----------|
| **Domain Locks** | Frozen domain specifications | `domain-locks/` |
| **Audits** | Layer validation findings | `audits/` |
| **Analysis** | Domain structure analysis | `analysis/` |
| **Authority** | Authority boundaries | `authority/` |
| **Contracts** | Rules and contracts | `contracts/` |

---

## Related Documentation

- HOC Layer Topology: `docs/architecture/HOC_LAYER_TOPOLOGY_V1.md`
- HOC Architecture Index: `docs/architecture/hoc/INDEX.md`
- Controls Domain: `docs/architecture/hoc/CONTROLS_DOMAIN.md`

---

*Last reorganization: 2026-01-26*
