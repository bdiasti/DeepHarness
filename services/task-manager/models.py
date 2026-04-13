"""
Task Manager — SQLAlchemy Models
"""

import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Text, DateTime, Date, ForeignKey, Table, Enum as SAEnum, Integer
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


# --- Work Item ---

class WorkItem(Base):
    __tablename__ = "work_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project = Column(String(200), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    item_type = Column(String(50), default="task")  # task, bug, story, epic
    status = Column(String(50), default="todo", index=True)  # todo, in_progress, review, done
    priority = Column(String(10), default="P2")  # P0, P1, P2, P3
    assigned_to = Column(String(200), default="")
    sprint_id = Column(UUID(as_uuid=True), ForeignKey("sprints.id"), nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=True)
    tags = Column(String(500), default="")  # comma-separated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sprint = relationship("Sprint", back_populates="items")
    parent = relationship("WorkItem", remote_side=[id])
    commits = relationship("CommitLink", back_populates="work_item", cascade="all, delete-orphan")


# --- Sprint ---

class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project = Column(String(200), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    goal = Column(Text, default="")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(50), default="planning")  # planning, active, completed
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("WorkItem", back_populates="sprint")


# --- Commit Link ---

class CommitLink(Base):
    __tablename__ = "commit_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_item_id = Column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=False)
    commit_hash = Column(String(100), nullable=False)
    message = Column(String(500), default="")
    branch = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    work_item = relationship("WorkItem", back_populates="commits")
