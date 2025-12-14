"""
BudgetLLM - Hard budget limits + prompt caching + safety governance for LLM API calls.

Your agent stops before you overspend - and before it goes off the rails.

Features:
- Drop-in OpenAI replacement
- Hard budget limits (daily, monthly, cumulative)
- Automatic kill-switch when limit exceeded
- Prompt caching for cost savings
- Hallucination risk scoring
- Parameter clamping (temperature, top_p, max_tokens)
- Safety enforcement (optional blocking)
"""

from budgetllm.core.client import Client, create_client
from budgetllm.core.budget import BudgetTracker, BudgetExceededError
from budgetllm.core.cache import PromptCache
from budgetllm.core.backends.memory import MemoryBackend
from budgetllm.core.backends.redis import RedisBackend
from budgetllm.core.safety import SafetyController, HighRiskOutputError

__version__ = "0.2.0"  # Bump for safety governance feature
__all__ = [
    # Core client
    "Client",
    "create_client",
    # Budget management
    "BudgetTracker",
    "BudgetExceededError",
    # Caching
    "PromptCache",
    "MemoryBackend",
    "RedisBackend",
    # Safety governance
    "SafetyController",
    "HighRiskOutputError",
]
