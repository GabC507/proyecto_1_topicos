# QA MANUAL - Solo verificación (sin modificar nada)

Fecha: 28/10/2026  
Repositorio: `proyecto_1_topicos`  
Ramas remotas verificadas: `main`, `feature/saved-contact-details`, `feature/dynamic-availability-calendar`, `feature/secure-customer-appointment-management`, `feature/admin-blocked-times`

> Nota: No se han ejecutado las pruebas automatizadas por falta de `pytest` en el entorno actual. La verificación se realiza directamente sobre el código de cada rama remota contra la lista de QA enviada.

## Orden de integración
| # | PR | Base | Rama | Estado |
|---|---|---|---|---|
| 1 | #3 | `main` | `feature/saved-contact-details` | Abierto (apilado) |
| 2 | #4 | `feature/saved-contact-details` | `feature/dynamic-availability-calendar` | Abierto (apilado) |
| 3 | #1 | `feature/dynamic-availability-calendar` | `feature/secure-customer-appointment-management` | Abierto (apilado) |
| 4 | #2 | `feature/secure-customer-appointment-management` | `feature/admin-blocked-times` | Abierto (apilado) |

## Evidencia por historia

### PR #3 - Datos guardados con consentimiento
**Archivos revisados:** `frontend/index.html` (rama `feature/saved-contact-details`)

| Caso QA | Verificación en código | Resultado |
|---|---|---|
| Sin consentimiento, recargar | `rememberContact(name, phone)` solo guarda si `#saveContactConsent` está marcado. | **OK (teórico)** |
| Con consentimiento y reserva exitosa, recargar/autocompletar | `readSavedContact()` lee `citafacil_saved_contact` y autocompleta `#name` y `#phone`. | **OK (teórico)** |
| Borrar datos guardados | `forgetSavedContact()` elimina la clave, desmarca checkbox y oculta botón. | **OK (teórico)** |
| Solo guardar contacto / no datos de pago/notas | Solo guarda `{name, phone}`. Notas y datos de pago no se guardan. | **OK (teórico)** |
| Solo en este navegador | Exclusivo con `localStorage`. Sin persistencia server-side. | **OK (teórico)** |

### PR #4 - Calendario de disponibilidad
**Rama:** `feature/dynamic-availability-calendar`

| Caso QA | Verificación en código | Resultado |
|---|---|---|
| Estados disponible/parcial/ocupado/completo/sin horarios | Requiere revisión JS/UI | **No concluyente** |
| Navegar meses / responsive móvil | Requiere revisión CSS/JS | **No concluyente** |
| Día cerrado / sin disponibilidad / error de red | Requiere prueba manual | **No concluyente** |
| Doble intento concurrente / 409 | Backend `POST /api/appointments` valida con `is_slot_free` y retorna 409 | **OK** |

### PR #1 - Cancelar/reprogramar con código privado
**Rama:** `feature/secure-customer-appointment-management`

| Caso QA | Verificación esperada | Resultado |
|---|---|---|
| Código incorrecto/correcto | Debe validar código privado/hash. No debe permitir gestión solo por teléfono. | **Pendiente** |
| Reprogramar a horario libre | Validar disponibilidad + reglas de negocio | **Pendiente** |
| Horario ocupado/pasado/cerrado -> rechazo | Aplicar validaciones | **Pendiente** |
| Cancelar cita futura libera horario | Debe liberar franja al cancelar | **Pendiente** |
| Privacidad: teléfono solo no revela cita | Sin código válido, no debe retornar datos | **Pendiente** |

### PR #2 - Bloqueos admin y corrección teléfono +507
**Rama:** `feature/admin-blocked-times`

| Caso QA | Verificación esperada | Resultado |
|---|---|---|
| Sin token admin: listar/crear/eliminar bloqueos denegado | Endpoints bajo `/api/admin` con `require_admin` | **Consistente con patrón** |
| Intervalo/día completo desaparecen del calendario | Deben integrarse en `generate_slots`/`is_slot_free` | **Pendiente** |
| Reserva directa a API con horario bloqueado -> 409 | `is_slot_free` debe considerar bloqueos | **Pendiente** |
| Retirar bloqueo libera horario | Debe reflejarse en disponibilidad | **Pendiente** |
| Bloquear con cita activa -> rechazado sin cambiar cita | Debe validar citas vigentes | **Pendiente** |
| +507 6123 4567 aceptado y normalizado | Validación/normalización +507 | **Pendiente** |
| Teléfono inválido -> error por campo/motivo, conserva hora | Validación clara sin perder selección | **Pendiente** |

### Previsión - `main`
**Archivos revisados:** `backend/app/forecast.py`, `backend/app/routers/admin.py`, `backend/tests/test_booking.py`

| Caso QA | Verificación en código | Resultado |
|---|---|---|
| Sin historial -> indica falta de datos | `has_history=false`, mensaje correcto | **OK** |
| Con datos demo -> promedio mismo día semana, excluye canceladas | Lógica correcta, cubierto por tests | **OK** |
| Sin token admin -> denegado / con token -> carga | Usa `require_admin` | **OK** |
| Móvil/escritorio | Depende de UI | **No concluyente** |

## Veredicto
- **#3:** Coherente con checklist. Pendiente confirmar llamada a `rememberContact()` en submit exitoso.
- **#4:** Backend OK. UX/estados requieren prueba en navegador.
- **#1:** Crítico validar que no sea posible gestionar por teléfono solo. Requiere revisión completa del diff.
- **#2:** Crítico integrar bloqueos en `availability` y validar normalización +507.
- **main (Previsión):** Cumple criterios técnicos.

**Gate:** Evidencia QA por PR + aprobación Reviewer + comentarios bloqueantes resueltos + tests pasando. Respetar orden **#3 → #4 → #1 → #2**.
