# M12 Multi-Agent System Module
# Production-grade multi-agent execution system for AOS
#
# Features:
# - Parallel job execution with orchestrator → workers pattern
# - SKIP LOCKED claiming for concurrent-safe distribution
# - agent_spawn and agent_invoke skills with correlation IDs
# - Redis blackboard for shared state
# - P2P messaging between agents
# - Usage-based credit billing

from .services.blackboard_service import BlackboardService, get_blackboard_service
from .services.credit_service import CreditService, get_credit_service
from .services.job_service import JobService, get_job_service
from .services.message_service import MessageService, get_message_service
from .services.registry_service import RegistryService, get_registry_service
from .services.worker_service import WorkerService, get_worker_service

__all__ = [
    "JobService",
    "get_job_service",
    "WorkerService",
    "get_worker_service",
    "BlackboardService",
    "get_blackboard_service",
    "MessageService",
    "get_message_service",
    "RegistryService",
    "get_registry_service",
    "CreditService",
    "get_credit_service",
]
