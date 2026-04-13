"""
Task Manager — FastAPI Application

Standalone microservice for project task management.
Runs on port 8100, uses PostgreSQL for storage.
"""

from contextlib import asynccontextmanager
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import init_db, get_db
from models import WorkItem, Sprint, CommitLink
from schemas import (
    WorkItemCreate, WorkItemUpdate, WorkItemResponse,
    SprintCreate, SprintUpdate, SprintResponse,
    CommitLinkCreate, CommitLinkResponse,
    BoardResponse, BoardColumn,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print()
    print("=" * 50)
    print("  Task Manager Service")
    print("  http://localhost:8100")
    print("  Docs: http://localhost:8100/docs")
    print("=" * 50)
    print()
    yield


app = FastAPI(title="Task Manager", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════
# Work Items
# ═══════════════════════════════════════════

@app.post("/api/items", response_model=WorkItemResponse)
async def create_item(data: WorkItemCreate, db: AsyncSession = Depends(get_db)):
    item = WorkItem(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item, ["commits"])
    return item


@app.get("/api/items", response_model=list[WorkItemResponse])
async def list_items(
    project: str = Query(...),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    sprint_id: Optional[UUID] = None,
    assigned_to: Optional[str] = None,
    item_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(WorkItem).options(selectinload(WorkItem.commits)).where(WorkItem.project == project)
    if status:
        q = q.where(WorkItem.status == status)
    if priority:
        q = q.where(WorkItem.priority == priority)
    if sprint_id:
        q = q.where(WorkItem.sprint_id == sprint_id)
    if assigned_to:
        q = q.where(WorkItem.assigned_to == assigned_to)
    if item_type:
        q = q.where(WorkItem.item_type == item_type)
    q = q.order_by(WorkItem.priority, WorkItem.created_at)
    result = await db.execute(q)
    return result.scalars().all()


@app.get("/api/items/{item_id}", response_model=WorkItemResponse)
async def get_item(item_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WorkItem).options(selectinload(WorkItem.commits)).where(WorkItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    return item


@app.patch("/api/items/{item_id}", response_model=WorkItemResponse)
async def update_item(item_id: UUID, data: WorkItemUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkItem).where(WorkItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item, ["commits"])
    return item


@app.delete("/api/items/{item_id}")
async def delete_item(item_id: UUID, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(WorkItem).where(WorkItem.id == item_id))
    await db.commit()
    return {"status": "deleted"}


# ═══════════════════════════════════════════
# Sprints
# ═══════════════════════════════════════════

@app.post("/api/sprints", response_model=SprintResponse)
async def create_sprint(data: SprintCreate, db: AsyncSession = Depends(get_db)):
    sprint = Sprint(**data.model_dump())
    db.add(sprint)
    await db.commit()
    await db.refresh(sprint)
    return SprintResponse(
        **{c.name: getattr(sprint, c.name) for c in Sprint.__table__.columns},
        item_count=0,
    )


@app.get("/api/sprints", response_model=list[SprintResponse])
async def list_sprints(project: str = Query(...), db: AsyncSession = Depends(get_db)):
    q = (
        select(Sprint, func.count(WorkItem.id).label("item_count"))
        .outerjoin(WorkItem, WorkItem.sprint_id == Sprint.id)
        .where(Sprint.project == project)
        .group_by(Sprint.id)
        .order_by(Sprint.start_date)
    )
    result = await db.execute(q)
    sprints = []
    for sprint, count in result.all():
        sprints.append(SprintResponse(
            **{c.name: getattr(sprint, c.name) for c in Sprint.__table__.columns},
            item_count=count,
        ))
    return sprints


@app.patch("/api/sprints/{sprint_id}", response_model=SprintResponse)
async def update_sprint(sprint_id: UUID, data: SprintUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Sprint).where(Sprint.id == sprint_id))
    sprint = result.scalar_one_or_none()
    if not sprint:
        raise HTTPException(404, "Sprint not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(sprint, field, value)
    await db.commit()
    await db.refresh(sprint)
    count_result = await db.execute(
        select(func.count(WorkItem.id)).where(WorkItem.sprint_id == sprint_id)
    )
    return SprintResponse(
        **{c.name: getattr(sprint, c.name) for c in Sprint.__table__.columns},
        item_count=count_result.scalar() or 0,
    )


# ═══════════════════════════════════════════
# Board View
# ═══════════════════════════════════════════

@app.get("/api/board", response_model=BoardResponse)
async def get_board(
    project: str = Query(...),
    sprint_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(WorkItem).options(selectinload(WorkItem.commits)).where(WorkItem.project == project)
    if sprint_id:
        q = q.where(WorkItem.sprint_id == sprint_id)
    q = q.order_by(WorkItem.priority, WorkItem.created_at)
    result = await db.execute(q)
    items = result.scalars().all()

    statuses = ["todo", "in_progress", "review", "done"]
    columns = []
    for status in statuses:
        col_items = [i for i in items if i.status == status]
        columns.append(BoardColumn(
            status=status,
            items=col_items,
            count=len(col_items),
        ))

    return BoardResponse(
        project=project,
        sprint=str(sprint_id) if sprint_id else None,
        columns=columns,
        total=len(items),
    )


# ═══════════════════════════════════════════
# Commit Links
# ═══════════════════════════════════════════

@app.post("/api/commits", response_model=CommitLinkResponse)
async def link_commit(data: CommitLinkCreate, db: AsyncSession = Depends(get_db)):
    # Verify item exists
    result = await db.execute(select(WorkItem).where(WorkItem.id == data.work_item_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Work item not found")
    link = CommitLink(**data.model_dump())
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


# ═══════════════════════════════════════════
# Stats
# ═══════════════════════════════════════════

@app.get("/api/stats")
async def get_stats(project: str = Query(...), db: AsyncSession = Depends(get_db)):
    total = await db.execute(select(func.count(WorkItem.id)).where(WorkItem.project == project))
    done = await db.execute(
        select(func.count(WorkItem.id)).where(WorkItem.project == project, WorkItem.status == "done")
    )
    sprints = await db.execute(select(func.count(Sprint.id)).where(Sprint.project == project))
    return {
        "project": project,
        "total_items": total.scalar() or 0,
        "done_items": done.scalar() or 0,
        "total_sprints": sprints.scalar() or 0,
    }


# ═══════════════════════════════════════════
# Health
# ═══════════════════════════════════════════

@app.get("/health")
async def health():
    return {"status": "ok", "service": "task-manager"}


@app.get("/")
async def root():
    """Redirect root to docs."""
    return RedirectResponse(url="/docs")


# ═══════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
