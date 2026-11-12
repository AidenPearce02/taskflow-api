import math
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from taskflow_api.api.schemas.task import (
    SortParam,
    TaskCreate,
    TaskListQueryParams,
    TaskListResponse,
    TaskResponse,
    TaskSortField,
)
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


priority_order = case(
    (Task.priority == TaskPriority.LOW, 1),
    (Task.priority == TaskPriority.MEDIUM, 2),
    (Task.priority == TaskPriority.HIGH, 3),
)

status_order = case(
    (Task.status == TaskStatus.TODO, 1),
    (Task.status == TaskStatus.IN_PROGRESS, 2),
    (Task.status == TaskStatus.DONE, 3),
)

sort_columns = {
    TaskSortField.CREATED_AT: Task.created_at,
    TaskSortField.UPDATED_AT: Task.updated_at,
    TaskSortField.DUE_DATE: Task.due_date,
    TaskSortField.TITLE: Task.title,
    TaskSortField.PRIORITY: priority_order,
    TaskSortField.STATUS: status_order,
}


def build_task_order_clauses(sort_params: list[SortParam]) -> list[ColumnElement]:
    order_clauses = []

    for field, direction in sort_params:
        column = sort_columns[field]

        expression = column.desc() if direction == "desc" else column.asc()

        if field == TaskSortField.DUE_DATE:
            expression = expression.nulls_last()

        order_clauses.append(expression)
    return order_clauses


@router.get("", status_code=status.HTTP_200_OK, response_model=TaskListResponse)
def get_tasks(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    params: Annotated[TaskListQueryParams, Query()],
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

    offset = (params.page - 1) * params.limit

    conditions = [Task.project_id == project_id]
    if params.status is not None:
        conditions.append(Task.status == params.status)
    if params.priority is not None:
        conditions.append(Task.priority == params.priority)
    if params.assignee_id is not None:
        conditions.append(Task.assignee_id == params.assignee_id)

    order_clauses = build_task_order_clauses(params.sort_params)

    stmt = (
        select(Task)
        .where(*conditions)
        .order_by(*order_clauses, Task.id.desc())
        .offset(offset)
        .limit(params.limit)
    )

    tasks = db.scalars(stmt).all()

    count_stmt = select(func.count()).select_from(Task).where(*conditions)
    total = db.scalar(count_stmt) or 0
    pages = math.ceil(total / params.limit)

    return {
        "items": tasks,
        "total": total,
        "page": params.page,
        "limit": params.limit,
        "pages": pages,
    }
