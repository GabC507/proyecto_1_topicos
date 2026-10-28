# AI Development Log

## Registro inicial del proyecto

Registrar solo las interacciones de IA que afectaron decisiones o cambios importantes. No completar los casos de error o rechazo con ejemplos inventados: anotar lo que ocurra al revisar y probar el código.

| Actividad | Herramienta | Solicitud / uso | Resultado | Decisión humana |
|---|---|---|---|---|
| Análisis inicial | OpenCode | Revisar la estructura y el flujo existente antes de modificarlo | Identificó FastAPI, SQLAlchemy, rutas administrativas protegidas y pruebas pytest | Se conservaron las capas existentes; no se modificó el flujo de reservas |
| Previsión de demanda | OpenCode | Implementar una historia de usuario con endpoint, gráfico y pruebas | Endpoint protegido que promedia reservas no canceladas por día de la semana; gráfico sin librería adicional | Pendiente: Reviewer debe comprobar el algoritmo y QA debe ejecutar las pruebas antes de aceptar el cambio |
| Verificación en Windows | OpenCode | Preparar el entorno y ejecutar las pruebas automatizadas | Python 3.14.3 no pudo instalar las versiones fijadas de `pydantic-core` y `psycopg2-binary` porque intentó compilarlas sin las herramientas nativas requeridas. Con Python 3.12.10 se instalaron las dependencias. La primera ejecución de pytest encontró que `/tmp` se resolvía como `C:\tmp`; se cambió la base de pruebas para usar la carpeta temporal del sistema. Resultado final: 9 pruebas pasaron; `/health` respondió 200 durante la verificación. | Se usó Python 3.12.10, coherente con `render.yaml`; la base de datos de pruebas quedó portable para Windows. La revisión independiente y QA manual del equipo siguen pendientes. Los datos de demostración se cargaron en la base local. |
| Historias restantes | OpenCode | Implementar datos guardados, calendario dinámico, gestión segura de citas y bloqueos de horario en cambios separados | Las cuatro historias quedaron en ramas locales separadas; las pruebas automatizadas del backend pasan con Python 3.12.6. No se hizo QA visual/manual. | Se mantuvo el contacto en el navegador con consentimiento y borrado; para gestionar citas se usa un código aleatorio y solo se almacena su hash. El usuario reservó la QA funcional para sí; Reviewer y QA del equipo aún deben validar los PR. |
| Validación de celular panameño | OpenCode | Investigar un HTTP 422 al reservar desde el frontend | Se encontró que solo se normalizaban teléfonos chilenos y que la UI mostraba el detalle estructurado de validación como `[object Object]`. Se agregó soporte E.164 `+507`, mensajes de validación legibles y conservación del horario seleccionado para reintentar. | El usuario pidió mantener Chile y habilitar números panameños con prefijo `+507`. | 22 pruebas backend aprobadas; flujo local con teléfono inválido `422`, corrección a `+507` y reserva exitosa `201`. |

## Iteración integrada de previsión · 2026-10-25

No se almacenan prompts completos, tokens ni datos reales de clientes.

| Fecha | Actividad | Herramienta | Solicitud / resultado | Decisión humana | Validación |
|---|---|---|---|---|---|
| 2026-10-25 | Análisis de historias | OpenCode (asistente de IA) | Comparó la guía del curso, el plan del equipo y el repositorio; detectó que el feature de previsión indicado en el plan no existía en el código. | El equipo confirmó que la primera historia a implementar sería previsión de demanda. | Se verificaron el estado de `main`, `feature/demand-forecast`, el endpoint administrativo y el panel. |
| 2026-10-25 | Diseño | OpenCode (asistente de IA) | Propuso promedio por día de semana de las últimas ocho semanas, token administrativo, siete fechas futuras, exclusión de cancelaciones y estado sin historial; presentó opciones visuales. | El equipo aprobó ocho semanas, el gráfico semanal A y el endpoint administrativo propuesto. | Especificación revisada y aprobada en `docs/superpowers/specs/2026-10-25-demand-forecast-design.md`. |
| 2026-10-25 | Implementación y pruebas | OpenCode (asistente de IA) | Implementó cálculo aislado, endpoint FastAPI, pruebas automatizadas y gráfico responsive; hizo portable la ruta de la base de pruebas al encontrar que `/tmp` no existe como `C:\tmp` en Windows. | El equipo autorizó continuar con la primera implementación y su commit. | `python -m pytest` desde `backend/`: 12 pruebas aprobadas; comprobación sintáctica del JavaScript inline. |
| 2026-10-25 | Revisión del cambio | Reviewer IA | Detectó que la explicación del gráfico no aclaraba el promedio del mismo día de semana y señaló la altura mínima que dibujaba barras para ceros; también recomendó fijar los límites de fechas en pruebas. | Se actualizaron el texto, la representación de cero y las pruebas para el inicio de ventana, hoy y fechas futuras. | `python -m pytest` desde `backend/`: 12 pruebas aprobadas después de los ajustes. |
| 2026-10-25 | Evidencia visual | PowerShell / Windows | Capturó ventanas aisladas del panel con datos sintéticos de demostración para escritorio y móvil. | El equipo pidió guardar capturas como evidencia de QA; se usaron solo datos demo. | Imágenes en `docs/demand-forecast-desktop.png` y `docs/demand-forecast-mobile.png`. |

## Errores de IA y cambios rechazados

Los hallazgos de revisión de esta iteración se corrigieron y se verificaron con pruebas. No se registran cambios de código rechazados en esta iteración.
