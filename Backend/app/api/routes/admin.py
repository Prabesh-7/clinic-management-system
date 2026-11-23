from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.core.config import get_settings
from app.core.security import generate_invite_token, hash_invite_token
from app.db.session import get_db
from app.models.invite import AccountInvite
from app.models.user import User, UserRole, UserStatus
from app.services.email import send_invite_email
from app.models.clinic import (
    Clinic,
    ClinicStatus,
)
from app.schemas.clinic import ClinicCreate, ClinicResponse
from app.core.security import hash_password
from slugify import slugify

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/clinics", response_model=list[ClinicResponse])
async def list_clinics(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(
        select(Clinic).order_by(Clinic.created_at.desc())
    )
    return result.scalars().all()


@router.post("/clinics", response_model=ClinicResponse, status_code=status.HTTP_201_CREATED)
async def create_clinic(
    payload: ClinicCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Clinic:
    existing_owner = await db.execute(
        select(User).where(
            (User.username == payload.owner_username)
            | (User.email == str(payload.owner_email).lower())
        )
    )
    if existing_owner.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Owner username or email already exists")

    base_slug = slugify(payload.name)
    slug = base_slug
    suffix = 2
    while True:
        existing = await db.execute(select(Clinic).where(Clinic.slug == slug))
        if existing.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    clinic = Clinic(
        name=payload.name,
        slug=slug,
        timezone=payload.timezone,
        currency=payload.currency.upper(),
        status=ClinicStatus.PENDING_VERIFICATION,
    )
    db.add(clinic)
    await db.flush()

    owner = User(
        username=payload.owner_username,
        email=str(payload.owner_email).lower(),
        full_name=payload.owner_full_name,
        role=UserRole.DENTAL,
        status=UserStatus.INVITE_PENDING,
        password_hash=None,
    )
    db.add(owner)
    await db.flush()
    clinic.owner_user_id = owner.id

    raw_token: str | None = None
    if payload.credential_mode == "invite":
        raw_token = generate_invite_token()
        db.add(AccountInvite(
            user_id=owner.id,
            clinic_id=clinic.id,
            token_hash=hash_invite_token(raw_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=get_settings().invite_token_hours),
        ))
    else:
        owner.status = UserStatus.ACTIVE
        owner.password_hash = hash_password(
            payload.temporary_password.get_secret_value()
        )
        owner.must_change_password = True
    await db.commit()
    await db.refresh(clinic)

    if raw_token is not None:
        try:
            await send_invite_email(
                recipient_email=owner.email,
                recipient_name=owner.full_name,
                raw_token=raw_token,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=202,
                detail="Clinic created, but the owner invite email could not be sent",
            ) from exc
    return clinic
