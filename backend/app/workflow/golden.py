# Golden-File Pipeline (M4)
"""
Golden-file recorder and verifier for workflow replay testing.

Provides:
1. Step-by-step recording during execution
2. HMAC signing for tamper detection
3. Replay verification against recorded golden files
4. CI-ready diffing for merge gates

Design Principles:
- Deterministic recording: same execution produces same golden file
- Signed artifacts: HMAC protects against tampering
- CI integration: diffs block merges on mismatch
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import hmac
import json
import os
import logging

from .canonicalize import canonicalize_for_golden, DEFAULT_VOLATILE_FIELDS

logger = logging.getLogger("nova.workflow.golden")


def _canonical_json(obj: Any) -> str:
    """Canonical JSON for deterministic outputs."""
    def _serializer(o: Any) -> Any:
        if hasattr(o, 'to_dict'):
            return o.to_dict()
        if hasattr(o, '__dict__'):
            return {k: v for k, v in o.__dict__.items() if not k.startswith('_')}
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} not serializable")
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), default=_serializer)


@dataclass
class GoldenEvent:
    """
    A single event in the golden file.
    """
    event_type: str  # run_start, step, run_end
    run_id: str
    timestamp: str  # ISO format (non-deterministic, excluded from hash)
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }

    def to_deterministic_dict(self) -> Dict[str, Any]:
        """Return dict without non-deterministic fields (including nested timing)."""
        # Strip volatile fields from nested data
        stripped_data = self._strip_volatile_fields(self.data)
        return {
            "event_type": self.event_type,
            "run_id": self.run_id,
            # timestamp excluded
            "data": stripped_data,
        }

    def _strip_volatile_fields(self, data: Any) -> Any:
        """Recursively strip volatile timing fields from data."""
        VOLATILE_FIELDS = {
            'duration_ms', 'latency_ms', 'timestamp', 'ts', 'created_at',
            'updated_at', 'started_at', 'ended_at', 'execution_time_ms',
            'wall_clock', 'elapsed_ms'
        }
        if isinstance(data, dict):
            return {
                k: self._strip_volatile_fields(v)
                for k, v in data.items()
                if k not in VOLATILE_FIELDS
            }
        elif isinstance(data, list):
            return [self._strip_volatile_fields(item) for item in data]
        return data


class GoldenRecorder:
    """
    Golden-file recorder for workflow replay testing.

    Records:
    - run_start: workflow spec, seed, replay mode
    - step: inputs, outputs, seed per step
    - run_end: final status

    Files:
    - {run_id}.steps.jsonl: Line-delimited JSON events
    - {run_id}.steps.jsonl.sig: HMAC signature

    Usage:
        recorder = GoldenRecorder("/path/to/golden", secret="ci-secret")
        await recorder.record_run_start(run_id, spec, seed, replay=False)
        await recorder.record_step(run_id, idx, step, result, seed)
        await recorder.record_run_end(run_id, "completed")

        # Verify
        assert recorder.verify_golden(f"{run_id}.steps.jsonl")
    """

    # Default directory mode for golden files (rwxr-x---)
    DEFAULT_DIR_MODE = 0o750
    # Default file mode for golden files (rw-r-----)
    DEFAULT_FILE_MODE = 0o640

    def __init__(
        self,
        dirpath: Optional[str] = None,
        secret: Optional[str] = None,
        dir_mode: int = DEFAULT_DIR_MODE,
        file_mode: int = DEFAULT_FILE_MODE,
    ):
        """
        Initialize golden recorder.

        Args:
            dirpath: Directory to store golden files (default: GOLDEN_DIR env or /var/lib/aos/golden)
            secret: HMAC secret for signing (default: GOLDEN_SECRET env)
            dir_mode: Directory permission mode (default: 0o750)
            file_mode: File permission mode (default: 0o640)
        """
        self.dir = dirpath or os.getenv("GOLDEN_DIR", "/var/lib/aos/golden")
        self.secret = secret or os.getenv("GOLDEN_SECRET", "")
        self.dir_mode = dir_mode
        self.file_mode = file_mode

        if not self.secret:
            logger.warning("GOLDEN_SECRET not set - using empty secret (insecure)")

        # Create directory with secure permissions
        os.makedirs(self.dir, mode=self.dir_mode, exist_ok=True)
        # Ensure permissions are correct even if dir exists
        try:
            os.chmod(self.dir, self.dir_mode)
        except OSError as e:
            logger.warning(f"Could not set golden dir permissions: {e}")

    def _filepath(self, run_id: str) -> str:
        """Get golden file path for run_id."""
        return os.path.join(self.dir, f"{run_id}.steps.jsonl")

    async def record_run_start(
        self,
        run_id: str,
        spec: "WorkflowSpec",
        seed: int,
        replay: bool,
        budget_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record workflow run start.

        Args:
            run_id: Unique run identifier
            spec: Workflow specification
            seed: Base seed for deterministic execution
            replay: Whether this is a replay run
            budget_snapshot: Deterministic budget state for replay reproducibility
        """
        data = {
            "spec_id": spec.id,
            "spec_name": spec.name,
            "spec_version": spec.version,
            "steps_count": len(spec.steps),
            "seed": seed,
            "replay": replay,
            "spec_hash": hashlib.sha256(_canonical_json(spec.to_dict()).encode()).hexdigest()[:16],
        }

        # Add budget snapshot for replay reproducibility
        if budget_snapshot:
            data["budget_snapshot"] = budget_snapshot

        event = GoldenEvent(
            event_type="run_start",
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=data,
        )
        await self._append(run_id, event)

        logger.debug(
            "golden_run_start",
            extra={"run_id": run_id, "spec_id": spec.id, "seed": seed}
        )

    async def record_step(
        self,
        run_id: str,
        step_index: int,
        step: "StepDescriptor",
        result: "StepResult",
        seed: int,
    ) -> None:
        """
        Record a step execution.

        Args:
            run_id: Unique run identifier
            step_index: Step index (0-based)
            step: Step descriptor
            result: Step execution result
            seed: Seed used for this step
        """
        # Determine canonical output
        if hasattr(result, 'to_dict'):
            output = result.to_dict()
        elif isinstance(result, dict):
            output = result
        else:
            output = {"raw": str(result)}

        # Canonicalize output for hash (excludes volatile fields like duration_ms)
        canonical_output = canonicalize_for_golden(
            output,
            ignore_fields={'duration_ms', 'latency_ms'},
            redact_sensitive=False,
        )

        # Build step event data with error_code and recovery_hint
        step_data = {
            "index": step_index,
            "step_id": step.id,
            "skill_id": step.skill_id,
            "inputs": step.inputs,
            "seed": seed,
            "success": result.success if hasattr(result, 'success') else True,
            "output": output,  # Keep full output for debugging
            "output_hash": hashlib.sha256(
                json.dumps(canonical_output, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()[:16],
        }

        # Add error_code and recovery_hint if step failed
        if hasattr(result, 'error_code') and result.error_code:
            step_data["error_code"] = result.error_code
        if hasattr(result, 'recovery_hint') and result.recovery_hint:
            step_data["recovery_hint"] = result.recovery_hint

        event = GoldenEvent(
            event_type="step",
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=step_data,
        )
        await self._append(run_id, event)

        logger.debug(
            "golden_step_recorded",
            extra={
                "run_id": run_id,
                "step_index": step_index,
                "step_id": step.id,
                "error_code": getattr(result, 'error_code', None),
            }
        )

    async def record_run_end(
        self,
        run_id: str,
        status: str,
    ) -> None:
        """
        Record workflow run end and finalize file.

        Args:
            run_id: Unique run identifier
            status: Final status (completed, failed, aborted, budget_exceeded)
        """
        event = GoldenEvent(
            event_type="run_end",
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "status": status,
            },
        )
        await self._append(run_id, event)

        # Sign the golden file
        filepath = self._filepath(run_id)
        self.sign_golden(filepath)

        logger.info(
            "golden_run_end",
            extra={"run_id": run_id, "status": status, "filepath": filepath}
        )

    async def _append(self, run_id: str, event: GoldenEvent) -> None:
        """
        Append event to golden file.

        Args:
            run_id: Unique run identifier
            event: Event to append
        """
        filepath = self._filepath(run_id)
        is_new_file = not os.path.exists(filepath)

        with open(filepath, "a", encoding="utf-8") as f:
            f.write(_canonical_json(event.to_dict()) + "\n")

        # Set secure permissions on new files
        if is_new_file:
            try:
                os.chmod(filepath, self.file_mode)
            except OSError as e:
                logger.warning(f"Could not set golden file permissions: {e}")

    def sign_golden(self, filepath: str) -> str:
        """
        Sign a golden file with HMAC using atomic write.

        Uses atomic rename pattern to prevent TOCTOU race conditions:
        1. Write signature to temp file
        2. Atomically rename temp file to final path

        Args:
            filepath: Path to golden file

        Returns:
            Signature hex string
        """
        with open(filepath, "rb") as f:
            data = f.read()

        sig = hmac.new(self.secret.encode(), data, hashlib.sha256).hexdigest()

        # Atomic write pattern: write to unique temp, then rename
        # Use PID and thread ID to ensure unique temp file per concurrent process
        import threading
        sig_path = filepath + ".sig"
        tmp_sig_path = f"{filepath}.sig.tmp.{os.getpid()}.{threading.get_ident()}"

        try:
            with open(tmp_sig_path, "w") as f:
                f.write(sig)
            # Atomic rename (POSIX guarantees atomic on same filesystem)
            os.replace(tmp_sig_path, sig_path)
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(tmp_sig_path):
                try:
                    os.remove(tmp_sig_path)
                except Exception:
                    pass
            raise

        return sig

    def verify_golden(self, filepath: str) -> bool:
        """
        Verify a golden file signature.

        Args:
            filepath: Path to golden file

        Returns:
            True if signature matches
        """
        if not os.path.exists(filepath + ".sig"):
            return False

        with open(filepath, "rb") as f:
            data = f.read()

        with open(filepath + ".sig", "r") as f:
            expected_sig = f.read().strip()

        computed_sig = hmac.new(self.secret.encode(), data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed_sig, expected_sig)

    def load_golden(self, filepath: str) -> List[GoldenEvent]:
        """
        Load golden file events.

        Args:
            filepath: Path to golden file

        Returns:
            List of GoldenEvent objects
        """
        events = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    events.append(GoldenEvent(
                        event_type=data["event_type"],
                        run_id=data["run_id"],
                        timestamp=data["timestamp"],
                        data=data["data"],
                    ))
        return events

    def compare_golden(
        self,
        actual_filepath: str,
        expected_filepath: str,
        ignore_timestamps: bool = True,
    ) -> Dict[str, Any]:
        """
        Compare two golden files.

        Args:
            actual_filepath: Path to actual golden file
            expected_filepath: Path to expected golden file
            ignore_timestamps: Ignore timestamp differences

        Returns:
            Dict with 'match' boolean and 'diffs' list
        """
        actual_events = self.load_golden(actual_filepath)
        expected_events = self.load_golden(expected_filepath)

        diffs = []

        if len(actual_events) != len(expected_events):
            diffs.append({
                "type": "event_count_mismatch",
                "actual": len(actual_events),
                "expected": len(expected_events),
            })

        for i, (actual, expected) in enumerate(zip(actual_events, expected_events)):
            if ignore_timestamps:
                actual_dict = actual.to_deterministic_dict()
                expected_dict = expected.to_deterministic_dict()
            else:
                actual_dict = actual.to_dict()
                expected_dict = expected.to_dict()

            if actual_dict != expected_dict:
                diffs.append({
                    "type": "event_mismatch",
                    "index": i,
                    "actual": actual_dict,
                    "expected": expected_dict,
                })

        return {
            "match": len(diffs) == 0,
            "diffs": diffs,
        }


class InMemoryGoldenRecorder:
    """
    In-memory golden recorder for testing.

    Same interface as GoldenRecorder but stores events in memory.
    """

    def __init__(self):
        self._events: Dict[str, List[GoldenEvent]] = {}

    async def record_run_start(
        self,
        run_id: str,
        spec: "WorkflowSpec",
        seed: int,
        replay: bool,
        budget_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        if run_id not in self._events:
            self._events[run_id] = []

        data = {
            "spec_id": spec.id,
            "spec_name": spec.name,
            "seed": seed,
            "replay": replay,
        }

        # Add budget snapshot for replay reproducibility
        if budget_snapshot:
            data["budget_snapshot"] = budget_snapshot

        event = GoldenEvent(
            event_type="run_start",
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=data,
        )
        self._events[run_id].append(event)

    async def record_step(
        self,
        run_id: str,
        step_index: int,
        step: "StepDescriptor",
        result: "StepResult",
        seed: int,
    ) -> None:
        if run_id not in self._events:
            self._events[run_id] = []

        if hasattr(result, 'to_dict'):
            output = result.to_dict()
        elif isinstance(result, dict):
            output = result
        else:
            output = {"raw": str(result)}

        # Build step data with error_code support
        step_data = {
            "index": step_index,
            "step_id": step.id,
            "skill_id": step.skill_id,
            "seed": seed,
            "success": result.success if hasattr(result, 'success') else True,
            "output": output,
        }

        # Add error_code and recovery_hint if present
        if hasattr(result, 'error_code') and result.error_code:
            step_data["error_code"] = result.error_code
        if hasattr(result, 'recovery_hint') and result.recovery_hint:
            step_data["recovery_hint"] = result.recovery_hint

        event = GoldenEvent(
            event_type="step",
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=step_data,
        )
        self._events[run_id].append(event)

    async def record_run_end(
        self,
        run_id: str,
        status: str,
    ) -> None:
        if run_id not in self._events:
            self._events[run_id] = []

        event = GoldenEvent(
            event_type="run_end",
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={"status": status},
        )
        self._events[run_id].append(event)

    def get_events(self, run_id: str) -> List[GoldenEvent]:
        return self._events.get(run_id, [])

    def clear(self):
        self._events.clear()


# Import dependencies at end to avoid circular imports
from .engine import WorkflowSpec, StepDescriptor, StepResult
