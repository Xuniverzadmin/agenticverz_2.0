# Layer: L6 — Domain Driver
# AUDIENCE: INTERNAL
# Role: Protocol for memory storage backends.
# capability_id: CAP-014
# Memory Store
# Provides storage interface for agent memories

import logging
from typing import Any, Dict, List, Optional, Protocol, cast

from sqlmodel import Session, desc, select

from app.db import Memory, engine

logger = logging.getLogger("nova.memory.store")


class MemoryStore(Protocol):
    """Protocol for memory storage backends."""

    def store(
        self,
        agent_id: str,
        text: str,
        memory_type: str = "general",
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a memory and return its ID."""
        ...

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a memory by ID."""
        ...

    def list_by_agent(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List memories for an agent."""
        ...

    def search(
        self,
        agent_id: str,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search memories by text similarity."""
        ...

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        ...


class PostgresMemoryStore:
    """PostgreSQL-backed memory store using SQLModel.

    Uses the existing Memory table for storage.
    """

    def __init__(self):
        logger.info("PostgresMemoryStore initialized")

    def store(
        self,
        agent_id: str,
        text: str,
        memory_type: str = "general",
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a memory and return its ID."""
        import json

        with Session(engine) as session:
            memory = Memory(
                agent_id=agent_id,
                text=text,
                memory_type=memory_type,
                meta=json.dumps(meta) if meta else None,
            )
            session.add(memory)
            session.commit()
            session.refresh(memory)

            logger.debug(
                "memory_stored",
                extra={
                    "memory_id": memory.id,
                    "agent_id": agent_id,
                    "memory_type": memory_type,
                    "text_len": len(text),
                },
            )

            return memory.id

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a memory by ID."""
        import json

        with Session(engine) as session:
            memory = session.get(Memory, memory_id)
            if not memory:
                return None

            return {
                "id": memory.id,
                "agent_id": memory.agent_id,
                "text": memory.text,
                "memory_type": memory.memory_type,
                "meta": json.loads(memory.meta) if memory.meta else None,
                "created_at": memory.created_at.isoformat(),
            }

    def list_by_agent(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List memories for an agent, newest first."""
        import json

        with Session(engine) as session:
            query = select(Memory).where(Memory.agent_id == agent_id)

            if memory_type:
                query = query.where(Memory.memory_type == memory_type)

            query = query.order_by(desc(Memory.created_at)).offset(offset).limit(limit)

            memories = session.exec(query).all()

            return [
                {
                    "id": m.id,
                    "agent_id": m.agent_id,
                    "text": m.text,
                    "memory_type": m.memory_type,
                    "meta": json.loads(m.meta) if m.meta else None,
                    "created_at": m.created_at.isoformat(),
                }
                for m in memories
            ]

    def search(
        self,
        agent_id: str,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search memories by text similarity.

        Currently uses simple LIKE matching. Can be upgraded to
        full-text search or vector similarity later.
        """
        import json

        with Session(engine) as session:
            # Simple case-insensitive search
            search_pattern = f"%{query}%"

            stmt = (
                select(Memory)
                .where(Memory.agent_id == agent_id)
                .where(cast(Any, Memory.text).ilike(search_pattern))
                .order_by(desc(Memory.created_at))
                .limit(limit)
            )

            memories = session.exec(stmt).all()

            logger.debug(
                "memory_search",
                extra={
                    "agent_id": agent_id,
                    "query": query[:50],
                    "results": len(memories),
                },
            )

            return [
                {
                    "id": m.id,
                    "agent_id": m.agent_id,
                    "text": m.text,
                    "memory_type": m.memory_type,
                    "meta": json.loads(m.meta) if m.meta else None,
                    "created_at": m.created_at.isoformat(),
                }
                for m in memories
            ]

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        with Session(engine) as session:
            memory = session.get(Memory, memory_id)
            if not memory:
                return False

            session.delete(memory)
            session.commit()

            logger.debug("memory_deleted", extra={"memory_id": memory_id})
            return True

    def get_recent_for_context(
        self,
        agent_id: str,
        run_id: Optional[str] = None,
        limit: int = 10,
        max_chars: int = 2000,
    ) -> List[Dict[str, Any]]:
        """Get recent memories formatted for context injection.

        Args:
            agent_id: Agent to get memories for
            run_id: Optionally exclude memories from current run
            limit: Max number of memories
            max_chars: Max total characters across all memories

        Returns:
            List of memory dicts, newest first, within char limit
        """
        import json

        with Session(engine) as session:
            query = (
                select(Memory)
                .where(Memory.agent_id == agent_id)
                .order_by(desc(Memory.created_at))
                .limit(limit * 2)  # Fetch extra to filter
            )

            memories = session.exec(query).all()

            # Filter and limit by char count
            result = []
            total_chars = 0

            for m in memories:
                # Skip memories from current run if specified
                if run_id and m.meta:
                    try:
                        meta = json.loads(m.meta)
                        if meta.get("run_id") == run_id:
                            continue
                    except Exception:
                        pass

                text_len = len(m.text)
                if total_chars + text_len > max_chars:
                    break

                result.append(
                    {
                        "id": m.id,
                        "text": m.text,
                        "memory_type": m.memory_type,
                        "meta": json.loads(m.meta) if m.meta else None,
                        "created_at": m.created_at.isoformat(),
                    }
                )
                total_chars += text_len

                if len(result) >= limit:
                    break

            return result


# Singleton instance
_store: Optional[PostgresMemoryStore] = None


def get_memory_store() -> PostgresMemoryStore:
    """Get the singleton memory store instance."""
    global _store
    if _store is None:
        _store = PostgresMemoryStore()
    return _store
