"""Endpoints públicos: config, servicios, disponibilidad y creación de reservas."""
from __future__ import annotations

import secrets
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..availability import generate_calendar, generate_slots, is_slot_free
from ..config import settings
from ..database import get_db
from ..notifications import confirmation_message, send_whatsapp
from ..utils import local_now

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
    response_model=schemas.AppointmentCreatedOut,
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
    management_token = secrets.token_urlsafe(32)
    appt = crud.create_appointment(db, payload, service, end_at, management_token)

    # Confirmación por WhatsApp (real si Twilio está configurado; simulada si no)
    body = confirmation_message(
        settings.business_name, appt.customer_name, service.name, appt.start_at
    )
    if settings.twilio_enabled:
        body += f"\n\nCódigo privado para gestionar tu cita: {management_token}\nNo lo compartas."
    send_whatsapp(appt.customer_phone, body)
    result = schemas.AppointmentOut.model_validate(appt).model_dump()
    result["management_token"] = management_token
    return result


def _appointment_for_management(db: Session, management_token: str) -> models.Appointment:
    appointment = crud.appointment_by_management_token(db, management_token)
    if not appointment:
        raise HTTPException(status_code=404, detail="Código de gestión inválido.")
    return appointment


def _ensure_appointment_can_be_managed(appointment: models.Appointment) -> None:
    if appointment.status not in (models.STATUS_PENDING, models.STATUS_CONFIRMED) or appointment.start_at <= local_now():
        raise HTTPException(status_code=409, detail="Esta cita ya no se puede modificar.")


@router.post(
    "/appointments/manage/lookup",
    response_model=schemas.ManagedAppointmentOut,
    summary="Consultar una cita con su código privado",
)
def lookup_managed_appointment(
    payload: schemas.AppointmentManageRequest, db: Session = Depends(get_db)
):
    appointment = _appointment_for_management(db, payload.management_token)
    return {
        "service_id": appointment.service_id,
        "service_name": appointment.service.name,
        "start_at": appointment.start_at,
        "end_at": appointment.end_at,
        "status": appointment.status,
    }


@router.post(
    "/appointments/manage/cancel",
    response_model=schemas.MessageOut,
    summary="Cancelar una cita con su código privado",
)
def cancel_managed_appointment(
    payload: schemas.AppointmentManageRequest, db: Session = Depends(get_db)
):
    appointment = _appointment_for_management(db, payload.management_token)
    _ensure_appointment_can_be_managed(appointment)
    crud.set_status(db, appointment, models.STATUS_CANCELLED)
    return {"detail": "Cita cancelada."}


@router.post(
    "/appointments/manage/reschedule",
    response_model=schemas.ManagedAppointmentOut,
    summary="Reprogramar una cita con su código privado",
)
def reschedule_managed_appointment(
    payload: schemas.AppointmentRescheduleRequest, db: Session = Depends(get_db)
):
    appointment = _appointment_for_management(db, payload.management_token)
    _ensure_appointment_can_be_managed(appointment)
    service = crud.get_service(db, appointment.service_id)
    if not service or not service.active:
        raise HTTPException(status_code=409, detail="El servicio ya no está disponible.")
    if not is_slot_free(db, service, payload.start_at, exclude_appointment_id=appointment.id):
        raise HTTPException(status_code=409, detail="Ese horario no está disponible.")
    end_at = payload.start_at + timedelta(minutes=service.duration_min)
    appointment = crud.reschedule_appointment(db, appointment, payload.start_at, end_at)
    return {
        "service_id": appointment.service_id,
        "service_name": service.name,
        "start_at": appointment.start_at,
        "end_at": appointment.end_at,
        "status": appointment.status,
    }
