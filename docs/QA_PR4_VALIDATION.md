# QA automatizada - PR #4

Fecha: 28/10/2026  
Rama: `feature/dynamic-availability-calendar`  
Base del PR: `feature/saved-contact-details`

## Comprobaciones ejecutadas

| Caso | Comando o pasos automatizados | Resultado |
|---|---|---|
| El cambio de servicio invalida una consulta de horarios en curso | `node --test frontend/tests/request-sequence.test.cjs` | Pass |
| El cambio de mes invalida una consulta de horarios en curso | `node --test frontend/tests/request-sequence.test.cjs` | Pass |
| Una respuesta demorada de la fecha anterior no reemplaza horarios recientes | Prueba con promesa diferida en `frontend/tests/request-sequence.test.cjs` | Pass; se conservan los horarios de la última solicitud |
| Día completamente ocupado | Desde `backend/`: `python -m pytest -q tests/test_booking.py` | Pass; `status=full`, `available_slots=0` |
| Día cerrado, sin atención | Desde `backend/`: `python -m pytest -q tests/test_booking.py` | Pass; `status=unavailable`, `available_slots=0` |

## Resultado de la suite

En el entorno de desarrollo con Python 3.12:

```text
18 passed, 36 warnings
2 frontend request-sequence tests passed
```

Las advertencias son deprecaciones de dependencias y de `datetime.utcnow()`; no fallaron pruebas.

## Alcance

La validación de esta revisión cubre el control de respuestas obsoletas y los dos estados de calendario solicitados por Reviewer. No se registran aquí pruebas manuales en navegador ni capturas visuales nuevas.
