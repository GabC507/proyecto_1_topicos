"""Operaciones de base de datos (Create/Read/Update/Delete)."""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from . import models, schemas


# ---------- Servicios ----------
def list_services(db: Session, only_active: bool = True) -> list[models.Service]:
    q = db.query(models.Service)
    if only_active:
        q = q.filter(models.Service.active.is_(True))
    return q.order_by(models.Service.id).all()


def get_service(db: Session, service_id: int) -> Optional[models.Service]:
    return db.query(models.Service).filter(models.Service.id == service_id).first()


def create_service(db: Session, data: schemas.ServiceCreate) -> models.Service:
    obj = models.Service(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_service(db: Session, service: models.Service, data: schemas.ServiceUpdate) -> models.Service:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(service, key, value)
    db.commit()
    db.refresh(service)
    return service


def delete_service(db: Session, service: models.Service) -> None:
    db.delete(service)
    db.commit()


# ---------- Citas ----------
def create_appointment(
    db: Session, data: schemas.AppointmentCreate, service: models.Service, end_at: datetime
) -> models.Appointment:
    obj = models.Appointment(
        customer_name=data.customer_name.strip(),
        customer_phone=data.customer_phone,
        service_id=service.id,
        start_at=data.start_at,
        end_at=end_at,
        notes=(data.notes or "").strip(),
        status=models.STATUS_PENDING,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_appointments(
    db: Session, status: Optional[str] = None, day: Optional[date] = None
) -> list[models.Appointment]:
    q = db.query(models.Appointment)
    if status:
        q = q.filter(models.Appointment.status == status)
    if day:
        q = q.filter(
            models.Appointment.start_at >= datetime.combine(day, time.min),
            models.Appointment.start_at <= datetime.combine(day, time.max),
        )
    return q.order_by(models.Appointment.start_at).all()


def get_appointment(db: Session, appt_id: int) -> Optional[models.Appointment]:
    return db.query(models.Appointment).filter(models.Appointment.id == appt_id).first()


def set_status(db: Session, appt: models.Appointment, status: str) -> models.Appointment:
    appt.status = status
    db.commit()
    db.refresh(appt)
    return appt


def delete_appointment(db: Session, appt: models.Appointment) -> None:
    db.delete(appt)
    db.commit()


def stats(db: Session) -> dict:
    from .utils import local_now

    def count(status: str) -> int:
        return db.query(models.Appointment).filter(models.Appointment.status == status).count()

    upcoming = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.start_at >= local_now(),
            models.Appointment.status.in_([models.STATUS_PENDING, models.STATUS_CONFIRMED]),
        )
        .count()
    )
    return {
        "total": db.query(models.Appointment).count(),
        "pending": count(models.STATUS_PENDING),
        "confirmed": count(models.STATUS_CONFIRMED),
        "cancelled": count(models.STATUS_CANCELLED),
        "done": count(models.STATUS_DONE),
        "upcoming": upcoming,
    }


def demand_forecast(db: Session, weeks: int = 8) -> dict:
    """Estimate demand for the next seven days from matching past weekdays.

    Cancelled appointments are excluded; each forecast is the mean booking
    count for that weekday across the requested number of complete weeks.
    """
    from .utils import local_now

    today = local_now().date()
    history_start = today - timedelta(days=weeks * 7)
    history_end = today - timedelta(days=1)
    rows = (
        db.query(models.Appointment.start_at)
        .filter(
            models.Appointment.start_at >= datetime.combine(history_start, time.min),
            models.Appointment.start_at < datetime.combine(today, time.min),
            models.Appointment.status.in_(
                [models.STATUS_PENDING, models.STATUS_CONFIRMED, models.STATUS_DONE]
            ),
        )
        .all()
    )
    counts = Counter(row[0].date() for row in rows)

    history = []
    for offset in range(weeks * 7):
        history_date = history_start + timedelta(days=offset)
        history.append({"date": history_date, "bookings": counts[history_date]})
    forecast_start = today + timedelta(days=1)
    forecast = []
    for offset in range(7):
        forecast_date = forecast_start + timedelta(days=offset)
        samples = [
            counts[forecast_date - timedelta(days=7 * sample)]
            for sample in range(1, weeks + 1)
        ]
        forecast.append(
            {
                "date": forecast_date,
                "weekday": forecast_date.weekday(),
                "expected_bookings": round(sum(samples) / len(samples), 1),
                "sample_weeks": len(samples),
            }
        )

    return {
        "lookback_weeks": weeks,
        "history_start": history_start,
        "history_end": history_end,
        "history": history,
        "forecast_start": forecast_start,
        "forecast_end": forecast[-1]["date"],
        "forecast": forecast,
        "has_history": bool(rows),
    }
