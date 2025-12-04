"""
Database models for webhook receiver.

Stores received webhooks with metadata for replay, audit, and analysis.
"""

from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    Boolean,
    Index,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Webhook(Base):
    """Stored webhook payload."""

    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Timestamp
    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Request metadata
    method = Column(String(10), nullable=False, default="POST")
    path = Column(String(512), nullable=False, index=True)
    query_string = Column(Text, nullable=True)
    content_type = Column(String(255), nullable=True)

    # Headers (stored as JSON)
    headers = Column(JSON, nullable=True)

    # Body
    body_json = Column(JSON, nullable=True)  # Parsed JSON body
    body_raw = Column(Text, nullable=True)   # Raw body for non-JSON
    body_size = Column(Integer, nullable=True)

    # Source identification
    source_ip = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(String(512), nullable=True)

    # Signature validation
    signature_header = Column(String(255), nullable=True)
    signature_valid = Column(Boolean, nullable=True)

    # Alert-specific fields (for Alertmanager)
    alertname = Column(String(255), nullable=True, index=True)
    severity = Column(String(50), nullable=True, index=True)
    status = Column(String(50), nullable=True)  # firing, resolved

    # Replay tracking
    replayed = Column(Boolean, default=False)
    replay_count = Column(Integer, default=0)

    # Retention
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    __table_args__ = (
        Index("ix_webhooks_alertname_received", "alertname", "received_at"),
        Index("ix_webhooks_path_received", "path", "received_at"),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "method": self.method,
            "path": self.path,
            "content_type": self.content_type,
            "headers": self.headers,
            "body": self.body_json or self.body_raw,
            "body_size": self.body_size,
            "source_ip": self.source_ip,
            "alertname": self.alertname,
            "severity": self.severity,
            "status": self.status,
            "signature_valid": self.signature_valid,
        }


class WebhookStats(Base):
    """Aggregated webhook statistics."""

    __tablename__ = "webhook_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Counts
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)

    # By alertname
    alertname_counts = Column(JSON, nullable=True)  # {"CostSimV2Disabled": 5, ...}

    # By path
    path_counts = Column(JSON, nullable=True)  # {"/webhook": 100, ...}


def get_engine(database_url: str):
    """Create database engine."""
    return create_engine(database_url, pool_pre_ping=True)


def get_session_factory(engine):
    """Create session factory."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine):
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
