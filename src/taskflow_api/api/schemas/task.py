from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


class TaskSortField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DUE_DATE = "due_date"
    PRIORITY = "priority"
    STATUS = "status"
    TITLE = "title"


SortParam = tuple[TaskSortField, Literal["asc", "desc"]]


class TaskListQueryParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    page: int = Field(default=1, ge=1)
    sort: str = "-created_at"
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: UUID | None = None

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, value: str) -> str:
        if not value:
            raise ValueError("Sort cannot be empty")

        fields = value.split(",")

        if len(fields) > 3:
            raise ValueError("Maximum 3 sort fields allowed")

        seen = set()

        for item in fields:
            field_name = item.removeprefix("-")

            try:
                field = TaskSortField(field_name)
            except ValueError as exc:
                raise ValueError(f"Invalid sort field: {field_name}") from exc

            if field in seen:
                raise ValueError(f"Duplicate sort field: {field_name}")

            seen.add(field)

        return value

    @property
    def sort_params(self) -> list[SortParam]:
        result = []

        for item in self.sort.split(","):
            descending = item.startswith("-")
            field = TaskSortField(item.removeprefix("-"))

            result.append(
                (
                    field,
                    "desc" if descending else "asc",
                )
            )

        return result
