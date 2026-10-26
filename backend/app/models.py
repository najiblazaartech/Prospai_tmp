import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), default="")
    plan = Column(String(50), default="starter")
    is_active = Column(Boolean, default=True)

    workspaces = relationship("WorkspaceMember", back_populates="user")


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    manual_review = Column(Boolean, default=True)
    credits_remaining = Column(Integer, default=1000)
    max_daily_linkedin_actions = Column(Integer, default=80)

    campaigns = relationship("Campaign", back_populates="workspace")
    leads = relationship("Lead", back_populates="workspace")
    members = relationship("WorkspaceMember", back_populates="workspace")
    email_accounts = relationship("EmailAccount", back_populates="workspace")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    role = Column(String(50), default="owner")

    user = relationship("User", back_populates="workspaces")
    workspace = relationship("Workspace", back_populates="members")


class EmailAccount(Base, TimestampMixin):
    """Boite d'envoi pour le cold email (SMTP gratuit : Gmail app-password, Brevo...)."""
    __tablename__ = "email_accounts"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    smtp_host = Column(String(255), nullable=False)     # ex : smtp.gmail.com
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(255), nullable=False)
    smtp_password = Column(String(255), nullable=False)  # app-password, jamais le mot de passe principal
    sender_name = Column(String(255), default="")
    daily_limit = Column(Integer, default=30)           # anti-spam au demarrage
    warmup_until = Column(DateTime, nullable=True)     # periode de warm-up
    is_active = Column(Boolean, default=True)

    workspace = relationship("Workspace", back_populates="email_accounts")


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="active")
    prompt = Column(Text, default="")

    workspace = relationship("Workspace", back_populates="campaigns")
    steps = relationship("SequenceStep", back_populates="campaign", order_by="SequenceStep.day_offset")


class SequenceStep(Base):
    __tablename__ = "sequence_steps"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    day_offset = Column(Integer, nullable=False)
    channel = Column(String(50), nullable=False)
    condition = Column(String(100), default="always")
    template = Column(Text, default="")

    campaign = relationship("Campaign", back_populates="steps")


class Lead(Base, TimestampMixin):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    full_name = Column(String(255), nullable=False)
    role = Column(String(255), default="")
    company = Column(String(255), default="")
    company_size = Column(String(50), default="")
    country = Column(String(100), default="France")
    linkedin_url = Column(String(512), default="")
    email = Column(String(255), default="")
    email_status = Column(String(50), default="unknown")
    score = Column(Integer, default=0)
    score_reasons = Column(JSON, default=list)
    crm_status = Column(String(50), default="new")
    source = Column(String(100), default="mock")
    enrichment = Column(JSON, default=dict)

    workspace = relationship("Workspace", back_populates="leads")
    actions = relationship("Action", back_populates="lead")


class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("sequence_steps.id"), nullable=True)
    channel = Column(String(50), nullable=False)
    kind = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    content = Column(Text, default="")

    lead = relationship("Lead", back_populates="actions")
