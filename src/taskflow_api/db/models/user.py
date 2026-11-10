import uuid
from datetime import UTC, datetime

from sqlalchemy import UUID, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taskflow_api.db.base import Base
from taskflow_api.db.models.project_member import ProjectMember
from taskflow_api.db.models.task import Task


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(length=320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(length=1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    project_memberships: Mapped[list[ProjectMember]] = relationship(
        back_populates="user"
    )
    assigned_tasks: Mapped[list[Task]] = relationship(back_populates="assignee")
