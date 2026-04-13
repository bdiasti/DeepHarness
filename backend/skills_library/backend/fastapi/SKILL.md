---
name: fastapi
description: Python FastAPI with async SQLAlchemy, Pydantic validation, dependency injection
---

# FastAPI

Python async web framework with Pydantic models, async SQLAlchemy 2.x, and DI via `Depends`.

## App Setup

```python
# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .db import engine, Base
from .routers import users

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(users.router, prefix="/users", tags=["users"])
```

## Async SQLAlchemy

```python
# db.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db", echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase): pass

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
```

## Model & Pydantic Schemas

```python
# models.py
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str]

# schemas.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    model_config = {"from_attributes": True}
```

## Router with Dependencies

```python
# routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import User
from ..schemas import UserCreate, UserRead

router = APIRouter()

@router.post("", response_model=UserRead, status_code=201)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User(**data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Not found")
    return user
```

## Auth Dependency Example

```python
from fastapi import Header, HTTPException

async def current_user(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401)
    # decode JWT, return user
    return {"id": 1}
```

## Tips
- Run with `uvicorn main:app --reload`.
- Use `response_model` to control output; `status_code` for non-200 responses.
- Prefer `async def` endpoints when doing I/O; sync endpoints run in threadpool.
- Use Alembic for migrations; Pydantic Settings (`pydantic-settings`) for config.
