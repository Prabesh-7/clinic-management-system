import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    DENTAL = "dental"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    must_change_password: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(
            UserRole,
            name="user_role",
            validate_strings=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        index=True,
    )
    status: Mapped[UserStatus] = mapped_column(
        SqlEnum(
            UserStatus,
            name="user_status",
            validate_strings=True,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=UserStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
