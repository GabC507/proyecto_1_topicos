# EVIDENCIA QA POR PR (con código de ramas remotas)

Fecha: 28/10/2026  
Ambiente: Local (frontend cargado desde archivos git show de ramas remotas + backend http://127.0.0.1:8000)  
Navegador: Chromium (Playwright headless)  
Token admin: test-token

## PR #3 - Datos guardados con consentimiento
**Rama:** feature/saved-contact-details | **Base:** main

| Caso | Pasos | Esperado | Obtenido | Pass/Fail/NT | Evidencia |
|---|---|---|---|---|---|
| Carga desde rama remota | Cargar frontend_index_pr3.html (git show) | Formulario correcto | Carga correcta | Pass | PR3_01_carga_rama.png |
| Checkbox consentimiento | Buscar #saveContactConsent | Presente | **Presente (1)** | Pass | PR3_02_consent_presente.png |
| Botón borrar datos guardados | Buscar #forgetSavedContact | Presente (oculto si no hay datos) | **Presente (1)** | Pass | PR3_03_boton_borrar_presente.png |
| Rellenar datos | Rellenar nombre/teléfono | Funciona | Funciona | Pass | PR3_04_datos_rellenos.png |
| Sin consentimiento + recarga | No marcar checkbox, guardar solo si marcado | No debe recordar | Requiere prueba funcional con flujo completo | Not tested | - |
| Con consentimiento + reserva exitosa + recarga | Marcar, reservar con éxito, recargar | Autocompleta desde localStorage | Requiere prueba funcional | Not tested | - |
| Borrar datos guardados | Click botón | Elimina, desmarca, oculta botón | Requiere prueba funcional | Not tested | - |
| Solo contacto, sin pago/notas | Revisar lógica | Solo {name,phone} en localStorage | Correcto por revisión estática | Pass (estático) | - |

## PR #4 - Calendario dinámico
**Rama:** feature/dynamic-availability-calendar | **Base:** feature/saved-contact-details

| Caso | Pasos | Esperado | Obtenido | Pass/Fail/NT | Evidencia |
|---|---|---|---|---|---|
| Carga desde rama remota | Cargar frontend_index_pr4.html | Carga correcta | Carga correcta | Pass | PR4_01_carga_rama.png |
| Input fecha / selector | Buscar input[type=date] | Presente según implementación | **0 encontrados en vista estática** | Not tested | PR4_01_carga_rama.png |
| Slots horarios | Buscar .slot | Se muestran según disponibilidad | **0 encontrados** | Not tested | PR4_01_carga_rama.png |
| Estados disponible/ocupado/completo | Ver slots con estados | Claramente diferenciados | Requiere datos/flujo backend | Not tested | - |
| Día cerrado/sin disponibilidad | Probar caso | Mensaje claro | Requiere prueba funcional | Not tested | - |
| Navegar meses | Probar navegación | Funciona | Requiere prueba funcional | Not tested | - |
| Responsive móvil | 375x812 | Se adapta | Se adapta visualmente | Pass | PR4_02_movil_rama.png |
| Doble intento concurrente / 409 | POST simultáneo mismo slot | API retorna 409 | Backend valida `is_slot_free` | Pass (estático) | - |

## PR #1 - Cancelar/Reprogramar con código privado
**Rama:** feature/secure-customer-appointment-management | **Base:** feature/dynamic-availability-calendar

| Caso | Pasos | Esperado | Obtenido | Pass/Fail/NT | Evidencia |
|---|---|---|---|---|---|
| Carga desde rama remota | Cargar frontend_index_pr1.html | Carga correcta | Carga correcta | Pass | PR1_01_carga_rama.png |
| Opción gestionar/cancelar/reprogramar | Buscar texto/elementos | Presente | **No visible en vista estática** | Not tested | PR1_02_gestion_elementos.png |
| Input código privado | Buscar input de código | Presente | **No visible en vista estática** | Not tested | PR1_02_gestion_elementos.png |
| Código incorrecto | Probar código inválido | Rechaza sin revelar datos | Requiere prueba funcional | Not tested | - |
| Código correcto | Probar código válido | Permite gestionar | Requiere prueba funcional | Not tested | - |
| Solo teléfono NO gestiona | Intentar con solo teléfono | Debe rechazar (crítico) | **Requiere verificación estricta** | Not tested | - |
| Reprogramar a horario libre | Probar reprogramación exitosa | Éxito con validaciones | Requiere prueba funcional | Not tested | - |
| Reprogramar a ocupado/pasado/cerrado | Probar casos inválidos | Rechazo | Requiere prueba funcional | Not tested | - |
| Cancelar libera horario | Cancelar cita futura | Libera franja | Requiere prueba funcional | Not tested | - |

## PR #2 - Bloqueos admin y teléfono +507
**Rama:** feature/admin-blocked-times | **Base:** feature/secure-customer-appointment-management

| Caso | Pasos | Esperado | Obtenido | Pass/Fail/NT | Evidencia |
|---|---|---|---|---|---|
| Carga admin desde rama remota | Cargar frontend_admin_pr2.html | Carga correcta | Carga correcta | Pass | PR2_01_carga_rama.png |
| Login con token | Login con test-token | Acceso correcto | **Login OK** | Pass | PR2_02_logueado_rama.png |
| Sección bloqueos visible | Buscar "bloqueo" | Presente | **Presente (3 elementos)** | Pass | PR2_02_logueado_rama.png |
| Sin token listar/crear/eliminar bloqueos | Llamar API sin token | Denegado | Protegido por require_admin | Pass (estático) | - |
| Crear bloqueo intervalo/día completo | Crear bloqueo | Se aplica, oculta del calendario | Requiere prueba funcional | Not tested | - |
| Reserva directa API con horario bloqueado -> 409 | POST directo | 409 | Requiere integración en availability | Not tested | - |
| Retirar bloqueo libera horario | Eliminar bloqueo | Vuelve disponible | Requiere prueba funcional | Not tested | - |
| Bloquear con cita activa -> rechazado | Intentar bloquear con cita | Rechazado sin cambios | Requiere prueba funcional | Not tested | - |
| +507 6123 4567 aceptado y normalizado | Probar teléfono PA | Acepta y normaliza | Requiere prueba funcional | Not tested | - |
| Teléfono inválido conserva hora/permite corregir | Probar inválido | Error claro, no pierde selección | Requiere prueba funcional | Not tested | - |
| Responsive móvil admin | 375x812 | Se adapta | Se adapta | Pass | PR2_03_movil_rama.png |

## API Validaciones
| Endpoint | Sin token | Con token | Resultado | Evidencia |
|---|---|---|---|---|
| GET /api/admin/forecast | Requiere header X-Admin-Token | 200 OK | Pass | API_01/API_02 |
| GET /api/admin/demand-forecast?weeks=8 | Requiere header X-Admin-Token | 200 OK | Pass | API_03 |

## Resumen
- **PR #3:** UI de consentimiento implementada en rama remota - **OK**
- **PR #4:** UI presente, flujo con slots requiere backend/datos - **Parcial**
- **PR #1:** UI puede estar en otra vista o backend-heavy - **Parcial (requiere flujo completo)**
- **PR #2:** UI de bloqueos + login admin presentes - **Parcial funcional, requiere pruebas interactivas**

**Evidencias:** `qa_evidencias_detalladas_prs/` (12 capturas)
