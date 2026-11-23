from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User, UserStatus
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    result = await db.execute(
        select(User).where(User.username == payload.username)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if user.status == UserStatus.DISABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Account is disabled",
                "action": "Contact the platform administrator",
                "status": "disabled",
            },
        )
    if user.password_hash is None or not verify_password(
        payload.password.get_secret_value(),
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(
        access_token=token,
        must_change_password=user.must_change_password,
    )


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    current_password = payload.current_password.get_secret_value()
    new_password = payload.new_password.get_secret_value()
    new_password_confirmation = payload.new_password_confirmation.get_secret_value()

    if new_password != new_password_confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password confirmation does not match",
        )
    if current_password == new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must differ from the current password",
        )
    if current_user.password_hash is None or not verify_password(
        current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.password_hash = hash_password(new_password)
    current_user.must_change_password = False
    await db.commit()
    return {"status": "password_changed"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
