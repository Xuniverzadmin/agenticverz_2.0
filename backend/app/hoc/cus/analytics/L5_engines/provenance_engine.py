# Layer: L5 — Domain Engine
# NOTE: Renamed provenance.py → provenance_engine.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via provenance_async (L6)
#   Writes: via provenance_async (L6)
# Role: CostSim V2 provenance logging (full audit trail)
# Callers: sandbox engine
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470

# CostSim V2 Provenance Logging (M6)
"""
Full provenance logging for CostSim V2 sandbox.

Logs:
- input_hash: SHA256 of input
- output_hash: SHA256 of output
- input_json: Full input (optionally compressed)
- output_json: Full output (optionally compressed)
- model_version: V2 model version
- adapter_version: Adapter version
- commit_sha: Git commit
- runtime_ms: Execution time
- status: success/error/schema_error
- tenant_id: Tenant if present
"""

from __future__ import annotations

import asyncio
import base64
import gzip
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.costsim.config import get_commit_sha, get_config

logger = logging.getLogger("nova.costsim.provenance")


@dataclass
class ProvenanceLog:
    """Single provenance log entry."""

    id: str
    timestamp: datetime

    # Hashes
    input_hash: str
    output_hash: str

    # Full payloads (may be compressed)
    input_json: str
    output_json: str
    compressed: bool = False

    # Versioning
    model_version: str = "2.0.0"
    adapter_version: str = "2.0.0"
    commit_sha: str = "unknown"

    # Execution info
    runtime_ms: int = 0
    status: str = "success"  # success, error, timeout, schema_error

    # Context
    tenant_id: Optional[str] = None
    run_id: Optional[str] = None
    plan_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "input_json": self.input_json,
            "output_json": self.output_json,
            "compressed": self.compressed,
            "model_version": self.model_version,
            "adapter_version": self.adapter_version,
            "commit_sha": self.commit_sha,
            "runtime_ms": self.runtime_ms,
            "status": self.status,
            "tenant_id": self.tenant_id,
            "run_id": self.run_id,
            "plan_hash": self.plan_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvenanceLog":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            input_hash=data["input_hash"],
            output_hash=data["output_hash"],
            input_json=data["input_json"],
            output_json=data["output_json"],
            compressed=data.get("compressed", False),
            model_version=data.get("model_version", "2.0.0"),
            adapter_version=data.get("adapter_version", "2.0.0"),
            commit_sha=data.get("commit_sha", "unknown"),
            runtime_ms=data.get("runtime_ms", 0),
            status=data.get("status", "success"),
            tenant_id=data.get("tenant_id"),
            run_id=data.get("run_id"),
            plan_hash=data.get("plan_hash"),
        )

    def get_decompressed_input(self) -> Dict[str, Any]:
        """Get decompressed input JSON."""
        if self.compressed:
            decoded = base64.b64decode(self.input_json)
            decompressed = gzip.decompress(decoded)
            return json.loads(decompressed)
        return json.loads(self.input_json)

    def get_decompressed_output(self) -> Dict[str, Any]:
        """Get decompressed output JSON."""
        if self.compressed:
            decoded = base64.b64decode(self.output_json)
            decompressed = gzip.decompress(decoded)
            return json.loads(decompressed)
        return json.loads(self.output_json)


def compute_hash(data: Any) -> str:
    """Compute SHA256 hash of data."""
    if isinstance(data, dict) or isinstance(data, list):
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    else:
        canonical = str(data)
    return hashlib.sha256(canonical.encode()).hexdigest()


def compress_json(data: Any) -> str:
    """Compress JSON data to base64-encoded gzip."""
    json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
    compressed = gzip.compress(json_str.encode())
    return base64.b64encode(compressed).decode()


