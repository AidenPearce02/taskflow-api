from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from taskflow_api.api.schemas.project import (
    ProjectMemberAdd,
    ProjectMemberDetails,
    ProjectMemberResponse,
    ProjectMemberUpdate,
)
from taskflow_api.db.models.project import Project
from taskflow_api.db.models.project_member import ProjectMember, ProjectRole
from taskflow_api.db.models.user import User
from taskflow_api.dependencies.auth import get_current_user
from taskflow_api.dependencies.database import get_db

router = APIRouter()

ROLE_ASSIGNABLE_BY = {
    ProjectRole.OWNER: {ProjectRole.ADMIN, ProjectRole.MEMBER},
    ProjectRole.ADMIN: {ProjectRole.MEMBER},
}

ROLE_REMOVABLE_BY = {
    ProjectRole.OWNER: {ProjectRole.ADMIN, ProjectRole.MEMBER},
    ProjectRole.ADMIN: {ProjectRole.MEMBER},
}


@router.post(
    "/{project_id}/members",
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectMemberResponse,
)
def add_member(
    project_id: UUID,
    project_member_add: ProjectMemberAdd,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectMemberResponse:
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

    if project_member_add.role not in ROLE_ASSIGNABLE_BY.get(
        project_member.role, set()
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    new_member = db.scalar(select(User).where(User.email == project_member_add.email))
    if not new_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User doesn't exist"
        )

    existing_membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == new_member.id,
        )
    )

    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a project member",
        )

    membership = ProjectMember(
        project_id=project.id, user_id=new_member.id, role=project_member_add.role
    )

    db.add(membership)
    db.commit()
    db.refresh(membership)

    return membership


@router.get("/{project_id}/members", response_model=list[ProjectMemberDetails])
def get_members(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ProjectMemberDetails]:
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id,
    )

    membership = db.scalar(stmt)

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project doesn't exist",
        )

    stmt = (
        select(User, ProjectMember)
        .join(ProjectMember)
        .where(ProjectMember.project_id == project_id)
    )
    result: list[tuple[User, ProjectMember]] = db.execute(stmt).all()
    return [
        ProjectMemberDetails(
            user_id=user.id, email=user.email, role=project_membership.role
        )
        for user, project_membership in result
    ]


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
def update_member(
    project_id: UUID,
    user_id: UUID,
    project_member_update: ProjectMemberUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectMemberResponse:
    current_user_membership: ProjectMember | None = db.scalar(
        select(ProjectMember).where(
            ProjectMember.user_id == current_user.id,
            ProjectMember.project_id == project_id,
        )
    )
    if not current_user_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project doesn't exist"
        )

    update_member_membership: ProjectMember | None = db.scalar(
        select(ProjectMember).where(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id,
        )
    )
    if not update_member_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a project member",
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can't change your own role",
        )

    allowed_roles = ROLE_ASSIGNABLE_BY.get(current_user_membership.role, set())
    if (
        project_member_update.role not in allowed_roles
        or update_member_membership.role not in allowed_roles
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
    if update_member_membership.role == project_member_update.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Member already has this role",
        )

    update_member_membership.role = project_member_update.role

    db.commit()
    db.refresh(update_member_membership)

    return update_member_membership


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_member(
    project_id: UUID,
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    current_user_membership: ProjectMember | None = db.scalar(
        select(ProjectMember).where(
            ProjectMember.user_id == current_user.id,
            ProjectMember.project_id == project_id,
        )
    )
    if not current_user_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project doesn't exist"
        )

    delete_member_membership: ProjectMember | None = db.scalar(
        select(ProjectMember).where(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id,
        )
    )
    if not delete_member_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a project member",
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can't remove yourself from project",
        )

    allowed_roles = ROLE_REMOVABLE_BY.get(current_user_membership.role, set())
    if delete_member_membership.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    db.delete(delete_member_membership)
    db.commit()
