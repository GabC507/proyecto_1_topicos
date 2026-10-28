"""Tests de la lógica de reservas y de la API."""
import os
import tempfile
from pathlib import Path

# Usar una base de datos de prueba aislada ANTES de importar la app.
test_db_path = (Path(tempfile.gettempdir()) / "citafacil_test.db").as_posix()
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"
os.environ["ADMIN_TOKEN"] = "test-token"

from datetime import datetime, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.utils import PhoneError, local_now, normalize_cl_phone  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(models.Service(name="Corte", duration_min=30, price=8000, active=True))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def _next_open_day_at(hour: int):
    d = (local_now() + timedelta(days=1)).replace(hour=hour, minute=0, second=0, microsecond=0)
    while d.weekday() == 6:  # saltar domingo
        d += timedelta(days=1)
    return d


# ---------- Validación de teléfono ----------
def test_phone_valid_formats():
    assert normalize_cl_phone("+56 9 4291 6570") == "+56942916570"
    assert normalize_cl_phone("942916570") == "+56942916570"
    assert normalize_cl_phone("56942916570") == "+56942916570"
    assert normalize_cl_phone("4291 6570") == "+56942916570"  # 8 dígitos -> antepone 9


def test_phone_invalid():
    with pytest.raises(PhoneError):
        normalize_cl_phone("12345")


# ---------- Reservas ----------
def test_create_and_conflict():
    sid = client.get("/api/services").json()[0]["id"]
    start = _next_open_day_at(11)
    payload = {
        "customer_name": "Camila",
        "customer_phone": "+56 9 8765 4321",
        "service_id": sid,
        "start_at": start.isoformat(),
    }
    r = client.post("/api/appointments", json=payload)
    assert r.status_code == 201, r.text

    # mismo horario -> 409 (no doble-booking)
    r2 = client.post("/api/appointments", json={**payload, "customer_name": "Otro"})
    assert r2.status_code == 409


def test_management_code_is_random_hashed_and_required_for_lookup():
    service_id = client.get("/api/services").json()[0]["id"]
    start = _next_open_day_at(11)
    booking = client.post(
        "/api/appointments",
        json={
            "customer_name": "Camila",
            "customer_phone": "942916570",
            "service_id": service_id,
            "start_at": start.isoformat(),
        },
    )
    assert booking.status_code == 201, booking.text
    token = booking.json()["management_token"]
    assert len(token) >= 40

    db = SessionLocal()
    access = db.query(models.AppointmentAccess).one()
    assert access.token_hash != token
    assert len(access.token_hash) == 64
    db.close()

    invalid = client.post(
        "/api/appointments/manage/lookup", json={"management_token": "x" * 43}
    )
    assert invalid.status_code == 404
    lookup = client.post(
        "/api/appointments/manage/lookup", json={"management_token": token}
    )
    assert lookup.status_code == 200, lookup.text
    assert lookup.json()["service_id"] == service_id
    assert "customer_phone" not in lookup.json()
    assert "customer_name" not in lookup.json()


def test_customer_can_cancel_only_with_management_code():
    service_id = client.get("/api/services").json()[0]["id"]
    start = _next_open_day_at(11)
    booking = client.post(
        "/api/appointments",
        json={
            "customer_name": "Camila",
            "customer_phone": "942916570",
            "service_id": service_id,
            "start_at": start.isoformat(),
        },
    )
    token = booking.json()["management_token"]

    invalid = client.post(
        "/api/appointments/manage/cancel", json={"management_token": "x" * 43}
    )
    assert invalid.status_code == 404
    cancelled = client.post(
        "/api/appointments/manage/cancel", json={"management_token": token}
    )
    assert cancelled.status_code == 200, cancelled.text
    available = client.get(
        f"/api/availability?service_id={service_id}&date={start.date().isoformat()}"
    ).json()
    assert "11:00" in available


