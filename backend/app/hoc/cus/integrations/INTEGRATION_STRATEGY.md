# Integration Strategy (HOC / CUS / Integrations)

## Purpose
Define how the AI governance console monitors customer LLM usage across environments, with first-principles integration options and tradeoffs.

## First-Principles Requirement
To monitor, trace, and enforce controls, the system must be in the execution path (or at least the event path) of LLM calls.

## Integration Models

### Model A: Proxy / Gateway (Full Control)
Customer points their app to the AI console gateway instead of the provider.

**Flow**
Customer app -> AI console gateway -> LLM provider -> AI console gateway -> Customer app

**What this enables**
- Full request/response capture
- Run ID generation at ingress
- Deterministic logging and audit trail
- Real-time policy enforcement
- Replay support

**Provider behavior**
- Provider only sees the gateway as the caller.
- Requests are accepted if a valid key is used.
- Providers do not block proxying by default; they only enforce rate limits, terms, or key revocation.

**Credential options**
- Console key (reseller mode): simplest UX, provider cost borne by console.
- BYOK (customer key): customer retains billing; console must secure keys.

---

### Model B: SDK / Wrapper (Fast Adoption)
Customer uses the AI console SDK instead of calling the provider directly.

**Flow**
Customer app -> AI console SDK -> LLM provider

**What this enables**
- Structured logging
- Run ID generation
- Local policy enforcement

**Tradeoffs**
- Customers must update code.
- Enforcement depends on SDK usage compliance.

---

### Model C: Sidecar / Agent (Infra-Heavy)
A proxy sidecar runs in the customer's infrastructure.

**Flow**
Customer app -> Sidecar -> LLM provider

**What this enables**
- Consistent capture across services
- Works for heterogeneous apps

**Tradeoffs**
- Operational overhead for customers

---

### Model D: Log Ingestion (Lowest Control)
Customer sends logs or events to the console.

**Flow**
Customer app -> LLM provider
Customer logs -> AI console

**What this enables**
- Visibility only
- Post-hoc analysis

**Tradeoffs**
- No real-time controls
- Partial truth; weaker auditability

---

## Recommended Strategy (Default)
Use **Model A (Gateway)** when full governance, enforcement, and replay are required.
Use **Model B (SDK)** for fast adoption or when customers require BYOK without routing changes.

## Deterministic Monitoring Baseline
Regardless of integration model, the following are required:
- Run ID generation
- Immutable event ledger
- Request/response capture
- Validation and policy enforcement pipeline
- Replayability from stored inputs

## Open Questions (for product)
- Which model is default for enterprise vs SMB?
- Are BYOK keys stored or fetched just-in-time?
- What controls run at ingress vs post-response?
