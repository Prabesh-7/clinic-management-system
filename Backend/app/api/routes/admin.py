from datetime import datetime, timedelta, timezone
import smtplib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.core.config import get_settings
from app.core.security import generate_invite_token, hash_invite_token
from app.db.session import get_db
from app.models.invite import AccountInvite
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserResponse
from app.services.email import send_invite_email

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/dental-users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dental_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> User:
    existing = await db.execute(
        select(User).where(
            (User.username == payload.username)
            | (User.email == str(payload.email).lower())
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered",
        )

    user = User(
        username=payload.username,
        email=str(payload.email).lower(),
        full_name=payload.full_name,
        role=UserRole.DENTAL,
        status=UserStatus.INVITE_PENDING,
        password_hash=None,
    )
    db.add(user)
    await db.flush()

    raw_token = generate_invite_token()
    invite = AccountInvite(
        user_id=user.id,
        token_hash=hash_invite_token(raw_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=get_settings().invite_token_hours),
    )
    db.add(invite)
    await db.commit()
    await db.refresh(user)

    try:
        await send_invite_email(
            recipient_email=user.email,
            recipient_name=user.full_name,
            raw_token=raw_token,
        )
    except (RuntimeError, OSError, smtplib.SMTPException) as exc:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=(
                "Dental account created, but the invite email could not be sent"
            ),
        ) from exc

    return user
