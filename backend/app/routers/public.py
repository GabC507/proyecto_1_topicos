"""Endpoints públicos: config, servicios, disponibilidad y creación de reservas."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..availability import generate_calendar, generate_slots, is_slot_free
from ..config import settings
from ..database import get_db
from ..notifications import confirmation_message, send_whatsapp

router = APIRouter(prefix="/api", tags=["Público"])


@router.get("/config", response_model=schemas.ConfigOut, summary="Configuración del negocio")
def get_config():
    return schemas.ConfigOut(
        business_name=settings.business_name,
        timezone=settings.business_timezone,
        currency=settings.currency,
        open_hour=settings.open_hour,
        close_hour=settings.close_hour,
        slot_interval_minutes=settings.slot_interval_minutes,
        closed_weekdays=sorted(settings.closed_weekdays_set),
    )


@router.get("/services", response_model=list[schemas.ServiceOut], summary="Servicios activos")
def get_services(db: Session = Depends(get_db)):
    return crud.list_services(db, only_active=True)


@router.get("/availability", response_model=list[str], summary="Horarios disponibles")
def get_availability(
    service_id: int = Query(..., description="ID del servicio"),
    day: date = Query(..., alias="date", description="Fecha en formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    service = crud.get_service(db, service_id)
    if not service or not service.active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")
    return generate_slots(db, service, day)


@router.get(
    "/availability/calendar",
    response_model=list[schemas.AvailabilityCalendarDayOut],
    summary="Disponibilidad diaria de un mes",
)
def get_availability_calendar(
    service_id: int = Query(..., description="ID del servicio"),
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="Mes YYYY-MM"),
    db: Session = Depends(get_db),
):
    service = crud.get_service(db, service_id)
    if not service or not service.active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")
    try:
        month_start = datetime.strptime(month, "%Y-%m").date()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Mes inválido.") from exc
    return generate_calendar(db, service, month_start.year, month_start.month)


@router.post(
    "/appointments",
    response_model=schemas.AppointmentOut,
    status_code=201,
    summary="Crear una reserva",
)
def create_appointment(payload: schemas.AppointmentCreate, db: Session = Depends(get_db)):
    service = crud.get_service(db, payload.service_id)
    if not service or not service.active:
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")
    if not is_slot_free(db, service, payload.start_at):
        raise HTTPException(
            status_code=409,
            detail="Ese horario ya no está disponible. Por favor elige otro.",
        )
    end_at = payload.start_at + timedelta(minutes=service.duration_min)
    appt = crud.create_appointment(db, payload, service, end_at)

    # Confirmación por WhatsApp (real si Twilio está configurado; simulada si no)
    body = confirmation_message(
        settings.business_name, appt.customer_name, service.name, appt.start_at
    )
    send_whatsapp(appt.customer_phone, body)
    return appt
