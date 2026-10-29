from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from taskflow_api.api.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from taskflow_api.db.models.project import Project
from taskflow_api.db.models.project_member import ProjectMember, ProjectRole
from taskflow_api.db.models.user import User
from taskflow_api.dependencies.auth import get_current_user
from taskflow_api.dependencies.database import get_db

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Project:
    project = Project(name=project_data.name, description=project_data.description)
    db.add(project)

    db.flush()

    membership = ProjectMember(
        project_id=project.id, user_id=current_user.id, role=ProjectRole.OWNER
    )
    db.add(membership)

    db.commit()
    db.refresh(project)

    return project


@router.get("", response_model=list[ProjectResponse])
def get_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Project]:
    stmt = (
        select(Project)
        .join(ProjectMember)
        .where(ProjectMember.user_id == current_user.id)
    )
    projects = db.scalars(stmt).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    stmt = (
        select(Project)
        .join(ProjectMember)
        .where(
            ProjectMember.user_id == current_user.id,
            Project.id == project_id,
        )
    )
    project = db.scalar(stmt)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project doesn't exist"
        )
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    stmt = (
        select(Project, ProjectMember)
        .join(ProjectMember)
        .where(
            ProjectMember.user_id == current_user.id,
            Project.id == project_id,
        )
    )
    result: tuple[Project, ProjectMember] | None = db.execute(stmt).one_or_none()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project doesn't exist"
        )
    project, project_member = result
    if project_member.role not in {ProjectRole.OWNER, ProjectRole.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    for field in project_data.model_fields_set:
        setattr(project, field, getattr(project_data, field))

    db.commit()
    db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    result: tuple[ProjectMember, Project] | None = db.execute(
        select(ProjectMember, Project)
        .join(Project)
        .where(
            ProjectMember.user_id == current_user.id,
            ProjectMember.project_id == project_id,
        )
    ).one_or_none()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project doesn't exist"
        )
    current_user_membership, project = result
    if current_user_membership.role != ProjectRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    db.delete(project)
    db.commit()
