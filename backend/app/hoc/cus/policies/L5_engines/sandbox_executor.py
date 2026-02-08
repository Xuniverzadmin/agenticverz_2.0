# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Product: hoc/cus/policies (execution sandboxing)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Low-level sandbox execution with process isolation
# Callers: SandboxService
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: GAP-174 (Execution Sandboxing)

"""
Sandbox Executor (GAP-174)

Provides low-level execution isolation:
- Process-based execution with resource limits
- Container-based execution (Docker/Podman)
- Network namespace isolation
- Filesystem sandboxing
"""

import asyncio
import logging
import os
import resource
import shutil
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class IsolationLevel(str, Enum):
    """Level of isolation for sandbox execution."""

    NONE = "none"  # No isolation (for trusted code)
    PROCESS = "process"  # Process-level isolation with resource limits
    CONTAINER = "container"  # Container-based isolation (Docker/Podman)
    VM = "vm"  # VM-based isolation (future)


class SandboxStatus(str, Enum):
    """Status of a sandbox execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    KILLED = "killed"


class NetworkPolicy(str, Enum):
    """Network access policy for sandboxes."""

    NONE = "none"  # No network access
    LOCAL = "local"  # Localhost only
    RESTRICTED = "restricted"  # Specific hosts/ports only
    FULL = "full"  # Full network access


@dataclass
class ResourceLimits:
    """Resource limits for sandbox execution."""

    # CPU limits
    cpu_seconds: Optional[float] = 30.0  # Max CPU time in seconds
    cpu_cores: Optional[int] = 1  # Max CPU cores

    # Memory limits
    memory_mb: int = 256  # Max memory in MB
    memory_swap_mb: Optional[int] = None  # Max swap (None = same as memory)

    # Time limits
    wall_time_seconds: float = 60.0  # Max wall clock time

    # Process limits
    max_processes: int = 10  # Max number of processes
    max_open_files: int = 100  # Max open file descriptors

    # Disk limits
    disk_mb: Optional[int] = 100  # Max disk usage in MB
    max_file_size_mb: int = 10  # Max single file size

    # Network limits
    network_policy: NetworkPolicy = NetworkPolicy.NONE
    allowed_hosts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cpu_seconds": self.cpu_seconds,
            "cpu_cores": self.cpu_cores,
            "memory_mb": self.memory_mb,
            "memory_swap_mb": self.memory_swap_mb,
            "wall_time_seconds": self.wall_time_seconds,
            "max_processes": self.max_processes,
            "max_open_files": self.max_open_files,
            "disk_mb": self.disk_mb,
            "max_file_size_mb": self.max_file_size_mb,
            "network_policy": self.network_policy.value,
            "allowed_hosts": self.allowed_hosts,
        }


@dataclass
class ExecutionResult:
    """Result of a sandbox execution."""

    sandbox_id: str
    status: SandboxStatus

    # Output
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None

    # Resource usage
    cpu_time_seconds: Optional[float] = None
    memory_peak_mb: Optional[float] = None
    wall_time_seconds: Optional[float] = None

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Error info
    error_message: Optional[str] = None
    error_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sandbox_id": self.sandbox_id,
            "status": self.status.value,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "cpu_time_seconds": self.cpu_time_seconds,
            "memory_peak_mb": self.memory_peak_mb,
            "wall_time_seconds": self.wall_time_seconds,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "error_type": self.error_type,
        }


class SandboxExecutor(ABC):
    """Abstract base class for sandbox executors."""

    @abstractmethod
    async def execute(
        self,
        code: str,
        language: str,
        limits: ResourceLimits,
        environment: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, bytes]] = None,
    ) -> ExecutionResult:
        """
        Execute code in a sandbox.

        Args:
            code: Code to execute
            language: Programming language (python, javascript, bash, etc.)
            limits: Resource limits
            environment: Environment variables
            files: Additional files to include {filename: content}

        Returns:
            ExecutionResult
        """
        pass

    @abstractmethod
    async def cleanup(self, sandbox_id: str) -> bool:
        """Clean up sandbox resources."""
        pass

    @property
    @abstractmethod
    def isolation_level(self) -> IsolationLevel:
        """Get the isolation level of this executor."""
        pass


class ProcessSandboxExecutor(SandboxExecutor):
    """
    Process-based sandbox executor.

    Uses subprocess with resource limits (rlimit) for isolation.
    Suitable for moderate security requirements.
    """

    def __init__(self):
        self._sandboxes: Dict[str, Path] = {}  # sandbox_id -> working directory

    @property
    def isolation_level(self) -> IsolationLevel:
        return IsolationLevel.PROCESS

    async def execute(
        self,
        code: str,
        language: str,
        limits: ResourceLimits,
        environment: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, bytes]] = None,
    ) -> ExecutionResult:
        """Execute code in a process sandbox."""
        import uuid

        sandbox_id = f"proc-{uuid.uuid4().hex[:12]}"
        started_at = datetime.now(timezone.utc)

        # Create temporary working directory
        work_dir = Path(tempfile.mkdtemp(prefix=f"sandbox_{sandbox_id}_"))
        self._sandboxes[sandbox_id] = work_dir

        try:
            # Write code to file
            code_file = self._write_code_file(work_dir, code, language)

            # Write additional files
            if files:
                for filename, content in files.items():
                    file_path = work_dir / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(content)

            # Get interpreter command
            cmd = self._get_interpreter_command(language, code_file)

            # Set up environment
            env = os.environ.copy()
            if environment:
                env.update(environment)

            # Execute with resource limits
            result = await self._run_with_limits(
                cmd=cmd,
                cwd=work_dir,
                env=env,
                limits=limits,
                sandbox_id=sandbox_id,
                started_at=started_at,
            )

            return result

        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            return ExecutionResult(
                sandbox_id=sandbox_id,
                status=SandboxStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error_message=str(e),
                error_type=type(e).__name__,
            )

    def _write_code_file(self, work_dir: Path, code: str, language: str) -> Path:
        """Write code to a file in the working directory."""
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "bash": ".sh",
            "shell": ".sh",
            "ruby": ".rb",
            "php": ".php",
        }
        ext = extensions.get(language.lower(), ".txt")
        code_file = work_dir / f"main{ext}"
        code_file.write_text(code)
        if language.lower() in ("bash", "shell"):
            code_file.chmod(0o755)
        return code_file

    def _get_interpreter_command(self, language: str, code_file: Path) -> List[str]:
        """Get the interpreter command for a language."""
        interpreters = {
            "python": ["python3", str(code_file)],
            "javascript": ["node", str(code_file)],
            "typescript": ["npx", "ts-node", str(code_file)],
            "bash": ["bash", str(code_file)],
            "shell": ["sh", str(code_file)],
            "ruby": ["ruby", str(code_file)],
            "php": ["php", str(code_file)],
        }
        cmd = interpreters.get(language.lower())
        if not cmd:
            raise ValueError(f"Unsupported language: {language}")
        return cmd

    async def _run_with_limits(
        self,
        cmd: List[str],
        cwd: Path,
        env: Dict[str, str],
        limits: ResourceLimits,
        sandbox_id: str,
        started_at: datetime,
    ) -> ExecutionResult:
        """Run a command with resource limits."""

        def set_limits():
            """Set resource limits in the child process."""
            # CPU time limit
            if limits.cpu_seconds:
                soft = int(limits.cpu_seconds)
                hard = soft + 5  # Grace period
                resource.setrlimit(resource.RLIMIT_CPU, (soft, hard))

            # Memory limit
            mem_bytes = limits.memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))

            # File size limit
            file_bytes = limits.max_file_size_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_bytes, file_bytes))

            # Process limit
            resource.setrlimit(
                resource.RLIMIT_NPROC, (limits.max_processes, limits.max_processes)
            )

            # Open files limit
            resource.setrlimit(
                resource.RLIMIT_NOFILE, (limits.max_open_files, limits.max_open_files)
            )

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=set_limits,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=limits.wall_time_seconds,
                )

                completed_at = datetime.now(timezone.utc)
                wall_time = (completed_at - started_at).total_seconds()

                return ExecutionResult(
                    sandbox_id=sandbox_id,
                    status=SandboxStatus.COMPLETED if process.returncode == 0 else SandboxStatus.FAILED,
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    exit_code=process.returncode,
                    wall_time_seconds=wall_time,
                    started_at=started_at,
                    completed_at=completed_at,
                )

            except asyncio.TimeoutError:
                # Kill the process
                process.kill()
                await process.wait()

                return ExecutionResult(
                    sandbox_id=sandbox_id,
                    status=SandboxStatus.TIMEOUT,
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc),
                    wall_time_seconds=limits.wall_time_seconds,
                    error_message=f"Execution timed out after {limits.wall_time_seconds} seconds",
                    error_type="TimeoutError",
                )

        except Exception as e:
            return ExecutionResult(
                sandbox_id=sandbox_id,
                status=SandboxStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error_message=str(e),
                error_type=type(e).__name__,
            )

    async def cleanup(self, sandbox_id: str) -> bool:
        """Clean up sandbox working directory."""
        work_dir = self._sandboxes.pop(sandbox_id, None)
        if work_dir and work_dir.exists():
            try:
                shutil.rmtree(work_dir)
                return True
            except Exception as e:
                logger.warning(f"Failed to cleanup sandbox {sandbox_id}: {e}")
        return False


class ContainerSandboxExecutor(SandboxExecutor):
    """
    Container-based sandbox executor.

    Uses Docker or Podman for stronger isolation.
    Suitable for high security requirements.
    """

    def __init__(
        self,
        runtime: str = "docker",
        default_image: str = "python:3.11-slim",
    ):
        self._runtime = runtime
        self._default_image = default_image
        self._containers: Dict[str, str] = {}  # sandbox_id -> container_id

    @property
    def isolation_level(self) -> IsolationLevel:
        return IsolationLevel.CONTAINER

    async def execute(
        self,
        code: str,
        language: str,
        limits: ResourceLimits,
        environment: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, bytes]] = None,
    ) -> ExecutionResult:
        """Execute code in a container sandbox."""
        import uuid

        sandbox_id = f"cont-{uuid.uuid4().hex[:12]}"
        started_at = datetime.now(timezone.utc)

        # Create temporary directory for code
        work_dir = Path(tempfile.mkdtemp(prefix=f"sandbox_{sandbox_id}_"))

        try:
            # Write code to file
            code_file = self._write_code_file(work_dir, code, language)

            # Write additional files
            if files:
                for filename, content in files.items():
                    file_path = work_dir / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(content)

            # Get image for language
            image = self._get_image_for_language(language)

            # Build container run command
            cmd = self._build_container_command(
                image=image,
                work_dir=work_dir,
                code_file=code_file,
                language=language,
                limits=limits,
                environment=environment,
                sandbox_id=sandbox_id,
            )

            # Run container
            result = await self._run_container(
                cmd=cmd,
                limits=limits,
                sandbox_id=sandbox_id,
                started_at=started_at,
            )

            return result

        except Exception as e:
            logger.error(f"Container sandbox execution error: {e}")
            return ExecutionResult(
                sandbox_id=sandbox_id,
                status=SandboxStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error_message=str(e),
                error_type=type(e).__name__,
            )

        finally:
            # Cleanup temp directory
            if work_dir.exists():
                shutil.rmtree(work_dir, ignore_errors=True)

    def _write_code_file(self, work_dir: Path, code: str, language: str) -> Path:
        """Write code to a file in the working directory."""
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "bash": ".sh",
            "shell": ".sh",
        }
        ext = extensions.get(language.lower(), ".txt")
        code_file = work_dir / f"main{ext}"
        code_file.write_text(code)
        return code_file

    def _get_image_for_language(self, language: str) -> str:
        """Get Docker image for a language."""
        images = {
            "python": "python:3.11-slim",
            "javascript": "node:20-slim",
            "typescript": "node:20-slim",
            "bash": "alpine:latest",
            "shell": "alpine:latest",
        }
        return images.get(language.lower(), self._default_image)

    def _build_container_command(
        self,
        image: str,
        work_dir: Path,
        code_file: Path,
        language: str,
        limits: ResourceLimits,
        environment: Optional[Dict[str, str]],
        sandbox_id: str,
    ) -> List[str]:
        """Build the container run command."""
        cmd = [
            self._runtime, "run",
            "--rm",
            "--name", sandbox_id,
            # Resource limits
            f"--memory={limits.memory_mb}m",
            f"--cpus={limits.cpu_cores or 1}",
            "--pids-limit", str(limits.max_processes),
        ]

        # Network policy
        if limits.network_policy == NetworkPolicy.NONE:
            cmd.append("--network=none")

        # Mount working directory
        cmd.extend(["-v", f"{work_dir}:/workspace:ro"])
        cmd.extend(["-w", "/workspace"])

        # Environment variables
        if environment:
            for key, value in environment.items():
                cmd.extend(["-e", f"{key}={value}"])

        # Add image
        cmd.append(image)

        # Add interpreter command
        interpreter_cmds = {
            "python": ["python3", f"/workspace/{code_file.name}"],
            "javascript": ["node", f"/workspace/{code_file.name}"],
            "typescript": ["npx", "ts-node", f"/workspace/{code_file.name}"],
            "bash": ["sh", f"/workspace/{code_file.name}"],
            "shell": ["sh", f"/workspace/{code_file.name}"],
        }
        cmd.extend(interpreter_cmds.get(language.lower(), ["cat", f"/workspace/{code_file.name}"]))

        return cmd

    async def _run_container(
        self,
        cmd: List[str],
        limits: ResourceLimits,
        sandbox_id: str,
        started_at: datetime,
    ) -> ExecutionResult:
        """Run a container and capture output."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            self._containers[sandbox_id] = sandbox_id

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=limits.wall_time_seconds,
                )

                completed_at = datetime.now(timezone.utc)
                wall_time = (completed_at - started_at).total_seconds()

                return ExecutionResult(
                    sandbox_id=sandbox_id,
                    status=SandboxStatus.COMPLETED if process.returncode == 0 else SandboxStatus.FAILED,
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    exit_code=process.returncode,
                    wall_time_seconds=wall_time,
                    started_at=started_at,
                    completed_at=completed_at,
                )

            except asyncio.TimeoutError:
                # Kill the container
                await self._kill_container(sandbox_id)

                return ExecutionResult(
                    sandbox_id=sandbox_id,
                    status=SandboxStatus.TIMEOUT,
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc),
                    wall_time_seconds=limits.wall_time_seconds,
                    error_message=f"Execution timed out after {limits.wall_time_seconds} seconds",
                    error_type="TimeoutError",
                )

        except Exception as e:
            return ExecutionResult(
                sandbox_id=sandbox_id,
                status=SandboxStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error_message=str(e),
                error_type=type(e).__name__,
            )

    async def _kill_container(self, sandbox_id: str) -> None:
        """Kill a running container."""
        try:
            process = await asyncio.create_subprocess_exec(
                self._runtime, "kill", sandbox_id,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await process.wait()
        except Exception as e:
            logger.warning(f"Failed to kill container {sandbox_id}: {e}")

    async def cleanup(self, sandbox_id: str) -> bool:
        """Clean up container resources."""
        if sandbox_id in self._containers:
            try:
                # Force remove container if still exists
                process = await asyncio.create_subprocess_exec(
                    self._runtime, "rm", "-f", sandbox_id,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await process.wait()
                del self._containers[sandbox_id]
                return True
            except Exception as e:
                logger.warning(f"Failed to cleanup container {sandbox_id}: {e}")
        return False


def create_sandbox_executor(
    isolation_level: IsolationLevel = IsolationLevel.PROCESS,
    **kwargs,
) -> SandboxExecutor:
    """
    Create a sandbox executor with the specified isolation level.

    Args:
        isolation_level: Level of isolation required
        **kwargs: Additional arguments for the executor

    Returns:
        SandboxExecutor instance
    """
    if isolation_level == IsolationLevel.NONE:
        # Return process executor with no limits
        return ProcessSandboxExecutor()
    elif isolation_level == IsolationLevel.PROCESS:
        return ProcessSandboxExecutor()
    elif isolation_level == IsolationLevel.CONTAINER:
        return ContainerSandboxExecutor(**kwargs)
    else:
        raise ValueError(f"Unsupported isolation level: {isolation_level}")
