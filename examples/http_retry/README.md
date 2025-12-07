# HTTP Retry Demo

Demonstrates AOS **failure handling and recovery**.

This demo shows:
- Retry with exponential backoff
- Fallback to secondary endpoint
- Structured error outcomes
- Failure catalog matching

## Quick Start

```bash
# Install SDK
pip install aos-sdk

# Set environment
export AOS_API_KEY=your-api-key
export AOS_BASE_URL=http://localhost:8000

# Run demo
python demo.py

# Show failure catalog matching
SHOW_CATALOG=true python demo.py
```

## What It Does

### The Plan

1. **Try primary URL** (httpbin.org/status/503) - Always fails
2. **Retry** 2 times with 1 second backoff
3. **Fallback** to secondary URL (httpbin.org/status/200)
4. **Transform** result to extract status

### Flow

```
Primary URL (503)
    ↓ Fail
Retry #1 (503)
    ↓ Fail
Retry #2 (503)
    ↓ Fail
Fallback URL (200)
    ↓ Success!
Transform Result
```

## Machine-Native Failure Handling

In AOS, **failures are data, not exceptions**:

```json
{
  "outcome": {
    "success": false,
    "error": {
      "code": "HTTP_503",
      "category": "transient",
      "catalog_match": "SERVICE_UNAVAILABLE",
      "recovery_suggestion": "RETRY_WITH_BACKOFF"
    },
    "retries": [
      {"attempt": 1, "status": "failed"},
      {"attempt": 2, "status": "failed"}
    ],
    "fallback_used": true,
    "final_status": "succeeded"
  }
}
```

This enables:
- **Programmatic error handling** - No try/catch needed
- **Automatic recovery** - Catalog suggests actions
- **Audit trail** - All attempts recorded
- **Learning** - Failures feed back into catalog

## Expected Output

```
============================================================
AOS Demo: HTTP Retry & Failure Handling
============================================================

Configuration:
  API URL: http://127.0.0.1:8000
  Primary URL: https://httpbin.org/status/503
  Fallback URL: https://httpbin.org/status/200

Plan has 2 steps with retry/fallback:
  1. Try primary URL, fall back on failure
      Fallback: http_call
  2. Extract status and source URL

=== SIMULATION (Risk Analysis) ===

Feasibility: true
Estimated Cost: 5 cents

Identified Risks (2):
  1. Primary URL may return 5xx (transient)
  2. External HTTP dependency (network)

Step Analysis:

  Step 1: [http_call] Try primary URL, fall back on failure
    Feasible: true
    Potential Failures:
      - HTTP_503: Service Unavailable
      - TIMEOUT: Request timeout
      - NETWORK_ERROR: Connection failed

=== EXECUTION (With Retry) ===
Run created: run_abc123
Executing.... done!

Final Status: succeeded

Structured Outcome:
  Success: true

  Result: {
    "status": 200,
    "source": "https://httpbin.org/status/200"
  }

  Retry History (3 attempts):
    Attempt 1: failed
    Attempt 2: failed
    Attempt 3: succeeded (fallback)

============================================================
Demo complete!
Key takeaway: Failures are structured data, not exceptions.
============================================================
```

## Files

- `demo.py` - Main demo script
- `run.sh` - Shell wrapper
- `README.md` - This file

## Advanced Usage

```bash
# Show failure catalog matching
SHOW_CATALOG=true python demo.py

# Use custom endpoints
PRIMARY_URL=https://your-api.com/unreliable python demo.py
```
