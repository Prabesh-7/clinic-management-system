from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole, UserStatus


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=150, pattern=r"^[a-zA-Z0-9._-]+$")
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    role: UserRole = UserRole.DENTAL


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    created_at: datetime