class ProvenanceLogger:
    """
    Logger for CostSim V2 provenance.

    Stores provenance logs for every V2 simulation for:
    - Audit trail
    - Debugging
    - Drift analysis
    - Replay capability
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        db_enabled: bool = True,
        file_enabled: bool = True,
    ):
        """
        Initialize provenance logger.

        Args:
            storage_path: Path for file-based storage
            db_enabled: Enable database storage
            file_enabled: Enable file-based storage
        """
        config = get_config()
        self.storage_path = Path(storage_path or config.artifacts_dir) / "provenance"
        self.db_enabled = db_enabled
        self.file_enabled = file_enabled
        self.compress = config.provenance_compress

        # Ensure storage directory exists
        if self.file_enabled:
            self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory buffer for batch writes
        self._buffer: List[ProvenanceLog] = []
        self._buffer_size = 100
        self._lock = asyncio.Lock()

    async def log(
        self,
        input_data: Any,
        output_data: Any,
        runtime_ms: int,
        status: str = "success",
        tenant_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> ProvenanceLog:
        """
        Log a provenance entry.

        Args:
            input_data: Simulation input (plan)
            output_data: Simulation output (result)
            runtime_ms: Execution time in milliseconds
            status: Execution status
            tenant_id: Tenant identifier
            run_id: Run identifier

        Returns:
            Created ProvenanceLog
        """
        config = get_config()

        # Compute hashes
        input_hash = compute_hash(input_data)
        output_hash = compute_hash(output_data)

        # Prepare JSON payloads
        if self.compress:
            input_json = compress_json(input_data)
            output_json = compress_json(output_data)
            compressed = True
        else:
            input_json = json.dumps(input_data, sort_keys=True)
            output_json = json.dumps(output_data, sort_keys=True)
            compressed = False

        # Create log entry
        log_entry = ProvenanceLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            input_hash=input_hash,
            output_hash=output_hash,
            input_json=input_json,
            output_json=output_json,
            compressed=compressed,
            model_version=config.model_version,
            adapter_version=config.adapter_version,
            commit_sha=get_commit_sha(),
            runtime_ms=runtime_ms,
            status=status,
            tenant_id=tenant_id,
            run_id=run_id,
            plan_hash=input_hash[:16],
        )

        # Store
        await self._store(log_entry)

        return log_entry

    async def _store(self, log_entry: ProvenanceLog) -> None:
        """Store a provenance log entry."""
        async with self._lock:
            self._buffer.append(log_entry)

            if len(self._buffer) >= self._buffer_size:
                await self._flush()

    async def _flush(self) -> None:
        """Flush buffer to storage."""
        if not self._buffer:
            return

        entries = self._buffer.copy()
        self._buffer.clear()

        # File storage
        if self.file_enabled:
            await self._write_to_file(entries)

        # Database storage (if enabled)
        if self.db_enabled:
            await self._write_to_db(entries)

    async def _write_to_file(self, entries: List[ProvenanceLog]) -> None:
        """Write entries to file storage."""
        try:
            # Group by date
            by_date: Dict[str, List[ProvenanceLog]] = {}
            for entry in entries:
                date_str = entry.timestamp.strftime("%Y-%m-%d")
                if date_str not in by_date:
                    by_date[date_str] = []
                by_date[date_str].append(entry)

            # Write to date-partitioned files
            for date_str, date_entries in by_date.items():
                file_path = self.storage_path / f"provenance_{date_str}.jsonl"
                with open(file_path, "a") as f:
                    for entry in date_entries:
                        f.write(json.dumps(entry.to_dict()) + "\n")

        except Exception as e:
            logger.error(f"Failed to write provenance to file: {e}")

    async def _write_to_db(self, entries: List[ProvenanceLog]) -> None:
        """Write entries to database."""
        # TODO: Implement database storage
        # For now, file storage is primary
        pass

    async def close(self) -> None:
        """Flush remaining entries and close."""
        async with self._lock:
            await self._flush()

    async def query(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        input_hash: Optional[str] = None,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ProvenanceLog]:
        """
        Query provenance logs.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            input_hash: Filter by input hash
            status: Filter by status
            tenant_id: Filter by tenant
            limit: Maximum results

        Returns:
            List of matching ProvenanceLog entries
        """
        results: List[ProvenanceLog] = []

        # Scan files
        if self.file_enabled:
            for file_path in sorted(self.storage_path.glob("provenance_*.jsonl"), reverse=True):
                if len(results) >= limit:
                    break

                try:
                    with open(file_path, "r") as f:
                        for line in f:
                            if len(results) >= limit:
                                break

                            entry = ProvenanceLog.from_dict(json.loads(line))

                            # Apply filters
                            if start_date and entry.timestamp < start_date:
                                continue
                            if end_date and entry.timestamp > end_date:
                                continue
                            if input_hash and entry.input_hash != input_hash:
                                continue
                            if status and entry.status != status:
                                continue
                            if tenant_id and entry.tenant_id != tenant_id:
                                continue

                            results.append(entry)

                except Exception as e:
                    logger.error(f"Failed to read provenance file {file_path}: {e}")

        return results


# Global logger instance
_provenance_logger: Optional[ProvenanceLogger] = None


def get_provenance_logger() -> ProvenanceLogger:
    """Get the global provenance logger."""
    global _provenance_logger
    if _provenance_logger is None:
        _provenance_logger = ProvenanceLogger()
    return _provenance_logger
