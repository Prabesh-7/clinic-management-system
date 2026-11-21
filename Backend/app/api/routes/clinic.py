from datetime import datetime, timezone
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_clinic, require_clinic_owner
from app.core.security import generate_invite_token, hash_invite_token
from app.core.config import get_settings
from app.db.session import get_db
from app.models.clinic import (
    Clinic,
    ClinicLocation,
    ClinicMembership,
    ClinicWorkingHour,
    DentistProfile,
    MembershipRole,
    MembershipStatus,
)
from app.models.invite import AccountInvite
from app.models.user import User, UserRole, UserStatus
from app.schemas.clinic import (
    ClinicLocationCreate,
    ClinicProfileUpdate,
    ClinicResponse,
    ClinicMembershipCreate,
    DentistProfileUpdate,
    WorkingHourCreate,
)
from sqlalchemy import delete, update
from app.services.email import send_invite_email

router = APIRouter(prefix="/clinic", tags=["clinic"])


@router.get("/me", response_model=ClinicResponse)
async def clinic_me(
    context: tuple[Clinic, ClinicMembership] = Depends(get_current_clinic),
):
    clinic, _ = context
    return clinic


@router.patch("/me", response_model=ClinicResponse)
async def update_clinic_profile(
    payload: ClinicProfileUpdate,
    context: tuple[Clinic, ClinicMembership] = Depends(require_clinic_owner),
    db: AsyncSession = Depends(get_db),
):
    clinic, _ = context
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(clinic, field, value)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@router.post("/locations")
async def create_location(
    payload: ClinicLocationCreate,
    context: tuple[Clinic, ClinicMembership] = Depends(require_clinic_owner),
    db: AsyncSession = Depends(get_db),
):
    clinic, _ = context
    location = ClinicLocation(clinic_id=clinic.id, **payload.model_dump())
    if location.is_primary:
        await db.execute(
            update(ClinicLocation)
            .where(ClinicLocation.clinic_id == clinic.id)
            .values(is_primary=False)
        )
    db.add(location)
    await db.commit()
    await db.refresh(location)
    return location


@router.put("/locations/{location_id}/working-hours")
async def replace_working_hours(
    location_id: UUID,
    payload: list[WorkingHourCreate],
    context: tuple[Clinic, ClinicMembership] = Depends(require_clinic_owner),
    db: AsyncSession = Depends(get_db),
):
    clinic, _ = context
    location = await db.scalar(
        select(ClinicLocation).where(
            ClinicLocation.id == location_id,
            ClinicLocation.clinic_id == clinic.id,
        )
    )
    if location is None:
        raise HTTPException(status_code=404, detail="Clinic location not found")

    await db.execute(
        delete(ClinicWorkingHour)
        .where(ClinicWorkingHour.clinic_location_id == location.id)
    )
    for item in payload:
        db.add(ClinicWorkingHour(
            clinic_location_id=location.id,
            **item.model_dump(),
        ))
    await db.commit()
    return {"status": "updated"}


@router.post("/staff")
async def create_clinic_staff(
    payload: ClinicMembershipCreate,
    context: tuple[Clinic, ClinicMembership] = Depends(require_clinic_owner),
    db: AsyncSession = Depends(get_db),
):
    clinic, _ = context
    existing = await db.execute(
        select(User).where(
            (User.username == payload.username)
            | (User.email == str(payload.email).lower())
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Username or email already exists")

    user_role = (
        UserRole.DENTAL
        if payload.role == MembershipRole.DENTIST
        else UserRole.CLINIC_OWNER
        if payload.role == MembershipRole.OWNER
        else UserRole.RECEPTIONIST
        if payload.role == MembershipRole.RECEPTIONIST
        else UserRole.ACCOUNTANT
    )
    user = User(
        username=payload.username,
        email=str(payload.email).lower(),
        full_name=payload.full_name,
        role=user_role,
        status=UserStatus.INVITE_PENDING,
        password_hash=None,
    )
    db.add(user)
    await db.flush()
    membership_status = MembershipStatus.INVITE_PENDING
    db.add(ClinicMembership(
        clinic_id=clinic.id,
        user_id=user.id,
        role=payload.role,
        status=membership_status,
        is_primary=False,
    ))
    if payload.role == MembershipRole.DENTIST:
        db.add(DentistProfile(clinic_id=clinic.id, user_id=user.id))

    raw_token = generate_invite_token()
    db.add(AccountInvite(
        user_id=user.id,
        clinic_id=clinic.id,
        token_hash=hash_invite_token(raw_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=get_settings().invite_token_hours),
    ))
    await db.commit()
    await db.refresh(user)
    try:
        await send_invite_email(
            recipient_email=user.email,
            recipient_name=user.full_name,
            raw_token=raw_token,
        )
    except Exception as exc:
        raise HTTPException(status_code=202, detail="Staff account created, but invite email failed") from exc
    return {"id": str(user.id), "username": user.username, "email": user.email, "status": user.status.value}


@router.patch("/dentist-profile/me")
async def update_my_dentist_profile(
    payload: DentistProfileUpdate,
    context: tuple[Clinic, ClinicMembership] = Depends(get_current_clinic),
    db: AsyncSession = Depends(get_db),
):
    clinic, membership = context
    if membership.role != MembershipRole.DENTIST:
        raise HTTPException(status_code=403, detail="Dentist profile access required")

    profile = await db.scalar(
        select(DentistProfile).where(
            DentistProfile.clinic_id == clinic.id,
            DentistProfile.user_id == membership.user_id,
        )
    )
    if profile is None:
        profile = DentistProfile(
            clinic_id=clinic.id,
            user_id=membership.user_id,
        )
        db.add(profile)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile
