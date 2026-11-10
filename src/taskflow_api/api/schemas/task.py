from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from taskflow_api.db.models.task import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: UUID | None = None
    due_date: datetime | None = None


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str | None = None
    status: TaskStatus
    priority: TaskPriority
    assignee_id: UUID | None = None
    due_date: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    limit: int
    pages: int
