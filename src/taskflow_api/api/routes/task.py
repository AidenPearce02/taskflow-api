import math
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from taskflow_api.api.schemas.task import TaskCreate, TaskListResponse, TaskResponse
from taskflow_api.db.models.project_member import ProjectMember
from taskflow_api.db.models.task import Task, TaskPriority, TaskStatus
from taskflow_api.db.models.user import User
from taskflow_api.dependencies.auth import get_current_user
from taskflow_api.dependencies.database import get_db

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TaskResponse)
def create_task(
    project_id: UUID,
    task_create: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TaskResponse:
    stmt = select(ProjectMember).where(
        ProjectMember.user_id == current_user.id,
        ProjectMember.project_id == project_id,
    )
    result: ProjectMember | None = db.execute(stmt).scalar_one_or_none()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project doesn't exist"
        )

    if task_create.assignee_id is not None:
        stmt = select(ProjectMember).where(
            ProjectMember.user_id == task_create.assignee_id,
            ProjectMember.project_id == project_id,
        )
        result: ProjectMember | None = db.execute(stmt).scalar_one_or_none()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of the project",
            )

    task = Task(**task_create.model_dump(), project_id=project_id)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get("", status_code=status.HTTP_200_OK, response_model=TaskListResponse)
def get_tasks(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
    task_priority: Annotated[TaskPriority | None, Query(alias="priority")] = None,
    assignee_id: Annotated[UUID | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TaskListResponse:
    stmt = select(ProjectMember).where(
        ProjectMember.user_id == current_user.id,
        ProjectMember.project_id == project_id,
    )
    result: ProjectMember | None = db.execute(stmt).scalar_one_or_none()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project doesn't exist"
        )

    offset = (page - 1) * limit

    conditions = [Task.project_id == project_id]
    if task_status is not None:
        conditions.append(Task.status == task_status)
    if task_priority is not None:
        conditions.append(Task.priority == task_priority)
    if assignee_id is not None:
        conditions.append(Task.assignee_id == assignee_id)

    stmt = (
        select(Task)
        .where(*conditions)
        .order_by(Task.created_at.desc(), Task.id.desc())
        .offset(offset)
        .limit(limit)
    )

    tasks = db.scalars(stmt).all()

    count_stmt = select(func.count()).select_from(Task).where(*conditions)
    total = db.scalar(count_stmt) or 0
    pages = math.ceil(total / limit)

    return {
        "items": tasks,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }
