# Layer: L6 — Domain Driver
# AUDIENCE: INTERNAL
# Role: Retrieves memories and builds context for planners.
# Memory Retriever
# Retrieves and formats memories for planner context

import logging
from typing import Any, Dict, List, Optional

from .store import PostgresMemoryStore, get_memory_store

logger = logging.getLogger("nova.memory.retriever")


class MemoryRetriever:
    """Retrieves memories and builds context for planners.

    Combines recent memories, relevant searches, and run history
    to build a context summary for planning.
    """

    def __init__(
        self,
        store: Optional[PostgresMemoryStore] = None,
        max_memories: int = 10,
        max_context_chars: int = 3000,
    ):
        """Initialize retriever.

        Args:
            store: Memory store instance (uses default if not provided)
            max_memories: Maximum memories to include
            max_context_chars: Maximum characters for context
        """
        self.store = store or get_memory_store()
        self.max_memories = max_memories
        self.max_context_chars = max_context_chars

    def get_context_for_planning(
        self,
        agent_id: str,
        goal: str,
        current_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get context for planner, including memories and summary.

        Args:
            agent_id: Agent to get context for
            goal: Current goal (used for relevance search)
            current_run_id: Current run ID to exclude

        Returns:
            Dict with 'context_summary' and 'memory_snippets'
        """
        logger.debug("retrieving_context", extra={"agent_id": agent_id, "goal": goal[:50]})

        # Get recent memories
        recent = self.store.get_recent_for_context(
            agent_id=agent_id,
            run_id=current_run_id,
            limit=self.max_memories,
            max_chars=self.max_context_chars // 2,
        )

        # Search for goal-relevant memories
        relevant = []
        if goal:
            # Extract keywords from goal for search
            keywords = self._extract_keywords(goal)
            for keyword in keywords[:3]:  # Limit searches
                matches = self.store.search(
                    agent_id=agent_id,
                    query=keyword,
                    limit=3,
                )
                for m in matches:
                    # Avoid duplicates
                    if m["id"] not in [r["id"] for r in relevant + recent]:
                        relevant.append(m)
                        if len(relevant) >= 5:
                            break
                if len(relevant) >= 5:
                    break

        # Combine and sort by recency
        all_memories = recent + relevant
        all_memories.sort(key=lambda x: x["created_at"], reverse=True)

        # Limit to max
        all_memories = all_memories[: self.max_memories]

        # Build context summary
        context_summary = self._build_summary(all_memories, goal)

        # Format memory snippets for planner
        memory_snippets = [
            {
                "text": m["text"][:200],
                "memory_type": m["memory_type"],
                "created_at": m["created_at"],
            }
            for m in all_memories
        ]

        logger.info(
            "context_retrieved",
            extra={
                "agent_id": agent_id,
                "memory_count": len(memory_snippets),
                "summary_len": len(context_summary),
            },
        )

        return {
            "context_summary": context_summary if context_summary else None,
            "memory_snippets": memory_snippets if memory_snippets else None,
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract search keywords from text.

        Simple extraction - can be improved with NLP later.
        """
        # Remove common words and short words
        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "dare",
            "ought",
            "used",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
            "and",
            "but",
            "or",
            "nor",
            "so",
            "yet",
            "both",
            "either",
            "neither",
            "not",
            "only",
            "own",
            "same",
            "than",
            "too",
            "very",
            "just",
            "also",
            "now",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "every",
            "both",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "any",
            "if",
            "this",
            "that",
            "these",
            "those",
            "i",
            "me",
            "my",
            "myself",
            "we",
            "our",
            "ours",
            "ourselves",
            "you",
            "your",
            "yours",
            "yourself",
            "yourselves",
            "he",
            "him",
            "his",
            "himself",
            "she",
            "her",
            "hers",
            "herself",
            "it",
            "its",
            "itself",
            "they",
            "them",
            "their",
            "theirs",
        }

        words = text.lower().split()
        keywords = []

        for word in words:
            # Clean word
            clean = "".join(c for c in word if c.isalnum())
            if len(clean) > 3 and clean not in stop_words:
                keywords.append(clean)

        # Return unique keywords
        seen = set()
        unique = []
        for k in keywords:
            if k not in seen:
                seen.add(k)
                unique.append(k)

        return unique[:10]

    def _build_summary(
        self,
        memories: List[Dict[str, Any]],
        goal: str,
    ) -> str:
        """Build a context summary from memories.

        Creates a concise summary of recent activity for the planner.
        """
        if not memories:
            return ""

        # Group by memory type
        by_type: Dict[str, List[str]] = {}
        for m in memories:
            mtype = m.get("memory_type", "general")
            if mtype not in by_type:
                by_type[mtype] = []
            by_type[mtype].append(m["text"][:100])

        # Build summary
        parts = []

        if "skill_result" in by_type:
            count = len(by_type["skill_result"])
            parts.append(f"Recent actions: {count} skill executions")

        if "user_input" in by_type:
            parts.append(f"User provided: {by_type['user_input'][0][:50]}...")

        if "context" in by_type:
            parts.append(f"Context: {by_type['context'][0][:100]}...")

        # Add most recent memory preview
        if memories:
            newest = memories[0]
            parts.append(f"Last activity: {newest['text'][:80]}...")

        return " | ".join(parts) if parts else ""


# Singleton instance
_retriever: Optional[MemoryRetriever] = None


def get_retriever() -> MemoryRetriever:
    """Get the singleton memory retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = MemoryRetriever()
    return _retriever
