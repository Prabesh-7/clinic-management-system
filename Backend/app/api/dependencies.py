from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole, UserStatus
from app.models.clinic import (
    Clinic,
    ClinicMembership,
    MembershipRole,
    MembershipStatus,
    ClinicStatus,
)

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active",
        )

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return current_user


async def get_current_clinic(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[Clinic, ClinicMembership]:
    membership_result = await db.execute(
        select(ClinicMembership)
        .join(Clinic, Clinic.id == ClinicMembership.clinic_id)
        .where(
            ClinicMembership.user_id == current_user.id,
            ClinicMembership.status == MembershipStatus.ACTIVE,
            Clinic.status != ClinicStatus.CLOSED,
        )
        .order_by(ClinicMembership.is_primary.desc())
    )
    membership = membership_result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active clinic membership",
        )

    clinic_result = await db.execute(
        select(Clinic).where(Clinic.id == membership.clinic_id)
    )
    clinic = clinic_result.scalar_one_or_none()
    if clinic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found",
        )
    return clinic, membership


async def require_clinic_owner(
    context: tuple[Clinic, ClinicMembership] = Depends(get_current_clinic),
) -> tuple[Clinic, ClinicMembership]:
    clinic, membership = context
    if membership.role != MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clinic owner access required",
        )
    return clinic, membership
