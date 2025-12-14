"""
BudgetLLM - Hard budget limits + prompt caching for LLM API calls.

Your agent stops before you overspend.
"""

from budgetllm.core.client import Client, create_client
from budgetllm.core.budget import BudgetTracker, BudgetExceededError
from budgetllm.core.cache import PromptCache
from budgetllm.core.backends.memory import MemoryBackend
from budgetllm.core.backends.redis import RedisBackend

__version__ = "0.1.0"
__all__ = [
    "Client",
    "create_client",
    "BudgetTracker",
    "BudgetExceededError",
    "PromptCache",
    "MemoryBackend",
    "RedisBackend",
]
