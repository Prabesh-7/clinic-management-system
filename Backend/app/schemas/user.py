from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
import uuid

from app.models.user import UserRole, UserStatus


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=150, pattern=r"^[a-zA-Z0-9._-]+$")
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    role: UserRole = UserRole.DENTAL


class DentalUserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(
        min_length=3,
        max_length=150,
        pattern=r"^[a-zA-Z0-9._-]+$",
        description="Unique login name. Only letters, numbers, dots, underscores, and hyphen.",
        examples=["Dental-1"],
    )
    email: EmailStr = Field(examples=["dentist@example.com"])
    full_name: str = Field(
        min_length=2,
        max_length=200,
        examples=["Dr. Nabin Babu"],
    )
    temporary_password: SecretStr = Field(
        min_length=12,
        max_length=128,
        description="Temporary password. It must be changed on first login.",
        examples=["Dental!2026Temp"],
    )
    temporary_password_confirmation: SecretStr = Field(
        min_length=12,
        max_length=128,
        description="Repeat the temporary password exactly.",
        examples=["Dental!2026Temp"],
    )
    clinic_id: uuid.UUID | None = None
    create_dentist_profile: bool = Field(
        default=True,
        description="Create an empty dentist profile for the dental account.",
    )

    @field_validator("temporary_password")
    @classmethod
    def validate_temporary_password(cls, password: SecretStr) -> SecretStr:
        value = password.get_secret_value()
        if not any(char.islower() for char in value):
            raise ValueError("Password must contain a lowercase letter")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain an uppercase letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain a digit")
        if not any(not char.isalnum() for char in value):
            raise ValueError("Password must contain a special character")
        return password

    @model_validator(mode="after")
    def validate_password_confirmation(self):
        password = self.temporary_password.get_secret_value()
        confirmation = self.temporary_password_confirmation.get_secret_value()
        if password != confirmation:
            raise ValueError(
                "temporary_password_confirmation must match temporary_password"
            )
        return self


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    must_change_password: bool = False
    created_at: datetime
