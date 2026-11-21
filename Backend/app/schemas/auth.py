from pydantic import BaseModel, Field, SecretStr, field_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    password: SecretStr = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: SecretStr = Field(min_length=8, max_length=128)
    new_password: SecretStr = Field(min_length=12, max_length=128)
    new_password_confirmation: SecretStr = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, password: SecretStr) -> SecretStr:
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


class AcceptInviteRequest(BaseModel):
    token: SecretStr = Field(min_length=32)
    password: SecretStr = Field(min_length=12, max_length=128)
    password_confirmation: SecretStr = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: SecretStr) -> SecretStr:
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
