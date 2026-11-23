from datetime import time
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    model_validator,
)

from app.models.clinic import ClinicStatus


class ClinicCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        min_length=2,
        max_length=200,
        examples=["Smile Dental Clinic"],
    )
    owner_username: str = Field(
        min_length=3,
        max_length=150,
        pattern=r"^[a-zA-Z0-9._-]+$",
        examples=["Dental-1"],
    )
    owner_email: EmailStr = Field(examples=["owner@example.com"])
    owner_full_name: str = Field(
        min_length=2,
        max_length=200,
        examples=["Dr. Nabin Babu"],
    )
    timezone: str = "Asia/Kathmandu"
    currency: str = Field(default="NPR", min_length=3, max_length=3)
    owner_password: SecretStr
    owner_password_confirmation: SecretStr

    @model_validator(mode="after")
    def validate_credentials(self):
        password = self.owner_password.get_secret_value()
        confirmation = self.owner_password_confirmation.get_secret_value()
        if password != confirmation:
            raise ValueError("owner_password_confirmation must match owner_password")
        if len(password) < 12:
            raise ValueError("Owner password must contain at least 12 characters")
        if not any(c.islower() for c in password):
            raise ValueError("Owner password must contain a lowercase letter")
        if not any(c.isupper() for c in password):
            raise ValueError("Owner password must contain an uppercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Owner password must contain a digit")
        if not any(not c.isalnum() for c in password):
            raise ValueError("Owner password must contain a special character")
        return self


class ClinicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    registration_number: str | None = None
    website: str | None = None
    description: str | None = None
    timezone: str
    currency: str
    status: ClinicStatus


class ClinicProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    registration_number: str | None = Field(default=None, max_length=100)
    website: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    timezone: str | None = Field(default=None, max_length=100)
    currency: str | None = Field(default=None, min_length=3, max_length=3)


class ClinicLocationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    address_line1: str = Field(min_length=3, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str = Field(default="Nepal", max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_primary: bool = False


class WorkingHourCreate(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    opens_at: time | None = None
    closes_at: time | None = None
    break_starts_at: time | None = None
    break_ends_at: time | None = None
    is_closed: bool = False
