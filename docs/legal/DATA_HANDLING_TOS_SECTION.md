# Data Handling Terms of Service Section

**Status:** DRAFT
**Date:** 2025-12-30
**Reference:** PIN-052

---

## Purpose

This document provides the data handling section for the AOS Terms of Service.
It covers how customer data (including error messages) is processed, stored, and protected.

---

## Proposed ToS Section: Data Handling

### 1. Data Categories

AOS processes the following categories of data:

| Category | Description | Retention |
|----------|-------------|-----------|
| **Execution Data** | Run logs, traces, step outputs | 90 days |
| **Error Data** | Error messages, stack traces | 90 days (sanitized) |
| **Memory Data** | Agent memory, context | Tenant-controlled |
| **Embedding Data** | Vector representations | Indefinite (anonymized) |
| **Billing Data** | Usage, cost reports | 7 years (legal) |

### 2. Data Sanitization

**2.1 Automatic Sanitization**

Before processing error messages for machine learning or storage, AOS automatically removes:

- API keys and tokens (e.g., `sk-*`, `Bearer *`)
- Database connection strings with credentials
- Email addresses
- Private keys and certificates
- Credit card numbers
- Social Security Numbers

**2.2 Sanitization Guarantee**

> AOS will NEVER embed or store raw secrets in vector databases.
> All error messages are sanitized before embedding operations.

### 3. Tenant Isolation

**3.1 Data Boundary**

Each tenant's data is logically isolated:

- All queries include `tenant_id` filtering
- Cross-tenant data access is technically impossible
- Tenant data cannot be viewed by other tenants

**3.2 Audit Trail**

All data access is logged with:

- Timestamp
- Accessor identity
- Action performed
- Affected records

### 4. Embedding & Machine Learning

**4.1 How Embeddings Are Used**

Error patterns may be embedded (converted to vectors) to:

- Find similar historical failures
- Suggest recovery actions
- Improve system reliability

**4.2 Data Anonymization**

Before embedding:

1. All secrets are removed (see Section 2.1)
2. Tenant-specific identifiers are generalized
3. Timestamps are normalized

**4.3 Opt-Out**

Tenants may opt out of embedding-based features by:

1. Setting `DISABLE_EMBEDDINGS=true` in tenant configuration
2. Contacting support for manual data removal

### 5. Third-Party Services

AOS uses the following third-party services for AI operations:

| Service | Purpose | Data Sent |
|---------|---------|-----------|
| OpenAI | Embeddings | Sanitized text only |
| Anthropic | LLM reasoning | Sanitized error context |
| Voyage AI | Backup embeddings | Sanitized text only |

**All data sent to third parties is sanitized and anonymized.**

### 6. Data Retention

| Data Type | Default Retention | Configurable |
|-----------|-------------------|--------------|
| Execution traces | 90 days | Yes |
| Error patterns | 90 days | Yes |
| Embeddings | Indefinite | Yes (deletion supported) |
| Audit logs | 2 years | No |

### 7. Data Deletion Rights

Tenants may request:

1. **Export:** Full data export in JSON format
2. **Deletion:** Complete removal of all tenant data
3. **Anonymization:** Removal of identifying information

Requests are processed within 30 days.

### 8. Security Measures

| Measure | Implementation |
|---------|----------------|
| Encryption at rest | AES-256 |
| Encryption in transit | TLS 1.3 |
| Access control | RBAC with audit |
| Secret detection | Automatic sanitization |
| Penetration testing | Annual |

---

## Implementation Status

| Requirement | Status | Reference |
|-------------|--------|-----------|
| Secret sanitization | COMPLETE | `app/security/sanitize.py` |
| Tenant isolation | AUDIT IN PROGRESS | PIN-052 |
| Embedding anonymization | COMPLETE | Vector store integration |
| Opt-out mechanism | PENDING | Future work |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Initial draft |
