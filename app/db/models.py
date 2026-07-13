"""SQLAlchemy database models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RequestLog(Base):
    """Log of every inference request for analytics and cost tracking."""

    __tablename__ = "request_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    user_id = Column(String(255), nullable=False, index=True)
    api_key_prefix = Column(String(16), nullable=True)
    provider = Column(String(64), nullable=False)
    model = Column(String(128), nullable=False, index=True)
    request_type = Column(String(32), nullable=False)  # chat, embedding

    # Routing info
    strategy = Column(String(32), nullable=True)
    fallback_used = Column(Integer, default=0)

    # Tokens & cost
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)

    # Performance
    duration_ms = Column(Float, nullable=True)
    cache_hit = Column(Integer, default=0)

    # Request metadata
    status_code = Column(Integer, nullable=True)
    error_type = Column(String(64), nullable=True)
    request_id = Column(String(64), nullable=True, index=True)

    __table_args__ = (
        Index("ix_request_logs_timestamp", "timestamp"),
        Index("ix_request_logs_user_timestamp", "user_id", "timestamp"),
    )


class User(Base):
    """Gateway users and API keys."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=True)
    api_key_hash = Column(String(255), nullable=False)
    api_key_prefix = Column(String(16), nullable=False)
    is_admin = Column(Integer, default=0)
    is_active = Column(Integer, default=1)

    # Rate limits
    rpm_limit = Column(Integer, nullable=True)
    tpm_limit = Column(Integer, nullable=True)

    # Budget
    monthly_budget_usd = Column(Float, nullable=True)


class CostAggregate(Base):
    """Pre-aggregated cost data by user/model/day for fast dashboard queries."""

    __tablename__ = "cost_aggregates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime(timezone=True), nullable=False)
    user_id = Column(String(255), nullable=False)
    provider = Column(String(64), nullable=False)
    model = Column(String(128), nullable=False)
    request_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)

    __table_args__ = (
        Index("ix_cost_aggregates_date", "date"),
        Index("ix_cost_aggregates_user_date", "user_id", "date"),
    )