def test_customer_can_reschedule_and_cannot_take_an_occupied_slot():
    service_id = client.get("/api/services").json()[0]["id"]
    start = _next_open_day_at(11)
    first = client.post(
        "/api/appointments",
        json={
            "customer_name": "Camila",
            "customer_phone": "942916570",
            "service_id": service_id,
            "start_at": start.isoformat(),
        },
    )
    token = first.json()["management_token"]
    occupied_start = start.replace(hour=12)
    second = client.post(
        "/api/appointments",
        json={
            "customer_name": "Ana",
            "customer_phone": "942916571",
            "service_id": service_id,
            "start_at": occupied_start.isoformat(),
        },
    )
    assert second.status_code == 201, second.text

    conflict = client.post(
        "/api/appointments/manage/reschedule",
        json={"management_token": token, "start_at": occupied_start.isoformat()},
    )
    assert conflict.status_code == 409

    new_start = start.replace(hour=13)
    moved = client.post(
        "/api/appointments/manage/reschedule",
        json={"management_token": token, "start_at": new_start.isoformat()},
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["start_at"].startswith(new_start.isoformat())
    assert moved.json()["status"] == models.STATUS_PENDING


def test_admin_blocked_interval_is_enforced_and_can_be_removed():
    service_id = client.get("/api/services").json()[0]["id"]
    day = _next_open_day_at(11)
    headers = {"X-Admin-Token": "test-token"}
    payload = {
        "day": day.date().isoformat(),
        "start_time": "12:00",
        "end_time": "13:00",
        "reason": "Almuerzo",
    }
    assert client.get("/api/admin/blocked-times").status_code == 422
    assert client.post("/api/admin/blocked-times", json=payload).status_code == 422

    created = client.post("/api/admin/blocked-times", headers=headers, json=payload)
    assert created.status_code == 201, created.text
    assert created.json()["reason"] == "Almuerzo"

    available = client.get(
        f"/api/availability?service_id={service_id}&date={day.date().isoformat()}"
    ).json()
    assert "11:00" in available
    assert "12:00" not in available
    assert "12:30" not in available
    calendar = client.get(
        f"/api/availability/calendar?service_id={service_id}&month={day.strftime('%Y-%m')}"
    ).json()
    calendar_day = next(item for item in calendar if item["date"] == day.date().isoformat())
    assert calendar_day["status"] == "partial"

    direct_booking = client.post(
        "/api/appointments",
        json={
            "customer_name": "Camila",
            "customer_phone": "942916570",
            "service_id": service_id,
            "start_at": day.replace(hour=12).isoformat(),
        },
    )
    assert direct_booking.status_code == 409

    removed = client.delete(f"/api/admin/blocked-times/{created.json()['id']}", headers=headers)
    assert removed.status_code == 200
    reopened = client.get(
        f"/api/availability?service_id={service_id}&date={day.date().isoformat()}"
    ).json()
    assert "12:00" in reopened


def test_admin_can_block_a_full_day_but_not_overwrite_an_active_appointment():
    service_id = client.get("/api/services").json()[0]["id"]
    day = _next_open_day_at(11)
    headers = {"X-Admin-Token": "test-token"}
    full_day = client.post(
        "/api/admin/blocked-times",
        headers=headers,
        json={"day": day.date().isoformat(), "reason": "Cerrado"},
    )
    assert full_day.status_code == 201, full_day.text
    date_text = day.date().isoformat()
    availability = client.get(f"/api/availability?service_id={service_id}&date={date_text}")
    assert availability.json() == []
    calendar = client.get(
        f"/api/availability/calendar?service_id={service_id}&month={day.strftime('%Y-%m')}"
    ).json()
    calendar_day = next(item for item in calendar if item["date"] == date_text)
    assert calendar_day["status"] == "full"
    direct_booking = client.post(
        "/api/appointments",
        json={
            "customer_name": "Camila",
            "customer_phone": "942916570",
            "service_id": service_id,
            "start_at": day.isoformat(),
        },
    )
    assert direct_booking.status_code == 409

    removed = client.delete(
        f"/api/admin/blocked-times/{full_day.json()['id']}", headers=headers
    )
    assert removed.status_code == 200
    booked = client.post(
        "/api/appointments",
        json={
            "customer_name": "Camila",
            "customer_phone": "942916570",
            "service_id": service_id,
            "start_at": day.isoformat(),
        },
    )
    assert booked.status_code == 201, booked.text
    overlaps_booking = client.post(
        "/api/admin/blocked-times",
        headers=headers,
        json={"day": date_text, "start_time": "11:00", "end_time": "12:00"},
    )
    assert overlaps_booking.status_code == 409


def test_availability_removes_booked_slot():
    sid = client.get("/api/services").json()[0]["id"]
    day = _next_open_day_at(11)
    date_str = day.date().isoformat()

    before = client.get(f"/api/availability?service_id={sid}&date={date_str}").json()
    assert "11:00" in before

    client.post(
        "/api/appointments",
        json={
            "customer_name": "Ana",
            "customer_phone": "942916570",
            "service_id": sid,
            "start_at": day.isoformat(),
        },
    )
    after = client.get(f"/api/availability?service_id={sid}&date={date_str}").json()
    assert "11:00" not in after


def test_month_calendar_shows_partial_days_and_releases_cancelled_bookings():
    service_id = client.get("/api/services").json()[0]["id"]
    day = _next_open_day_at(11)
    month = day.strftime("%Y-%m")
    url = f"/api/availability/calendar?service_id={service_id}&month={month}"

    before = client.get(url)
    assert before.status_code == 200, before.text
    before_day = next(item for item in before.json() if item["date"] == day.date().isoformat())
    assert before_day["status"] == "available"

    booking = client.post(
        "/api/appointments",
        json={
            "customer_name": "Ana",
            "customer_phone": "942916570",
            "service_id": service_id,
            "start_at": day.isoformat(),
        },
    )
    assert booking.status_code == 201, booking.text

    occupied = client.get(url).json()
    occupied_day = next(item for item in occupied if item["date"] == day.date().isoformat())
    assert occupied_day["status"] == "partial"
    assert occupied_day["available_slots"] == before_day["available_slots"] - 1

    cancelled = client.patch(
        f"/api/admin/appointments/{booking.json()['id']}",
        headers={"X-Admin-Token": "test-token"},
        json={"status": models.STATUS_CANCELLED},
    )
    assert cancelled.status_code == 200, cancelled.text
    reopened = client.get(url).json()
    reopened_day = next(item for item in reopened if item["date"] == day.date().isoformat())
    assert reopened_day["status"] == "available"


def test_reject_invalid_phone_on_booking():
    sid = client.get("/api/services").json()[0]["id"]
    start = _next_open_day_at(13)
    r = client.post(
        "/api/appointments",
        json={
            "customer_name": "Mal Tel",
            "customer_phone": "123",
            "service_id": sid,
            "start_at": start.isoformat(),
        },
    )
    assert r.status_code == 422  # falla validación de teléfono


# ---------- Administración ----------
def test_admin_auth():
    assert client.get("/api/admin/appointments").status_code == 422  # falta cabecera
    assert client.get(
        "/api/admin/appointments", headers={"X-Admin-Token": "malo"}
    ).status_code == 401  # token incorrecto
    assert client.get(
        "/api/admin/appointments", headers={"X-Admin-Token": "test-token"}
    ).status_code == 200  # correcto


def test_demand_forecast_uses_weekday_history_and_excludes_cancelled():
    service_id = client.get("/api/services").json()[0]["id"]
    tomorrow = local_now().date() + timedelta(days=1)
    last_week = tomorrow - timedelta(days=7)
    two_weeks_ago = tomorrow - timedelta(days=14)

    db = SessionLocal()
    for day, status, name in [
        (last_week, models.STATUS_CONFIRMED, "Confirmada 1"),
        (last_week, models.STATUS_DONE, "Confirmada 2"),
        (two_weeks_ago, models.STATUS_PENDING, "Pendiente"),
        (last_week, models.STATUS_CANCELLED, "Cancelada"),
    ]:
        start_at = datetime.combine(day, datetime.min.time()).replace(hour=11)
        db.add(
            models.Appointment(
                customer_name=name,
                customer_phone="+56912345678",
                service_id=service_id,
                start_at=start_at,
                end_at=start_at + timedelta(minutes=30),
                status=status,
            )
        )
    db.commit()
    db.close()

    response = client.get(
        "/api/admin/demand-forecast?weeks=4",
        headers={"X-Admin-Token": "test-token"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["history"]) == 28
    assert len(data["forecast"]) == 7
    assert data["forecast"][0]["date"] == tomorrow.isoformat()
    assert data["forecast"][0]["expected_bookings"] == 0.8
    assert data["forecast"][0]["sample_weeks"] == 4
    assert sum(day["bookings"] for day in data["history"]) == 3
    assert data["has_history"] is True


def test_demand_forecast_requires_admin_and_bounds_lookback():
    assert client.get("/api/admin/demand-forecast").status_code == 422
    assert client.get(
        "/api/admin/demand-forecast?weeks=3",
        headers={"X-Admin-Token": "test-token"},
    ).status_code == 422


def test_demand_forecast_without_history_reports_zero_with_no_history_flag():
    response = client.get(
        "/api/admin/demand-forecast?weeks=4",
        headers={"X-Admin-Token": "test-token"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["has_history"] is False
    assert all(day["expected_bookings"] == 0 for day in data["forecast"])
