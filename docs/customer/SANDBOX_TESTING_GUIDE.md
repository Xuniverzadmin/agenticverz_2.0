# Customer Sandbox Testing Guide

**Agenticverz Customer Integrations**

> This guide explains how to safely test your LLM integrations with Agenticverz **before going live**, without incurring production costs or affecting real data.

---

## What Is Sandbox Testing?

Sandbox testing lets you validate your integration with Agenticverz in a **non-production environment** that behaves like the real system, but with:

- No production billing
- Isolated test data
- Full policy and limit enforcement (for correctness)
- Realistic behavior of the Agenticverz APIs

Think of it as **"production behavior without production risk."**

---

## When Should You Use the Sandbox?

Use sandbox testing to:

- Verify your SDK integration
- Test LLM usage tracking and limits
- Validate budget or rate-limit behavior
- Confirm your application handles warnings or blocks correctly
- Test observability and usage reporting

Do **not** use the sandbox for live customer traffic.

---

## How Sandbox Testing Works

In sandbox mode:

- Your application calls the same Agenticverz APIs as production
- Requests are authenticated as a **sandbox customer**
- Data is stored in an isolated test environment
- Usage is tracked but **not billed**
- Limits and policies still apply, so you can see real outcomes

No special test endpoints are used — this ensures your production code will behave the same way.

---

## Authentication in Sandbox

Depending on how you integrate, you authenticate using one of the following (as provided by Agenticverz):

- A **sandbox customer API key**, or
- A **test customer token** issued for sandbox use

> Sandbox credentials only work in the sandbox environment and cannot be used in production.

### Example Request

```bash
curl -X GET \
  -H "X-AOS-Customer-Key: your_sandbox_key" \
  -H "Content-Type: application/json" \
  https://sandbox.agenticverz.com/api/v1/cus/integrations
```

---

## What You Can Test Safely

You can safely test:

| Feature | Description |
|---------|-------------|
| **LLM Integrations** | Creating and managing your LLM provider connections |
| **Usage Tracking** | Running LLM calls and seeing usage metrics |
| **Cost Visibility** | Viewing cost data without real billing |
| **Limit Testing** | Triggering warnings when approaching limits |
| **Block Testing** | Triggering blocks when exceeding limits |
| **Health Signals** | Observing integration health and status |

All of this mirrors real production behavior.

---

## What Sandbox Testing Does NOT Do

Sandbox testing does **not**:

- Use production databases
- Bill your account
- Affect live customers
- Bypass security controls
- Relax governance rules

**If something is blocked or limited in sandbox, it will behave the same way in production.**

---

## SDK Usage

### Python SDK

```python
from aos_sdk import AOSClient

# Sandbox testing
client = AOSClient(
    base_url="https://sandbox.agenticverz.com",
    customer_key="your_sandbox_key"
)

# List integrations
integrations = client.integrations.list()
print(integrations)

# Check usage
usage = client.telemetry.get_usage()
print(usage)
```

### JavaScript SDK

```javascript
import { AOSClient } from '@agenticverz/aos-sdk';

// Sandbox testing
const client = new AOSClient({
  baseUrl: 'https://sandbox.agenticverz.com',
  customerKey: 'your_sandbox_key'
});

// List integrations
const integrations = await client.integrations.list();
console.log(integrations);
```

---

## Testing Scenarios

### Scenario 1: Basic Integration Test

```bash
# Create an integration
curl -X POST \
  -H "X-AOS-Customer-Key: your_sandbox_key" \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "name": "Test Integration"}' \
  https://sandbox.agenticverz.com/api/v1/cus/integrations

# List integrations
curl -X GET \
  -H "X-AOS-Customer-Key: your_sandbox_key" \
  https://sandbox.agenticverz.com/api/v1/cus/integrations
```

### Scenario 2: Usage Limit Testing

```bash
# Check current usage
curl -X GET \
  -H "X-AOS-Customer-Key: your_sandbox_key" \
  https://sandbox.agenticverz.com/api/v1/cus/telemetry/usage

# Make LLM calls to approach limit
# Then verify warning/block behavior
```

### Scenario 3: Error Handling

```bash
# Test with invalid integration
curl -X GET \
  -H "X-AOS-Customer-Key: your_sandbox_key" \
  https://sandbox.agenticverz.com/api/v1/cus/integrations/invalid-id

# Verify your code handles 404 correctly
```

---

## Moving from Sandbox to Production

When you are ready to go live:

1. **Switch your configuration** to production credentials
2. **Point your application** to the production Agenticverz API endpoint
3. **Remove any sandbox-specific keys** or settings

No code changes should be required — only configuration changes.

### Configuration Comparison

| Setting | Sandbox | Production |
|---------|---------|------------|
| Base URL | `https://sandbox.agenticverz.com` | `https://api.agenticverz.com` |
| Auth Header | `X-AOS-Customer-Key: sandbox_key` | `Authorization: Bearer jwt` |
| Billing | Disabled | Active |
| Data | Isolated test data | Real customer data |

---

## Important Rules

| Rule | Description |
|------|-------------|
| **Credential Isolation** | Sandbox credentials must never be used in production |
| **No Cross-Use** | Production credentials will not work in sandbox |
| **No Auth Bypass** | If authentication fails, do not disable security checks |
| **Customer-Grade** | Treat sandbox testing as customer-grade, not a mock |

---

## Common Issues

### "401 Unauthorized"

- Verify you are using sandbox credentials
- Verify you are calling the sandbox endpoint
- Check the authentication header format

### "403 Forbidden"

- Your sandbox account may lack the required permissions
- Contact support to verify your sandbox access level

### "Rate Limited"

- Sandbox has the same rate limits as production
- This is intentional — it lets you test limit behavior
- Wait and retry, or request higher sandbox limits

---

## Need Help?

If you encounter issues during sandbox testing:

1. Confirm you are using sandbox credentials
2. Confirm you are calling the sandbox API endpoint
3. Check error responses for guidance

If problems persist, reach out to Agenticverz support with:

- Your sandbox tenant ID
- The endpoint you are calling
- The error message received

---

## Summary

> **Sandbox testing gives you confidence that your integration will work in production — without the cost or risk of production usage.**

It is the recommended way to validate your Agenticverz integration before launch.

---

## Related Resources

- [API Reference](https://docs.agenticverz.com/api)
- [SDK Documentation](https://docs.agenticverz.com/sdk)
- [Integration Guide](https://docs.agenticverz.com/integrations)
- [Support Portal](https://support.agenticverz.com)
