"""
AOS Deterministic Runtime Context

Provides deterministic primitives for simulation and replay:
- Fixed seed for reproducible randomness
- Frozen time for time-independent simulation
- Tenant isolation
- RNG state capture for audit

Usage:
    ctx = RuntimeContext(seed=42, now="2025-12-06T12:00:00Z")
    value = ctx.randint(1, 100)  # Always same result for same seed
    ts = ctx.now  # Frozen timestamp
"""

import random
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict


@dataclass
class RuntimeContext:
    """
    Deterministic runtime context for AOS simulation and replay.

    All randomness and time access must go through this context
    to ensure reproducible behavior.

    Attributes:
        seed: Random seed for deterministic behavior (default: 42)
        now: Frozen timestamp (default: current UTC time)
        tenant_id: Tenant identifier for isolation
        env: Recorded environment variables (for audit)
        rng_state: Captured RNG state for replay
    """
    seed: int = 42
    now: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str = "default"
    env: Dict[str, str] = field(default_factory=dict)
    rng_state: Optional[str] = None
    _rng: random.Random = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        """Initialize RNG with seed."""
        if self.now is None:
            self.now = datetime.now(timezone.utc)
        elif isinstance(self.now, str):
            self.now = datetime.fromisoformat(self.now.replace('Z', '+00:00'))
        self._rng = random.Random(self.seed)
        self.rng_state = self._capture_rng_state()

    def _capture_rng_state(self) -> str:
        """Capture RNG state as hex string for audit."""
        state = self._rng.getstate()
        state_bytes = json.dumps(state, default=str).encode()
        return hashlib.sha256(state_bytes).hexdigest()[:16]

    def randint(self, a: int, b: int) -> int:
        """Deterministic random integer in [a, b]."""
        return self._rng.randint(a, b)

    def random(self) -> float:
        """Deterministic random float in [0, 1)."""
        return self._rng.random()

    def choice(self, seq: List[Any]) -> Any:
        """Deterministic random choice from sequence."""
        return self._rng.choice(seq)

    def shuffle(self, seq: List[Any]) -> None:
        """Deterministic in-place shuffle."""
        self._rng.shuffle(seq)

    def uuid(self) -> str:
        """Deterministic UUID based on seed and counter."""
        # Generate deterministic UUID from random bytes
        rand_bytes = bytes([self._rng.randint(0, 255) for _ in range(16)])
        hex_str = rand_bytes.hex()
        return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"

    def timestamp(self) -> str:
        """Return frozen timestamp as ISO8601 string."""
        return self.now.isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context for trace."""
        return {
            "seed": self.seed,
            "now": self.now.isoformat(),
            "tenant_id": self.tenant_id,
            "env": self.env,
            "rng_state": self.rng_state
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeContext":
        """Deserialize context from trace."""
        return cls(
            seed=data.get("seed", 42),
            now=data.get("now"),
            tenant_id=data.get("tenant_id", "default"),
            env=data.get("env", {})
        )


def freeze_time(iso_string: str) -> datetime:
    """Parse ISO8601 string to datetime."""
    return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))


def canonical_json(obj: Any) -> str:
    """
    Serialize object to canonical JSON (sorted keys, compact).

    This ensures identical objects produce identical byte output.
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), default=str)


def hash_trace(trace: Dict[str, Any]) -> str:
    """
    Compute deterministic hash of a trace.

    Used for replay verification and audit.
    """
    canonical = canonical_json(trace)
    return hashlib.sha256(canonical.encode()).hexdigest()
