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
