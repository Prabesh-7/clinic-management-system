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
    ClinicMembership,
    ClinicStatus,
    DentistProfile,
    MembershipRole,
    MembershipStatus,
)
from app.schemas.clinic import ClinicCreate, ClinicResponse
from app.schemas.user import DentalUserCreate
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


@router.post("/dental-users", status_code=status.HTTP_201_CREATED)
async def create_dental_user(
    payload: DentalUserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    username = payload.username.strip()
    email = str(payload.email).lower()
    full_name = payload.full_name.strip()

    existing = await db.execute(
        select(User).where(
            (User.username == username)
            | (User.email == email)
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    if payload.clinic_id is not None:
        clinic = await db.scalar(
            select(Clinic).where(Clinic.id == payload.clinic_id)
        )
        if clinic is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Clinic not found",
                    "clinic_id": str(payload.clinic_id),
                    "action": "Create the clinic with POST /admin/clinics or set clinic_id to null.",
                },
            )

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        role=UserRole.DENTAL,
        status=UserStatus.ACTIVE,
        password_hash=hash_password(payload.temporary_password.get_secret_value()),
        must_change_password=True,
    )
    db.add(user)
    await db.flush()

    if payload.clinic_id is not None:
        db.add(ClinicMembership(
            clinic_id=payload.clinic_id,
            user_id=user.id,
            role=MembershipRole.DENTIST,
            status=MembershipStatus.ACTIVE,
            is_primary=True,
        ))
        if payload.create_dentist_profile:
            db.add(DentistProfile(
                clinic_id=payload.clinic_id,
                user_id=user.id,
            ))

    await db.commit()
    await db.refresh(user)
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "status": user.status.value,
        "must_change_password": user.must_change_password,
        "clinic_id": str(payload.clinic_id) if payload.clinic_id is not None else None,
    }


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
        role=UserRole.CLINIC_OWNER,
        status=UserStatus.INVITE_PENDING,
        password_hash=None,
    )
    db.add(owner)
    await db.flush()

    db.add(ClinicMembership(
        clinic_id=clinic.id,
        user_id=owner.id,
        role=MembershipRole.OWNER,
        status=MembershipStatus.INVITE_PENDING,
        is_primary=True,
    ))

    raw_token = generate_invite_token()
    db.add(AccountInvite(
        user_id=owner.id,
        clinic_id=clinic.id,
        token_hash=hash_invite_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=get_settings().invite_token_hours),
    ))
    await db.commit()
    await db.refresh(clinic)

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
