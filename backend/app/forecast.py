"""Cálculo de previsión de demanda usando reservas históricas."""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Iterable


WEEKDAYS_ES = (
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
)
NO_HISTORY_MESSAGE = "Aún no hay historial de reservas suficiente para calcular una previsión."


def build_demand_forecast(
    appointments: Iterable,
    today: date,
    history_weeks: int,
) -> dict:
    """Estima reservas para los próximos siete días completos.

    Para cada fecha futura, promedia el número de reservas de la misma semana-
    día en las últimas ``history_weeks`` semanas. Los días sin reservas cuentan
    como cero y las citas canceladas no forman parte del historial.
    """
    window_start = today - timedelta(days=history_weeks * 7)
    counts_by_date = Counter()
    eligible_count = 0

    for appointment in appointments:
        appointment_date = appointment.start_at.date()
        if (
            appointment.status != "cancelled"
            and window_start <= appointment_date < today
        ):
            counts_by_date[appointment_date] += 1
            eligible_count += 1

    forecast_dates = [today + timedelta(days=offset) for offset in range(1, 8)]
    estimates = []
    if eligible_count:
        for forecast_date in forecast_dates:
            days_since_matching_weekday = (today.weekday() - forecast_date.weekday()) % 7
            if days_since_matching_weekday == 0:
                days_since_matching_weekday = 7
            latest_matching_date = today - timedelta(days=days_since_matching_weekday)
            sample_dates = [
                latest_matching_date - timedelta(days=7 * week)
                for week in range(history_weeks)
            ]
            average = sum(counts_by_date[day] for day in sample_dates) / history_weeks
            estimates.append(
                {
                    "date": forecast_date.isoformat(),
                    "weekday": WEEKDAYS_ES[forecast_date.weekday()],
                    "average_appointments": float(average),
                }
            )

    return {
        "has_history": bool(eligible_count),
        "history_weeks": history_weeks,
        "forecast_start": forecast_dates[0].isoformat(),
        "forecast_end": forecast_dates[-1].isoformat(),
        "estimates": estimates,
        "message": None if eligible_count else NO_HISTORY_MESSAGE,
    }
