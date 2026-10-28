"""Utilidades: validación de teléfonos y manejo de fechas locales."""
from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import settings


class PhoneError(ValueError):
    """Error de validación de número telefónico."""


def normalize_phone(raw: str) -> str:
    """Normaliza teléfonos chilenos y panameños a formato E.164.

    Los números panameños deben incluir +507; los chilenos conservan sus
    formatos nacionales e internacionales anteriores.
    """
    digits = re.sub(r"[^\d]", "", raw or "")
    if digits.startswith("507"):
        number = digits[3:]
        if len(number) == 8 and number[0] in "23456789":
            return "+507" + number
        raise PhoneError("Número panameño inválido. Usa +507 seguido de 8 dígitos.")
    if digits.startswith("56"):          # prefijo país
        digits = digits[2:]
    if digits.startswith("0"):           # 0 de larga distancia
        digits = digits[1:]
    if len(digits) == 8:                 # faltó el 9 inicial del móvil
        digits = "9" + digits
    if len(digits) != 9 or not digits.startswith("9"):
        raise PhoneError(
            "Número de celular chileno inválido. Usa el formato +56 9 XXXX XXXX."
        )
    return "+56" + digits


def format_cl_phone(e164: str) -> str:
    """Formatea +56912345678 -> '+56 9 1234 5678' para mostrar."""
    d = e164.replace("+56", "")
    if len(d) == 9:
        return f"+56 {d[0]} {d[1:5]} {d[5:]}"
    return e164


def local_now() -> datetime:
    """Hora actual del negocio (naive, en la zona horaria configurada)."""
    return datetime.now(ZoneInfo(settings.business_timezone)).replace(tzinfo=None)


def to_local_naive(dt: datetime) -> datetime:
    """Convierte un datetime con zona a hora local naive; deja los naive igual."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(ZoneInfo(settings.business_timezone)).replace(tzinfo=None)
    return dt
