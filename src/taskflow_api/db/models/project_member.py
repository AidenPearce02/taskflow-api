import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taskflow_api.db.base import Base

if TYPE_CHECKING:
    from taskflow_api.db.models.project import Project
    from taskflow_api.db.models.user import User


class ProjectRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (
        Index(
            "ix_project_members_user_id_project_id",
            "user_id",
            "project_id",
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[ProjectRole] = mapped_column(
        Enum(
            ProjectRole,
            name="project_role",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    project: Mapped["Project"] = relationship(
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        back_populates="project_memberships",
    )
