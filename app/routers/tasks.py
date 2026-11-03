from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class StatusFilter(str, Enum):
    all = "all"
    completed = "completed"
    pending = "pending"


def _get_owned_task(db: Session, task_id: int, user: models.User) -> models.Task:
    # Returning 404 (not 403) for other users' tasks avoids leaking which IDs exist.
    task = db.scalar(
        select(models.Task).where(models.Task.id == task_id, models.Task.owner_id == user.id)
    )
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Task {task_id} not found")
    return task


@router.post("", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: schemas.TaskCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = models.Task(**payload.model_dump(), owner_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=schemas.TaskList)
def list_tasks(
    status_filter: StatusFilter = Query(StatusFilter.all, alias="status"),
    search: str | None = Query(None, max_length=100, description="Match in title/description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    conditions = [models.Task.owner_id == user.id]
    if status_filter is StatusFilter.completed:
        conditions.append(models.Task.completed.is_(True))
    elif status_filter is StatusFilter.pending:
        conditions.append(models.Task.completed.is_(False))
    if search:
        like = f"%{search}%"
        conditions.append(models.Task.title.ilike(like) | models.Task.description.ilike(like))

    total = db.scalar(select(func.count()).select_from(models.Task).where(*conditions)) or 0
    items = db.scalars(
        select(models.Task)
        .where(*conditions)
        .order_by(models.Task.created_at.desc(), models.Task.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return schemas.TaskList(total=total, skip=skip, limit=limit, items=items)


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return _get_owned_task(db, task_id, user)


@router.put("/{task_id}", response_model=schemas.TaskOut)
@router.patch("/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    payload: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = _get_owned_task(db, task_id, user)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No fields provided to update")
    if "title" in changes and changes["title"] is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "title cannot be null")
    if "completed" in changes and changes["completed"] is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "completed cannot be null")
    for field, value in changes.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}/toggle", response_model=schemas.TaskOut)
def toggle_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = _get_owned_task(db, task_id, user)
    task.completed = not task.completed
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = _get_owned_task(db, task_id, user)
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
