"""
Task Manager — Pydantic Schemas
"""

from datetime import datetime, date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


# --- Work Item ---

class WorkItemCreate(BaseModel):
    project: str
    title: str
    description: str = ""
    item_type: str = "task"
    status: str = "todo"
    priority: str = "P2"
    assigned_to: str = ""
    sprint_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    tags: str = ""


class WorkItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    item_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    sprint_id: Optional[UUID] = None
    tags: Optional[str] = None


class WorkItemResponse(BaseModel):
    id: UUID
    project: str
    title: str
    description: str
    item_type: str
    status: str
    priority: str
    assigned_to: str
    sprint_id: Optional[UUID]
    parent_id: Optional[UUID]
    tags: str
    created_at: datetime
    updated_at: datetime
    commits: list["CommitLinkResponse"] = []

    model_config = {"from_attributes": True}


# --- Sprint ---

class SprintCreate(BaseModel):
    project: str
    name: str
    goal: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class SprintUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class SprintResponse(BaseModel):
    id: UUID
    project: str
    name: str
    goal: str
    start_date: Optional[date]
    end_date: Optional[date]
    status: str
    created_at: datetime
    item_count: int = 0

    model_config = {"from_attributes": True}


# --- Commit Link ---

class CommitLinkCreate(BaseModel):
    work_item_id: UUID
    commit_hash: str
    message: str = ""
    branch: str = ""


class CommitLinkResponse(BaseModel):
    id: UUID
    commit_hash: str
    message: str
    branch: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Board ---

class BoardColumn(BaseModel):
    status: str
    items: list[WorkItemResponse]
    count: int


class BoardResponse(BaseModel):
    project: str
    sprint: Optional[str] = None
    columns: list[BoardColumn]
    total: int
