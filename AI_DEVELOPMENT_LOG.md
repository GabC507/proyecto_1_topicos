# AI Development Log

Registrar solo las interacciones de IA que afectaron decisiones o cambios importantes. No completar los casos de error o rechazo con ejemplos inventados: anotar lo que ocurra al revisar y probar el código.

| Actividad | Herramienta | Solicitud / uso | Resultado | Decisión humana |
|---|---|---|---|---|
| Análisis inicial | OpenCode | Revisar la estructura y el flujo existente antes de modificarlo | Identificó FastAPI, SQLAlchemy, rutas administrativas protegidas y pruebas pytest | Se conservaron las capas existentes; no se modificó el flujo de reservas |
| Previsión de demanda | OpenCode | Implementar una historia de usuario con endpoint, gráfico y pruebas | Endpoint protegido que promedia reservas no canceladas por día de la semana; gráfico sin librería adicional | Pendiente: Reviewer debe comprobar el algoritmo y QA debe ejecutar las pruebas antes de aceptar el cambio |
| Verificación en Windows | OpenCode | Preparar el entorno y ejecutar las pruebas automatizadas | Python 3.14.3 no pudo instalar las versiones fijadas de `pydantic-core` y `psycopg2-binary` porque intentó compilarlas sin las herramientas nativas requeridas. Con Python 3.12.10 se instalaron las dependencias. La primera ejecución de pytest encontró que `/tmp` se resolvía como `C:\tmp`; se cambió la base de pruebas para usar la carpeta temporal del sistema. Resultado final: 9 pruebas pasaron; `/health` respondió 200 durante la verificación. | Se usó Python 3.12.10, coherente con `render.yaml`; la base de datos de pruebas quedó portable para Windows. La revisión independiente y QA manual del equipo siguen pendientes. Los datos de demostración se cargaron en la base local. |

## Errores de IA y cambios rechazados

Completar durante la revisión del equipo con evidencia real. Para cada caso, registrar qué propuso la IA, por qué era incorrecto o riesgoso y qué decisión tomó el equipo. No hay todavía un caso verificado en esta primera iteración.
