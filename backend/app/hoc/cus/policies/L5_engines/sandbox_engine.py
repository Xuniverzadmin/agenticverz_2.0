# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# PHASE: W2
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: sandbox_execution
#   Subscribes: none
# Data Access:
#   Reads: sandbox_config (via driver)
#   Writes: sandbox_results (via driver)
# Role: High-level sandbox engine with policy enforcement (pure business logic)
# Callers: Runtime, API routes, Skill executors
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-174 (Execution Sandboxing)
# NOTE: Renamed sandbox_service.py → sandbox_engine.py (2026-01-24) - BANNED_NAMING fix
#       Reclassified L4→L5 per HOC Topology V1

"""
Sandbox Service (GAP-174)

High-level service for managing sandbox execution:
- Policy-based isolation level selection
- Execution quota management
- Audit logging
- Result caching
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from .sandbox_executor import (
    ExecutionResult,
    IsolationLevel,
    NetworkPolicy,
    ResourceLimits,
    SandboxExecutor,
    SandboxStatus,
    create_sandbox_executor,
)

logger = logging.getLogger(__name__)


@dataclass
class SandboxPolicy:
    """Policy for sandbox execution."""

    policy_id: str
    name: str

    # Isolation settings
    isolation_level: IsolationLevel = IsolationLevel.PROCESS
    network_policy: NetworkPolicy = NetworkPolicy.NONE

    # Resource limits
    max_cpu_seconds: float = 30.0
    max_memory_mb: int = 256
    max_wall_time_seconds: float = 60.0
    max_processes: int = 10
    max_file_size_mb: int = 10

    # Language restrictions
    allowed_languages: Set[str] = field(default_factory=lambda: {"python", "javascript", "bash"})

    # Execution quotas
    max_executions_per_minute: int = 10
    max_executions_per_hour: int = 100

    # Flags
    allow_network: bool = False
    allow_file_write: bool = False
    require_approval: bool = False

    def to_resource_limits(self) -> ResourceLimits:
        """Convert policy to resource limits."""
        return ResourceLimits(
            cpu_seconds=self.max_cpu_seconds,
            memory_mb=self.max_memory_mb,
            wall_time_seconds=self.max_wall_time_seconds,
            max_processes=self.max_processes,
            max_file_size_mb=self.max_file_size_mb,
            network_policy=self.network_policy,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "isolation_level": self.isolation_level.value,
            "network_policy": self.network_policy.value,
            "max_cpu_seconds": self.max_cpu_seconds,
            "max_memory_mb": self.max_memory_mb,
            "max_wall_time_seconds": self.max_wall_time_seconds,
            "max_processes": self.max_processes,
            "max_file_size_mb": self.max_file_size_mb,
            "allowed_languages": list(self.allowed_languages),
            "max_executions_per_minute": self.max_executions_per_minute,
            "max_executions_per_hour": self.max_executions_per_hour,
            "allow_network": self.allow_network,
            "allow_file_write": self.allow_file_write,
            "require_approval": self.require_approval,
        }


@dataclass
class ExecutionRequest:
    """Request to execute code in a sandbox."""

    code: str
    language: str

    # Optional settings
    policy_id: Optional[str] = None
    environment: Optional[Dict[str, str]] = None
    files: Optional[Dict[str, bytes]] = None

    # Context
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    run_id: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionRecord:
    """Record of a sandbox execution for audit."""

    record_id: str
    sandbox_id: str
    tenant_id: Optional[str]
    user_id: Optional[str]
    run_id: Optional[str]

    # Request info
    language: str
    code_hash: str
    policy_id: str

    # Result info
    status: SandboxStatus
    exit_code: Optional[int]
    wall_time_seconds: Optional[float]

    # Timestamps
    created_at: datetime
    completed_at: Optional[datetime] = None

    # Error info
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "sandbox_id": self.sandbox_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "run_id": self.run_id,
            "language": self.language,
            "code_hash": self.code_hash,
            "policy_id": self.policy_id,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "wall_time_seconds": self.wall_time_seconds,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }


class SandboxService:
    """
    High-level sandbox service.

    Features:
    - Policy-based execution management
    - Quota enforcement
    - Audit logging
    - Multiple executor support
    """

    def __init__(self):
        self._executors: Dict[IsolationLevel, SandboxExecutor] = {}
        self._policies: Dict[str, SandboxPolicy] = {}
        self._execution_records: List[ExecutionRecord] = []
        self._quota_tracker: Dict[str, Dict[str, List[datetime]]] = {}  # tenant -> {minute: [], hour: []}
        self._setup_default_policies()

    def _setup_default_policies(self) -> None:
        """Set up default sandbox policies."""
        self._policies = {
            # Restrictive policy for untrusted code
            "restricted": SandboxPolicy(
                policy_id="restricted",
                name="Restricted",
                isolation_level=IsolationLevel.CONTAINER,
                network_policy=NetworkPolicy.NONE,
                max_cpu_seconds=10.0,
                max_memory_mb=128,
                max_wall_time_seconds=30.0,
                max_processes=5,
                allowed_languages={"python", "javascript"},
                allow_network=False,
                allow_file_write=False,
            ),
            # Standard policy for regular execution
            "standard": SandboxPolicy(
                policy_id="standard",
                name="Standard",
                isolation_level=IsolationLevel.PROCESS,
                network_policy=NetworkPolicy.NONE,
                max_cpu_seconds=30.0,
                max_memory_mb=256,
                max_wall_time_seconds=60.0,
                max_processes=10,
                allowed_languages={"python", "javascript", "bash"},
                allow_network=False,
                allow_file_write=True,
            ),
            # Permissive policy for trusted code
            "permissive": SandboxPolicy(
                policy_id="permissive",
                name="Permissive",
                isolation_level=IsolationLevel.PROCESS,
                network_policy=NetworkPolicy.LOCAL,
                max_cpu_seconds=60.0,
                max_memory_mb=512,
                max_wall_time_seconds=120.0,
                max_processes=20,
                allowed_languages={"python", "javascript", "typescript", "bash", "shell"},
                allow_network=True,
                allow_file_write=True,
            ),
            # High-security policy for sensitive operations
            "high_security": SandboxPolicy(
                policy_id="high_security",
                name="High Security",
                isolation_level=IsolationLevel.CONTAINER,
                network_policy=NetworkPolicy.NONE,
                max_cpu_seconds=5.0,
                max_memory_mb=64,
                max_wall_time_seconds=15.0,
                max_processes=3,
                allowed_languages={"python"},
                allow_network=False,
                allow_file_write=False,
                require_approval=True,
            ),
        }

    def _get_executor(self, isolation_level: IsolationLevel) -> SandboxExecutor:
        """Get or create an executor for the isolation level."""
        if isolation_level not in self._executors:
            self._executors[isolation_level] = create_sandbox_executor(isolation_level)
        return self._executors[isolation_level]

    async def execute(
        self,
        request: ExecutionRequest,
    ) -> ExecutionResult:
        """
        Execute code in a sandbox.

        Args:
            request: Execution request

        Returns:
            ExecutionResult
        """
        import hashlib
        import uuid

        # Get policy
        policy = self._get_policy(request.policy_id)

        # Validate language
        if request.language.lower() not in policy.allowed_languages:
            return ExecutionResult(
                sandbox_id=f"denied-{uuid.uuid4().hex[:8]}",
                status=SandboxStatus.FAILED,
                error_message=f"Language '{request.language}' not allowed by policy '{policy.policy_id}'",
                error_type="PolicyViolation",
            )

        # Check quota
        if request.tenant_id and not self._check_quota(request.tenant_id, policy):
            return ExecutionResult(
                sandbox_id=f"quota-{uuid.uuid4().hex[:8]}",
                status=SandboxStatus.FAILED,
                error_message="Execution quota exceeded",
                error_type="QuotaExceeded",
            )

        # Create record
        record_id = f"exec-{uuid.uuid4().hex[:12]}"
        code_hash = hashlib.sha256(request.code.encode()).hexdigest()[:16]

        # Get executor and execute
        executor = self._get_executor(policy.isolation_level)
        limits = policy.to_resource_limits()

        # Override limits from environment if provided
        if request.environment:
            if "SANDBOX_CPU_LIMIT" in request.environment:
                try:
                    limits.cpu_seconds = float(request.environment["SANDBOX_CPU_LIMIT"])
                except ValueError:
                    pass
            if "SANDBOX_MEMORY_LIMIT" in request.environment:
                try:
                    limits.memory_mb = int(request.environment["SANDBOX_MEMORY_LIMIT"])
                except ValueError:
                    pass

        created_at = datetime.now(timezone.utc)

        result = await executor.execute(
            code=request.code,
            language=request.language,
            limits=limits,
            environment=request.environment,
            files=request.files,
        )

        # Create audit record
        record = ExecutionRecord(
            record_id=record_id,
            sandbox_id=result.sandbox_id,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            run_id=request.run_id,
            language=request.language,
            code_hash=code_hash,
            policy_id=policy.policy_id,
            status=result.status,
            exit_code=result.exit_code,
            wall_time_seconds=result.wall_time_seconds,
            created_at=created_at,
            completed_at=result.completed_at,
            error_message=result.error_message,
        )
        self._execution_records.append(record)

        # Trim old records
        if len(self._execution_records) > 10000:
            self._execution_records = self._execution_records[-5000:]

        # Track quota
        if request.tenant_id:
            self._track_execution(request.tenant_id)

        # Cleanup sandbox
        await executor.cleanup(result.sandbox_id)

        logger.info(
            f"Sandbox execution: {result.sandbox_id} "
            f"status={result.status.value} "
            f"language={request.language} "
            f"policy={policy.policy_id}"
        )

        return result

    def _get_policy(self, policy_id: Optional[str]) -> SandboxPolicy:
        """Get a policy by ID, defaulting to 'standard'."""
        if policy_id and policy_id in self._policies:
            return self._policies[policy_id]
        return self._policies["standard"]

    def _check_quota(self, tenant_id: str, policy: SandboxPolicy) -> bool:
        """Check if tenant has quota remaining."""
        now = datetime.now(timezone.utc)

        if tenant_id not in self._quota_tracker:
            return True

        tracker = self._quota_tracker[tenant_id]

        # Check minute quota
        minute_key = now.strftime("%Y-%m-%d-%H-%M")
        minute_executions = tracker.get(minute_key, [])
        if len(minute_executions) >= policy.max_executions_per_minute:
            return False

        # Check hour quota
        hour_key = now.strftime("%Y-%m-%d-%H")
        hour_executions = tracker.get(hour_key, [])
        if len(hour_executions) >= policy.max_executions_per_hour:
            return False

        return True

    def _track_execution(self, tenant_id: str) -> None:
        """Track an execution for quota purposes."""
        now = datetime.now(timezone.utc)

        if tenant_id not in self._quota_tracker:
            self._quota_tracker[tenant_id] = {}

        tracker = self._quota_tracker[tenant_id]

        # Track minute
        minute_key = now.strftime("%Y-%m-%d-%H-%M")
        if minute_key not in tracker:
            tracker[minute_key] = []
        tracker[minute_key].append(now)

        # Track hour
        hour_key = now.strftime("%Y-%m-%d-%H")
        if hour_key not in tracker:
            tracker[hour_key] = []
        tracker[hour_key].append(now)

        # Cleanup old entries (keep last 2 hours)
        cutoff = now.strftime("%Y-%m-%d-") + str(max(0, int(now.strftime("%H")) - 2)).zfill(2)
        keys_to_remove = [k for k in tracker.keys() if k < cutoff]
        for key in keys_to_remove:
            del tracker[key]

    def define_policy(
        self,
        policy_id: str,
        name: str,
        **kwargs,
    ) -> SandboxPolicy:
        """
        Define a new sandbox policy.

        Args:
            policy_id: Unique identifier
            name: Human-readable name
            **kwargs: Policy parameters

        Returns:
            Created policy
        """
        policy = SandboxPolicy(
            policy_id=policy_id,
            name=name,
            **kwargs,
        )
        self._policies[policy_id] = policy
        logger.info(f"Defined sandbox policy: {policy_id}")
        return policy

    def get_policy(self, policy_id: str) -> Optional[SandboxPolicy]:
        """Get a policy by ID."""
        return self._policies.get(policy_id)

    def list_policies(self) -> Dict[str, SandboxPolicy]:
        """List all defined policies."""
        return dict(self._policies)

    def get_execution_records(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        run_id: Optional[str] = None,
        status: Optional[SandboxStatus] = None,
        limit: int = 100,
    ) -> List[ExecutionRecord]:
        """
        Get execution records with optional filtering.

        Args:
            tenant_id: Filter by tenant
            user_id: Filter by user
            run_id: Filter by run
            status: Filter by status
            limit: Maximum records to return

        Returns:
            List of execution records
        """
        records = self._execution_records

        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]
        if user_id:
            records = [r for r in records if r.user_id == user_id]
        if run_id:
            records = [r for r in records if r.run_id == run_id]
        if status:
            records = [r for r in records if r.status == status]

        return records[-limit:]

    def get_execution_stats(
        self,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get execution statistics.

        Args:
            tenant_id: Optional tenant filter

        Returns:
            Statistics dictionary
        """
        records = self._execution_records
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]

        if not records:
            return {
                "total_executions": 0,
                "by_status": {},
                "by_language": {},
                "by_policy": {},
                "avg_wall_time_seconds": 0,
            }

        by_status: Dict[str, int] = {}
        by_language: Dict[str, int] = {}
        by_policy: Dict[str, int] = {}
        total_time = 0.0
        time_count = 0

        for record in records:
            # By status
            status = record.status.value
            by_status[status] = by_status.get(status, 0) + 1

            # By language
            by_language[record.language] = by_language.get(record.language, 0) + 1

            # By policy
            by_policy[record.policy_id] = by_policy.get(record.policy_id, 0) + 1

            # Wall time
            if record.wall_time_seconds:
                total_time += record.wall_time_seconds
                time_count += 1

        return {
            "total_executions": len(records),
            "by_status": by_status,
            "by_language": by_language,
            "by_policy": by_policy,
            "avg_wall_time_seconds": total_time / time_count if time_count > 0 else 0,
        }
