# AOS Developer Onboarding Guide (v1.0)

**Install -> Authenticate -> Simulate -> Execute -> Replay -> Inspect**

---

## 0. Prerequisites

**Required**
- Python 3.10+
- Node.js 18+
- curl
- A Keycloak user created by your admin
- AOS backend URL (e.g., `https://api.agenticverz.com`)

**Optional**
- Docker (for local infra)
- jq (for JSON viewing)

---

## 1. Install the SDKs

### Python

```bash
pip install aos-sdk
# verify
python -c "from aos_sdk import AOSClient; print('OK')"
```

### JavaScript / TypeScript

```bash
npm install @agenticverz/aos-sdk
# verify
node -e "import('@agenticverz/aos-sdk').then(()=>console.log('OK'))"
```

---

## 2. Get a JWT Access Token (Keycloak)

You must authenticate before calling AOS.

Replace:
- `<realm>`
- `<client_id>`
- `<username>`
- `<password>`

### Password Authentication (direct)

```bash
export TOKEN=$(curl -s \
  -d "client_id=<client_id>" \
  -d "grant_type=password" \
  -d "username=<username>" \
  -d "password=<password>" \
  https://auth-dev.xuniverz.com/realms/<realm>/protocol/openid-connect/token \
  | jq -r .access_token)
```

### Verify token

```bash
echo $TOKEN | cut -c1-20
```

### Test API connectivity

```bash
curl -H "Authorization: Bearer $TOKEN" https://api.agenticverz.com/healthz
```

---

## 3. Configure AOS Client

### Python

```python
from aos_sdk import AOSClient

client = AOSClient(
    api_url="https://api.agenticverz.com",
    token="<your JWT token>"
)
```

### JavaScript

```ts
import { AOSClient } from "@agenticverz/aos-sdk";

const client = new AOSClient({
  apiUrl: "https://api.agenticverz.com",
  token: process.env.AOS_TOKEN,
});
```

---

## 4. Run Your First Deterministic Simulation

AOS requires a "plan" - a machine-native workflow that is deterministic in simulation mode.

Example plan (`plan.json`):

```json
[
  { "skill": "echo", "input": { "text": "hello world" } }
]
```

### Simulate (dry-run)

```bash
aos simulate plan.json --seed 42 --dry-run
```

### Simulate and save trace

```bash
aos simulate plan.json --seed 42 --save-trace trace.json
```

**Output fields:**
- `trace_id` - unique identifier
- `root_hash` - deterministic hash for verification
- `seed` - reproducible random seed

---

## 5. Execute the Plan (real run)

```bash
aos run plan.json --seed 42 --save-trace exec.trace.json
```

**Simulation vs Execution**
- `simulate` -> no side effects
- `run` -> real execution

---

## 6. Replay and Verify Determinism

Replay enforces:
- input_hash match
- output_hash match
- step ordering
- idempotency rules

### Replay

```bash
aos replay trace.json -v
```

If everything matches:
```
Integrity: VERIFIED
```

---

## 7. Compare Two Traces

Useful for:
- debugging
- multi-language parity
- upstream dependency stability

```bash
aos diff trace1.json trace2.json
```

If deterministic, result is `IDENTICAL`.

---

## 8. View Your Stored Traces

AOS stores traces server-side if:
- `--save-trace` is enabled
- you call backend simulate/run APIs

### List traces

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.agenticverz.com/api/v1/traces?limit=20 | jq .
```

### Get single trace

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.agenticverz.com/api/v1/traces/<trace_id> | jq .
```

---

## 9. Idempotency & Replay Behavior (Important)

AOS enforces side-effect safety on replays.

Each step has:
- `idempotency_key`
- `replay_behavior`: `"execute" | "skip" | "check"`

### Pure functions

```json
"replay_behavior": "execute"
```

### External calls (Slack, HTTP)

```json
"replay_behavior": "skip"
```

### Fallback-required steps

```json
"replay_behavior": "check"
```

---

## 10. Using the Python SDK Directly

### Simulate

```python
trace = client.simulate(plan, seed=42, save_trace=True)
print(trace.root_hash)
```

### Execute

```python
exec_trace = client.execute(plan, seed=42)
print(exec_trace.output)
```

### Replay

```python
client.replay("trace.json")
```

---

## 11. Using the JS SDK Directly

### Simulate

```ts
const trace = await client.simulate(plan, { seed: 42, saveTrace: true });
console.log(trace.rootHash);
```

### Execute

```ts
const result = await client.execute(plan, { seed: 42 });
console.log(result.output);
```

### Replay

```ts
await client.replay("trace.json");
```

---

## 12. Common Errors & Fixes

### "403 forbidden"
- Tenant mismatch
- Missing role
- Using wrong realm or wrong client_id

### "Trace mismatch during replay"
- Non-idempotent step not marked `skip`
- External API returning variable output
- Plan changed between runs

### "Invalid token"
- Expired token - fetch a new one
- Wrong Keycloak realm

### "Redis missing for idempotency"
Set:
```bash
export REDIS_URL=redis://localhost:6379/0
```

---

## 13. Full End-to-End Test (Everything)

```bash
# 1. Simulate -> save trace
aos simulate plan.json --seed 42 --save-trace s.trace.json

# 2. Execute -> save trace
aos run plan.json --seed 42 --save-trace e.trace.json

# 3. Replay (should match)
aos replay s.trace.json

# 4. Compare two traces
aos diff s.trace.json e.trace.json

# 5. Check server traces
curl -H "Authorization: Bearer $TOKEN" https://api.agenticverz.com/api/v1/traces | jq .
```

If all succeed, your environment is correct.

---

## 14. Next Steps

- Build custom skills
- Build your own deterministic workflows
- Integrate external APIs (Slack, Stripe, Webhooks)
- Use AOS for fully self-healing automation

If you're an enterprise team:
- Set up multi-tenant roles
- Configure SSO/SAML
- Export traces to S3 / object storage
- Set alerting on determinism failures

---

## 15. Where To Get Help

**Docs**
```
/docs/QUICKSTART.md
/docs/AUTH_SETUP.md
/docs/DETERMINISM.md
```

**CLI Help**
```bash
aos --help
aos simulate --help
aos replay --help
```

**Issues**
Open a ticket in your organization's internal tracker or GitHub.
