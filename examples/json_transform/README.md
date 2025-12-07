# JSON Transform Demo

Demonstrates **pure deterministic transformation** with AOS.

This demo shows:
- Same input always produces same output
- Transforms are safe to replay
- Budget and feasibility checking

## Quick Start

```bash
# Install SDK
pip install aos-sdk

# Set environment
export AOS_API_KEY=your-api-key
export AOS_BASE_URL=http://localhost:8000

# Run demo
python demo.py

# Optional: verify determinism
CHECK_DETERMINISM=true python demo.py
```

## What It Does

**Input:** User list with mixed active/inactive status
```json
{
  "users": [
    {"id": 1, "name": "Alice", "active": true},
    {"id": 2, "name": "Bob", "active": false},
    {"id": 3, "name": "Charlie", "active": true}
  ]
}
```

**Transform Steps:**
1. Filter only active users
2. Extract name and email
3. Reshape to contact list format

**Output:**
```json
[
  {"contact": "alice@example.com", "label": "Alice"},
  {"contact": "charlie@example.com", "label": "Charlie"}
]
```

## Why Determinism Matters

In AOS, `json_transform` is a **pure skill**:
- No external dependencies
- No side effects
- Identical inputs always produce identical outputs

This enables:
- **Replay testing** - Verify behavior without re-execution
- **Golden file testing** - Compare outputs against known-good
- **Cost prediction** - Exact cost known before execution

## Expected Output

```
============================================================
AOS Demo: JSON Transform (Deterministic)
============================================================

Input Data:
{
  "users": [
    {"id": 1, "name": "Alice", ...},
    ...
  ]
}

Transform Plan:
  1. Filter active users and extract name/email
  2. Reshape into contact list format

=== SIMULATION ===
Plan has 2 transform steps

Simulation Result:
  Feasible: True
  Estimated Cost: 1 cents
  Deterministic: Yes (json_transform is pure)

=== EXECUTION ===
Run created: run_xyz789

Execution Status: succeeded

Transformed Output:
[
  {"contact": "alice@example.com", "label": "Alice"},
  {"contact": "charlie@example.com", "label": "Charlie"}
]

============================================================
[SUCCESS] JSON transform completed!
============================================================
```

## Files

- `demo.py` - Main demo script
- `run.sh` - Shell wrapper
- `README.md` - This file
