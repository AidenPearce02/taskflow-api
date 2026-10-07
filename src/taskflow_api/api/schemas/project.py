from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from taskflow_api.db.models.project_member import ProjectRole


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    description: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    name: str = Field(default=None, min_length=3, max_length=200)
    description: str | None = None


class ProjectMemberAdd(BaseModel):
    email: EmailStr
    role: ProjectRole = ProjectRole.MEMBER


class ProjectMemberUpdate(BaseModel):
    role: ProjectRole


class ProjectMemberResponse(BaseModel):
    user_id: UUID
    role: ProjectRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
