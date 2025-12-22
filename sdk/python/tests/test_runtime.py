"""
Tests for RuntimeContext determinism.
"""

from datetime import datetime, timezone

import pytest

from aos_sdk import RuntimeContext, canonical_json, freeze_time, hash_trace


class TestRuntimeContext:
    """Tests for RuntimeContext deterministic behavior."""

    def test_same_seed_same_randint(self):
        """Same seed produces identical randint sequences."""
        ctx1 = RuntimeContext(seed=42)
        ctx2 = RuntimeContext(seed=42)

        vals1 = [ctx1.randint(0, 1000) for _ in range(100)]
        vals2 = [ctx2.randint(0, 1000) for _ in range(100)]

        assert vals1 == vals2

    def test_different_seed_different_randint(self):
        """Different seeds produce different sequences."""
        ctx1 = RuntimeContext(seed=42)
        ctx2 = RuntimeContext(seed=43)

        vals1 = [ctx1.randint(0, 1000) for _ in range(100)]
        vals2 = [ctx2.randint(0, 1000) for _ in range(100)]

        assert vals1 != vals2

    def test_same_seed_same_random(self):
        """Same seed produces identical random() sequences."""
        ctx1 = RuntimeContext(seed=1337)
        ctx2 = RuntimeContext(seed=1337)

        vals1 = [ctx1.random() for _ in range(50)]
        vals2 = [ctx2.random() for _ in range(50)]

        assert vals1 == vals2

    def test_same_seed_same_choice(self):
        """Same seed produces identical choice sequences."""
        options = ["a", "b", "c", "d", "e"]

        ctx1 = RuntimeContext(seed=999)
        ctx2 = RuntimeContext(seed=999)

        vals1 = [ctx1.choice(options) for _ in range(50)]
        vals2 = [ctx2.choice(options) for _ in range(50)]

        assert vals1 == vals2

    def test_same_seed_same_uuid(self):
        """Same seed produces identical UUIDs."""
        ctx1 = RuntimeContext(seed=42)
        ctx2 = RuntimeContext(seed=42)

        uuid1 = ctx1.uuid()
        uuid2 = ctx2.uuid()

        assert uuid1 == uuid2
        assert len(uuid1) == 36  # Standard UUID length with dashes

    def test_uuid_format(self):
        """UUID has correct format."""
        ctx = RuntimeContext(seed=42)
        uuid = ctx.uuid()

        parts = uuid.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_frozen_time_string(self):
        """Timestamp from string is frozen."""
        ctx = RuntimeContext(seed=42, now="2025-01-01T12:00:00Z")

        assert ctx.timestamp() == "2025-01-01T12:00:00+00:00"
        assert ctx.now.year == 2025
        assert ctx.now.month == 1
        assert ctx.now.day == 1
        assert ctx.now.hour == 12

    def test_frozen_time_datetime(self):
        """Timestamp from datetime is frozen."""
        dt = datetime(2025, 6, 15, 8, 30, 0, tzinfo=timezone.utc)
        ctx = RuntimeContext(seed=42, now=dt)

        assert ctx.now == dt
        assert "2025-06-15" in ctx.timestamp()

    def test_rng_state_captured(self):
        """RNG state is captured as hex string."""
        ctx = RuntimeContext(seed=42)

        assert ctx.rng_state is not None
        assert len(ctx.rng_state) == 16
        assert all(c in "0123456789abcdef" for c in ctx.rng_state)

    def test_rng_state_deterministic(self):
        """Same seed produces same RNG state."""
        ctx1 = RuntimeContext(seed=42)
        ctx2 = RuntimeContext(seed=42)

        assert ctx1.rng_state == ctx2.rng_state

    def test_tenant_id_default(self):
        """Default tenant_id is 'default'."""
        ctx = RuntimeContext(seed=42)
        assert ctx.tenant_id == "default"

    def test_tenant_id_custom(self):
        """Custom tenant_id is preserved."""
        ctx = RuntimeContext(seed=42, tenant_id="tenant-001")
        assert ctx.tenant_id == "tenant-001"

    def test_to_dict_serialization(self):
        """Context serializes to dict correctly."""
        ctx = RuntimeContext(
            seed=42, now="2025-01-01T00:00:00Z", tenant_id="test", env={"FOO": "bar"}
        )

        data = ctx.to_dict()

        assert data["seed"] == 42
        assert data["tenant_id"] == "test"
        assert data["env"] == {"FOO": "bar"}
        assert "2025-01-01" in data["now"]
        assert data["rng_state"] is not None

    def test_from_dict_deserialization(self):
        """Context deserializes from dict correctly."""
        data = {
            "seed": 99,
            "now": "2025-06-15T10:00:00Z",
            "tenant_id": "restored",
            "env": {"KEY": "value"},
        }

        ctx = RuntimeContext.from_dict(data)

        assert ctx.seed == 99
        assert ctx.tenant_id == "restored"
        assert ctx.env == {"KEY": "value"}

    def test_shuffle_deterministic(self):
        """Same seed produces identical shuffle."""
        items1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        items2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        ctx1 = RuntimeContext(seed=42)
        ctx2 = RuntimeContext(seed=42)

        ctx1.shuffle(items1)
        ctx2.shuffle(items2)

        assert items1 == items2


