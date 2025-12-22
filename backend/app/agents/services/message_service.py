# M12 Message Service
# P2P messaging between agents
#
# Pattern reused from M10 outbox_processor.py (80% reuse)
# M12.1: Added LISTEN/NOTIFY for low-latency message delivery

import json
import logging
import os
import select
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("nova.agents.message_service")


@dataclass
class Message:
    """Agent message entity."""

    id: UUID
    from_instance_id: str
    to_instance_id: str
    job_id: Optional[UUID]
    message_type: str
    payload: Any
    status: str
    reply_to_id: Optional[UUID]
    created_at: datetime
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]


@dataclass
class SendResult:
    """Result of sending a message."""

    success: bool
    message_id: Optional[UUID] = None
    error: Optional[str] = None


class MessageService:
    """
    P2P messaging service for M12 multi-agent system.

    Supports:
    - Direct messages between agents
    - Request-response patterns (reply_to_id)
    - Inbox queries with status filtering
    - Message acknowledgment
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url if database_url is not None else os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL required for MessageService")

        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self.Session = sessionmaker(bind=self.engine)

    def send(
        self,
        from_instance_id: str,
        to_instance_id: str,
        message_type: str,
        payload: Any,
        job_id: Optional[UUID] = None,
        reply_to_id: Optional[UUID] = None,
    ) -> SendResult:
        """
        Send a message to another agent.

        Args:
            from_instance_id: Sender instance ID
            to_instance_id: Recipient instance ID
            message_type: Type (request, response, broadcast, etc.)
            payload: Message content
            job_id: Optional job context
            reply_to_id: Optional message being replied to

        Returns:
            SendResult with message ID or error
        """
        message_id = uuid4()

        with self.Session() as session:
            try:
                session.execute(
                    text(
                        """
                        INSERT INTO agents.messages (
                            id, from_instance_id, to_instance_id, job_id,
                            message_type, payload, status, reply_to_id, created_at
                        ) VALUES (
                            :id, :from_instance_id, :to_instance_id,
                            CAST(:job_id AS UUID),
                            :message_type, CAST(:payload AS JSONB),
                            'pending', CAST(:reply_to_id AS UUID), now()
                        )
                    """
                    ),
                    {
                        "id": str(message_id),
                        "from_instance_id": from_instance_id,
                        "to_instance_id": to_instance_id,
                        "job_id": str(job_id) if job_id else None,
                        "message_type": message_type,
                        "payload": json.dumps(payload) if not isinstance(payload, str) else payload,
                        "reply_to_id": str(reply_to_id) if reply_to_id else None,
                    },
                )

                # Notify listeners about new message
                session.execute(
                    text("SELECT pg_notify(:channel, :payload)"),
                    {
                        "channel": f"msg_{to_instance_id}",
                        "payload": json.dumps(
                            {
                                "message_id": str(message_id),
                                "from": from_instance_id,
                                "type": message_type,
                            }
                        ),
                    },
                )

                session.commit()

                logger.debug(
                    "message_sent",
                    extra={
                        "message_id": str(message_id),
                        "from": from_instance_id,
                        "to": to_instance_id,
                        "type": message_type,
                    },
                )

                return SendResult(success=True, message_id=message_id)

            except Exception as e:
                session.rollback()
                logger.error(f"Send message failed: {e}")
                return SendResult(success=False, error=str(e)[:200])

    def get_inbox(
        self,
        instance_id: str,
        status: Optional[str] = None,
        message_type: Optional[str] = None,
        job_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[Message]:
        """
        Get messages for an agent.

        Args:
            instance_id: Agent instance ID
            status: Filter by status (pending, delivered, read)
            message_type: Filter by type
            job_id: Filter by job context
            limit: Max messages to return

        Returns:
            List of messages
        """
        with self.Session() as session:
            query = """
                SELECT
                    id, from_instance_id, to_instance_id, job_id,
                    message_type, payload, status, reply_to_id,
                    created_at, delivered_at, read_at
                FROM agents.messages
                WHERE to_instance_id = :instance_id
            """
            params: Dict[str, Any] = {
                "instance_id": instance_id,
                "limit": limit,
            }

            if status:
                query += " AND status = :status"
                params["status"] = status

            if message_type:
                query += " AND message_type = :message_type"
                params["message_type"] = message_type

            if job_id:
                query += " AND job_id = :job_id"
                params["job_id"] = str(job_id)

            query += " ORDER BY created_at DESC LIMIT :limit"

            result = session.execute(text(query), params)
            messages = []

            for row in result:
                messages.append(
                    Message(
                        id=UUID(str(row[0])),
                        from_instance_id=row[1],
                        to_instance_id=row[2],
                        job_id=UUID(str(row[3])) if row[3] else None,
                        message_type=row[4],
                        payload=row[5],
                        status=row[6],
                        reply_to_id=UUID(str(row[7])) if row[7] else None,
                        created_at=row[8],
                        delivered_at=row[9],
                        read_at=row[10],
                    )
                )

            return messages

    def get_message(self, message_id: UUID) -> Optional[Message]:
        """Get a specific message by ID."""
        with self.Session() as session:
            result = session.execute(
                text(
                    """
                    SELECT
                        id, from_instance_id, to_instance_id, job_id,
                        message_type, payload, status, reply_to_id,
                        created_at, delivered_at, read_at
                    FROM agents.messages
                    WHERE id = :message_id
                """
                ),
                {"message_id": str(message_id)},
            )
            row = result.fetchone()

            if not row:
                return None

            return Message(
                id=UUID(str(row[0])),
                from_instance_id=row[1],
                to_instance_id=row[2],
                job_id=UUID(str(row[3])) if row[3] else None,
                message_type=row[4],
                payload=row[5],
                status=row[6],
                reply_to_id=UUID(str(row[7])) if row[7] else None,
                created_at=row[8],
                delivered_at=row[9],
                read_at=row[10],
            )

    def mark_delivered(self, message_id: UUID) -> bool:
        """Mark message as delivered."""
        with self.Session() as session:
            try:
                result = session.execute(
                    text(
                        """
                        UPDATE agents.messages
                        SET status = 'delivered', delivered_at = now()
                        WHERE id = :message_id AND status = 'pending'
                        RETURNING id
                    """
                    ),
                    {"message_id": str(message_id)},
                )
                row = result.fetchone()
                session.commit()
                return row is not None
            except Exception as e:
                session.rollback()
                logger.error(f"Mark delivered failed: {e}")
                return False

    def mark_read(self, message_id: UUID) -> bool:
        """Mark message as read."""
        with self.Session() as session:
            try:
                result = session.execute(
                    text(
                        """
                        UPDATE agents.messages
                        SET status = 'read', read_at = now()
                        WHERE id = :message_id AND status IN ('pending', 'delivered')
                        RETURNING id
                    """
                    ),
                    {"message_id": str(message_id)},
                )
                row = result.fetchone()
                session.commit()
                return row is not None
            except Exception as e:
                session.rollback()
                logger.error(f"Mark read failed: {e}")
                return False

    def get_replies(
        self,
        original_message_id: UUID,
        timeout_ms: int = 30000,
    ) -> List[Message]:
        """
        Get replies to a message.

        Used for request-response patterns.

        Args:
            original_message_id: Original message ID
            timeout_ms: Timeout in milliseconds (not used in poll mode)

        Returns:
            List of reply messages
        """
        with self.Session() as session:
            result = session.execute(
                text(
                    """
                    SELECT
                        id, from_instance_id, to_instance_id, job_id,
                        message_type, payload, status, reply_to_id,
                        created_at, delivered_at, read_at
                    FROM agents.messages
                    WHERE reply_to_id = :original_message_id
                    ORDER BY created_at
                """
                ),
                {"original_message_id": str(original_message_id)},
            )

            messages = []
            for row in result:
                messages.append(
                    Message(
                        id=UUID(str(row[0])),
                        from_instance_id=row[1],
                        to_instance_id=row[2],
                        job_id=UUID(str(row[3])) if row[3] else None,
                        message_type=row[4],
                        payload=row[5],
                        status=row[6],
                        reply_to_id=UUID(str(row[7])) if row[7] else None,
                        created_at=row[8],
                        delivered_at=row[9],
                        read_at=row[10],
                    )
                )

            return messages

    def wait_for_message(
        self,
        instance_id: str,
        timeout_seconds: float = 30.0,
        message_type: Optional[str] = None,
    ) -> Optional[Message]:
        """
        Wait for a new message using PostgreSQL LISTEN/NOTIFY.

        This provides sub-second latency compared to polling.

        Args:
            instance_id: Agent instance to wait for messages
            timeout_seconds: How long to wait
            message_type: Optional filter by message type

        Returns:
            Message if received, None on timeout
        """
        channel = f"msg_{instance_id}"

        try:
            # Use raw psycopg2 connection for LISTEN
            conn = psycopg2.connect(self.database_url)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute(f"LISTEN {channel}")

            # Wait for notification
            if select.select([conn], [], [], timeout_seconds) == ([], [], []):
                # Timeout - check for any pending messages anyway
                cur.close()
                conn.close()
                messages = self.get_inbox(instance_id, status="pending", message_type=message_type, limit=1)
                return messages[0] if messages else None

            # Got notification - fetch the message
            conn.poll()
            notifications = conn.notifies

            cur.close()
            conn.close()

            if notifications:
                # Fetch the actual message
                messages = self.get_inbox(instance_id, status="pending", message_type=message_type, limit=1)
                return messages[0] if messages else None

            return None

        except Exception as e:
            logger.error(f"wait_for_message failed: {e}")
            # Fallback to simple query
            messages = self.get_inbox(instance_id, status="pending", message_type=message_type, limit=1)
            return messages[0] if messages else None

    def wait_for_reply(
        self,
        original_message_id: UUID,
        timeout_seconds: float = 30.0,
    ) -> Optional[Message]:
        """
        Wait for a reply to a specific message using LISTEN/NOTIFY.

        Args:
            original_message_id: Message to wait for reply to
            timeout_seconds: How long to wait

        Returns:
            Reply message if received, None on timeout
        """
        try:
            # First check if reply already exists
            replies = self.get_replies(original_message_id)
            if replies:
                return replies[0]

            # Get the original message to find receiver instance
            orig = self.get_message(original_message_id)
            if not orig:
                return None

            # Listen on the sender's channel for reply
            channel = f"msg_{orig.from_instance_id}"

            conn = psycopg2.connect(self.database_url)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute(f"LISTEN {channel}")

            start_time = datetime.now(timezone.utc)
            deadline = start_time.timestamp() + timeout_seconds

            while datetime.now(timezone.utc).timestamp() < deadline:
                remaining = deadline - datetime.now(timezone.utc).timestamp()
                if remaining <= 0:
                    break

                if select.select([conn], [], [], min(remaining, 1.0)) != ([], [], []):
                    conn.poll()
                    # Check for reply
                    replies = self.get_replies(original_message_id)
                    if replies:
                        cur.close()
                        conn.close()
                        return replies[0]

            cur.close()
            conn.close()

            # Final check
            replies = self.get_replies(original_message_id)
            return replies[0] if replies else None

        except Exception as e:
            logger.error(f"wait_for_reply failed: {e}")
            # Fallback to simple poll
            replies = self.get_replies(original_message_id)
            return replies[0] if replies else None

    def cleanup_old_messages(
        self,
        older_than_hours: int = 24,
    ) -> int:
        """
        Delete old messages (read or failed).

        Args:
            older_than_hours: Delete messages older than this

        Returns:
            Number of messages deleted
        """
        with self.Session() as session:
            try:
                result = session.execute(
                    text(
                        """
                        DELETE FROM agents.messages
                        WHERE status = 'read'
                          AND created_at < now() - make_interval(hours => :hours)
                        RETURNING id
                    """
                    ),
                    {"hours": older_than_hours},
                )
                deleted = len(result.fetchall())
                session.commit()

                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} old messages")

                return deleted

            except Exception as e:
                session.rollback()
                logger.error(f"Message cleanup failed: {e}")
                return 0


# Singleton instance
_service: Optional[MessageService] = None


def get_message_service() -> MessageService:
    """Get singleton message service instance."""
    global _service
    if _service is None:
        _service = MessageService()
    return _service
