# webhook_verify.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/webhook_verify.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            webhook_verify.py
Lives in:        services/
Role:            Services
Inbound:         webhook API
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Webhook Signature Verification Utility
Violations:      none
```

## Purpose

Webhook Signature Verification Utility

Provides HMAC-SHA256 signature verification for webhook receivers with
support for key versioning and grace periods during rotation.

Usage (FastAPI example):
    from app.utils.webhook_verify import WebhookVerifier

    verifier = WebhookVerifier(keys={
        "v1": "old_key_hex...",
        "v2": "new_key_hex...",
    }, current_version="v2", grace_versions=["v1"])

    @app.post("/webhook")
    async def receive_webhook(request: Request):
        body = await request.body()
        signature = request.headers.get("X-Webhook-Signature")
        key_version = request.headers.get("X-Webhook-Key-Version")

        if not verifier.verify(body, signature, key_version):
            raise HTTPException(status_code=401, detail="Invalid signature")
        # Process webhook...

## Import Analysis

**External:**
- `hvac`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `create_file_key_loader(keys_path: str) -> Callable[[str], Optional[str]]`

Create a key loader that reads from files.

Args:
    keys_path: Directory containing key files (e.g., /var/lib/aos/webhook-keys)

Returns:
    Function that loads key hex string for a version

### `create_vault_key_loader(mount_path: str, secret_path: str) -> Callable[[str], Optional[str]]`

Create a key loader that reads from Vault.

Requires hvac library: pip install hvac

Args:
    mount_path: Vault KV v2 mount path
    secret_path: Path to secret within mount

Returns:
    Function that loads key hex string for a version

### `verify_webhook(body: bytes, signature: str, key_version: Optional[str], keys: Dict[str, str], grace_versions: Optional[List[str]]) -> bool`

Quick verification without creating a WebhookVerifier instance.

Args:
    body: Raw request body
    signature: X-Webhook-Signature header
    key_version: X-Webhook-Key-Version header
    keys: Dict of version -> hex key
    grace_versions: List of grace period versions

Returns:
    True if valid

## Classes

### `WebhookVerifier`

Webhook signature verifier with key version support.

Supports zero-downtime key rotation by accepting:
1. The specified key version from X-Webhook-Key-Version header
2. Grace period versions during rotation
3. Current version as fallback if no header provided

#### Methods

- `__init__(keys: Optional[Dict[str, str]], current_version: Optional[str], grace_versions: Optional[List[str]], key_loader: Optional[Callable[[str], Optional[str]]])` — Initialize verifier.
- `_parse_grace_env() -> List[str]` — Parse grace versions from environment.
- `_get_key(version: str) -> Optional[bytes]` — Get key bytes for a version.
- `_compute_signature(body: bytes, key: bytes) -> str` — Compute HMAC-SHA256 signature.
- `verify(body: Union[bytes, str], signature: Optional[str], key_version: Optional[str]) -> bool` — Verify webhook signature.
- `sign(body: Union[bytes, str], version: Optional[str]) -> tuple` — Sign a payload (for testing or forwarding).

## Domain Usage

**Callers:** webhook API

## Export Contract

```yaml
exports:
  functions:
    - name: create_file_key_loader
      signature: "create_file_key_loader(keys_path: str) -> Callable[[str], Optional[str]]"
      consumers: ["orchestrator"]
    - name: create_vault_key_loader
      signature: "create_vault_key_loader(mount_path: str, secret_path: str) -> Callable[[str], Optional[str]]"
      consumers: ["orchestrator"]
    - name: verify_webhook
      signature: "verify_webhook(body: bytes, signature: str, key_version: Optional[str], keys: Dict[str, str], grace_versions: Optional[List[str]]) -> bool"
      consumers: ["orchestrator"]
  classes:
    - name: WebhookVerifier
      methods:
        - verify
        - sign
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['hvac']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