class TestCanonicalJson:
    """Tests for canonical JSON serialization."""

    def test_key_order_independent(self):
        """Different key order produces same canonical JSON."""
        data1 = {"b": 2, "a": 1, "c": 3}
        data2 = {"a": 1, "b": 2, "c": 3}
        data3 = {"c": 3, "a": 1, "b": 2}

        json1 = canonical_json(data1)
        json2 = canonical_json(data2)
        json3 = canonical_json(data3)

        assert json1 == json2 == json3

    def test_nested_key_order(self):
        """Nested objects also have sorted keys."""
        data1 = {"outer": {"z": 26, "a": 1}}
        data2 = {"outer": {"a": 1, "z": 26}}

        json1 = canonical_json(data1)
        json2 = canonical_json(data2)

        assert json1 == json2

    def test_compact_format(self):
        """Canonical JSON is compact (no spaces)."""
        data = {"a": 1, "b": 2}
        result = canonical_json(data)

        assert " " not in result
        assert result == '{"a":1,"b":2}'

    def test_arrays_preserved(self):
        """Array order is preserved."""
        data = {"items": [3, 1, 2]}
        result = canonical_json(data)

        assert result == '{"items":[3,1,2]}'

    def test_special_types_handled(self):
        """Non-JSON types are converted via default=str."""
        from datetime import datetime

        data = {"time": datetime(2025, 1, 1)}
        result = canonical_json(data)

        assert "2025" in result


class TestHashTrace:
    """Tests for trace hashing."""

    def test_same_data_same_hash(self):
        """Identical data produces identical hash."""
        trace1 = {"seed": 42, "steps": [{"id": 1}]}
        trace2 = {"seed": 42, "steps": [{"id": 1}]}

        hash1 = hash_trace(trace1)
        hash2 = hash_trace(trace2)

        assert hash1 == hash2

    def test_different_data_different_hash(self):
        """Different data produces different hash."""
        trace1 = {"seed": 42, "steps": [{"id": 1}]}
        trace2 = {"seed": 43, "steps": [{"id": 1}]}

        hash1 = hash_trace(trace1)
        hash2 = hash_trace(trace2)

        assert hash1 != hash2

    def test_key_order_independent_hash(self):
        """Key order doesn't affect hash."""
        trace1 = {"b": 2, "a": 1}
        trace2 = {"a": 1, "b": 2}

        hash1 = hash_trace(trace1)
        hash2 = hash_trace(trace2)

        assert hash1 == hash2

    def test_hash_length(self):
        """Hash is full SHA256 (64 hex chars)."""
        trace = {"data": "test"}
        h = hash_trace(trace)

        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestFreezeTime:
    """Tests for time freezing utility."""

    def test_parse_z_suffix(self):
        """Parse ISO8601 with Z suffix."""
        dt = freeze_time("2025-01-01T00:00:00Z")

        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 1
        assert dt.tzinfo == timezone.utc

    def test_parse_offset(self):
        """Parse ISO8601 with offset."""
        dt = freeze_time("2025-06-15T12:30:00+00:00")

        assert dt.year == 2025
        assert dt.month == 6
        assert dt.day == 15
        assert dt.hour == 12
        assert dt.minute == 30


class TestDeterminismMultipleSeeds:
    """Test determinism across various seeds."""

    @pytest.mark.parametrize("seed", [0, 1, 42, 1337, 999999, 2**31 - 1])
    def test_seed_reproducibility(self, seed):
        """Each seed produces reproducible output."""
        ctx1 = RuntimeContext(seed=seed)
        ctx2 = RuntimeContext(seed=seed)

        # Generate many values
        vals1 = []
        vals2 = []
        for _ in range(100):
            vals1.append(ctx1.randint(0, 10000))
            vals1.append(ctx1.random())
            vals1.append(ctx1.uuid())

        ctx1_reset = RuntimeContext(seed=seed)
        ctx2_reset = RuntimeContext(seed=seed)

        for _ in range(100):
            vals2.append(ctx1_reset.randint(0, 10000))
            vals2.append(ctx1_reset.random())
            vals2.append(ctx1_reset.uuid())

        assert vals1 == vals2
