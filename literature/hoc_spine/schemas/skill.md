# skill.py

**Path:** `backend/app/hoc/cus/hoc_spine/schemas/skill.py`  
**Layer:** L4 — HOC Spine (Schema)  
**Component:** Schemas

---

## Placement Card

```
File:            skill.py
Lives in:        schemas/
Role:            Schemas
Inbound:         API routes, engines
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Skill API schemas (pure Pydantic DTOs)
Violations:      none
```

## Purpose

Skill API schemas (pure Pydantic DTOs)

## Import Analysis

**External:**
- `pydantic`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `SkillStatus(str, Enum)`

Skill execution status.

### `SkillInputBase(BaseModel)`

Base class for all skill inputs.

All skill-specific inputs should inherit from this.
Provides common validation and serialization.

### `SkillOutputBase(BaseModel)`

Base class for all skill outputs.

Provides consistent structure for all skill results.

### `HttpMethod(str, Enum)`

Supported HTTP methods.

### `HttpCallInput(SkillInputBase)`

Input schema for http_call skill.

#### Methods

- `validate_url(v: str) -> str` — Basic URL validation.

### `HttpCallOutput(SkillOutputBase)`

Output schema for http_call skill.

### `LLMProvider(str, Enum)`

Supported LLM providers.

### `LLMMessage(BaseModel)`

A single message in the LLM conversation.

### `LLMInvokeInput(SkillInputBase)`

Input schema for llm_invoke skill.

### `LLMInvokeOutput(SkillOutputBase)`

Output schema for llm_invoke skill.

### `FileReadInput(SkillInputBase)`

Input schema for file_read skill.

### `FileReadOutput(SkillOutputBase)`

Output schema for file_read skill.

### `FileWriteInput(SkillInputBase)`

Input schema for file_write skill.

### `FileWriteOutput(SkillOutputBase)`

Output schema for file_write skill.

### `PostgresQueryInput(SkillInputBase)`

Input schema for postgres_query skill.

### `PostgresQueryOutput(SkillOutputBase)`

Output schema for postgres_query skill.

### `JsonTransformInput(SkillInputBase)`

Input schema for json_transform skill.

### `JsonTransformOutput(SkillOutputBase)`

Output schema for json_transform skill.

### `EmailSendInput(SkillInputBase)`

Input schema for email_send skill.

#### Methods

- `normalize_recipients(v)` — Ensure recipients are always a list.

### `EmailSendOutput(SkillOutputBase)`

Output schema for email_send skill.

### `KVOperation(str, Enum)`

KV store operations.

### `KVStoreInput(SkillInputBase)`

Input schema for kv_store skill.

### `KVStoreOutput(SkillOutputBase)`

Output schema for kv_store skill.

### `SlackSendInput(SkillInputBase)`

Input schema for slack_send skill.

### `SlackSendOutput(SkillOutputBase)`

Output schema for slack_send skill.

### `WebhookSendInput(SkillInputBase)`

Input schema for webhook_send skill.

#### Methods

- `validate_webhook_url(v: str) -> str` — _No docstring._

### `WebhookSendOutput(SkillOutputBase)`

Output schema for webhook_send skill.

### `VoyageModel(str, Enum)`

Voyage AI embedding models.

### `VoyageInputType(str, Enum)`

Input type for Voyage embeddings.

### `VoyageEmbedInput(SkillInputBase)`

Input schema for voyage_embed skill.

### `VoyageEmbedOutput(SkillOutputBase)`

Output schema for voyage_embed skill.

### `SkillMetadata(BaseModel)`

Metadata about a registered skill.

## Domain Usage

**Callers:** API routes, engines

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: SkillStatus
      methods: []
      consumers: ["orchestrator"]
    - name: SkillInputBase
      methods: []
      consumers: ["orchestrator"]
    - name: SkillOutputBase
      methods: []
      consumers: ["orchestrator"]
    - name: HttpMethod
      methods: []
      consumers: ["orchestrator"]
    - name: HttpCallInput
      methods:
        - validate_url
      consumers: ["orchestrator"]
    - name: HttpCallOutput
      methods: []
      consumers: ["orchestrator"]
    - name: LLMProvider
      methods: []
      consumers: ["orchestrator"]
    - name: LLMMessage
      methods: []
      consumers: ["orchestrator"]
    - name: LLMInvokeInput
      methods: []
      consumers: ["orchestrator"]
    - name: LLMInvokeOutput
      methods: []
      consumers: ["orchestrator"]
    - name: FileReadInput
      methods: []
      consumers: ["orchestrator"]
    - name: FileReadOutput
      methods: []
      consumers: ["orchestrator"]
    - name: FileWriteInput
      methods: []
      consumers: ["orchestrator"]
    - name: FileWriteOutput
      methods: []
      consumers: ["orchestrator"]
    - name: PostgresQueryInput
      methods: []
      consumers: ["orchestrator"]
    - name: PostgresQueryOutput
      methods: []
      consumers: ["orchestrator"]
    - name: JsonTransformInput
      methods: []
      consumers: ["orchestrator"]
    - name: JsonTransformOutput
      methods: []
      consumers: ["orchestrator"]
    - name: EmailSendInput
      methods:
        - normalize_recipients
      consumers: ["orchestrator"]
    - name: EmailSendOutput
      methods: []
      consumers: ["orchestrator"]
    - name: KVOperation
      methods: []
      consumers: ["orchestrator"]
    - name: KVStoreInput
      methods: []
      consumers: ["orchestrator"]
    - name: KVStoreOutput
      methods: []
      consumers: ["orchestrator"]
    - name: SlackSendInput
      methods: []
      consumers: ["orchestrator"]
    - name: SlackSendOutput
      methods: []
      consumers: ["orchestrator"]
    - name: WebhookSendInput
      methods:
        - validate_webhook_url
      consumers: ["orchestrator"]
    - name: WebhookSendOutput
      methods: []
      consumers: ["orchestrator"]
    - name: VoyageModel
      methods: []
      consumers: ["orchestrator"]
    - name: VoyageInputType
      methods: []
      consumers: ["orchestrator"]
    - name: VoyageEmbedInput
      methods: []
      consumers: ["orchestrator"]
    - name: VoyageEmbedOutput
      methods: []
      consumers: ["orchestrator"]
    - name: SkillMetadata
      methods: []
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['pydantic']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

