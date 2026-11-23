from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_clinic, require_clinic_owner
from app.db.session import get_db
from app.models.clinic import Clinic, ClinicLocation, ClinicWorkingHour
from app.schemas.clinic import (
    ClinicLocationCreate,
    ClinicProfileUpdate,
    ClinicResponse,
    WorkingHourCreate,
)

router = APIRouter(prefix="/clinic", tags=["clinic"])


@router.get("/me", response_model=ClinicResponse)
async def clinic_me(
    clinic: Clinic = Depends(get_current_clinic),
):
    return clinic


@router.patch("/me", response_model=ClinicResponse)
async def update_clinic_profile(
    payload: ClinicProfileUpdate,
    clinic: Clinic = Depends(require_clinic_owner),
    db: AsyncSession = Depends(get_db),
):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one clinic detail to update",
        )

    for field, value in updates.items():
        setattr(clinic, field, value)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@router.post("/locations")
async def create_location(
    payload: ClinicLocationCreate,
    clinic: Clinic = Depends(require_clinic_owner),
    db: AsyncSession = Depends(get_db),
):
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
    clinic: Clinic = Depends(require_clinic_owner),
    db: AsyncSession = Depends(get_db),
):
    location = await db.scalar(
        select(ClinicLocation).where(
            ClinicLocation.id == location_id,
            ClinicLocation.clinic_id == clinic.id,
        )
    )
    if location is None:
        raise HTTPException(status_code=404, detail="Clinic location not found")

    await db.execute(
        delete(ClinicWorkingHour).where(
            ClinicWorkingHour.clinic_location_id == location.id
        )
    )
    for item in payload:
        db.add(
            ClinicWorkingHour(
                clinic_location_id=location.id,
                **item.model_dump(),
            )
        )
    await db.commit()
    return {"status": "updated"}
