from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    hash_invite_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.invite import AccountInvite
from app.models.user import User, UserStatus
from app.schemas.auth import AcceptInviteRequest, LoginRequest, TokenResponse
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

    if (
        user is None
        or user.status != UserStatus.ACTIVE
        or user.password_hash is None
        or not verify_password(payload.password.get_secret_value(), user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/invite/accept", response_model=UserResponse)
async def accept_invite(
    payload: AcceptInviteRequest,
    db: AsyncSession = Depends(get_db),
) -> User:
    password = payload.password.get_secret_value()
    password_confirmation = payload.password_confirmation.get_secret_value()

    if password != password_confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password confirmation does not match",
        )

    token_hash = hash_invite_token(payload.token.get_secret_value())
    result = await db.execute(
        select(AccountInvite).where(AccountInvite.token_hash == token_hash)
    )
    invite = result.scalar_one_or_none()

    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invite token",
        )

    now = datetime.now(timezone.utc)
    if invite.used_at is not None or invite.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite token is no longer valid",
        )

    expires_at = invite.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite token has expired",
        )

    user_result = await db.execute(select(User).where(User.id == invite.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invited user no longer exists",
        )

    user.password_hash = hash_password(password)
    user.status = UserStatus.ACTIVE
    invite.used_at = now
    await db.commit()
    await db.refresh(user)
    return user
