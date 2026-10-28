# Plan de trabajo del equipo

**Proyecto 1 - Tópicos Especiales II**  
**Equipo:** tres estudiantes  
**Aplicación base:** CitaFácil (`gianca675/citafacil`)

## Objetivo

Mejorar una aplicación existente de reservas usando herramientas de IA desde el escritorio y prácticas reales de ingeniería. La meta no es generar mucho código, sino entregar historias funcionales, probadas y revisadas, y dejar evidencia de las decisiones humanas.

## Historias a entregar

1. **Datos guardados:** como cliente recurrente, quiero reutilizar mis datos de contacto al reservar para no ingresarlos cada vez.
2. **Calendario:** como cliente, quiero distinguir horarios disponibles y ocupados para elegir una hora sin intentar reservar una ya tomada.
3. **Previsión:** como administrador, quiero ver la demanda estimada desde las reservas históricas para planificar horarios y cupos.
4. **Adicional, cancelación o reprogramación:** como cliente, quiero gestionar mi cita conforme a las reglas del negocio. La aplicación debe verificar que la persona está autorizada; no se debe dar acceso a una cita solo con conocer un teléfono.
5. **Adicional, bloqueo de horario:** como administrador, quiero bloquear fechas u horas no disponibles para que no se ofrezcan en el calendario.

Para la historia de datos guardados, limitarse a nombre y contacto con consentimiento y opción para borrar los datos guardados. No guardar números ni códigos de tarjetas. Si en el futuro se integra pago, usar un proveedor que tokenice el medio de pago. Si se guardan perfiles en el servidor, definir autenticación antes de implementarlo.

## Reparto de roles

Los roles son por sprint, no cargos permanentes. El Developer implementa y entrega la historia; el Reviewer revisa el cambio y aprueba o solicita correcciones; QA prueba los criterios de aceptación y reporta evidencia. Todos deben poder explicar el sistema completo.

| Sprint | Developer | Reviewer | QA | Trabajo principal |
|---|---|---|---|---|
| 1 | Tú | Compañero/a 2 | Compañero/a 3 | Previsión de demanda y gráfico administrativo |
| 2 | Compañero/a 2 | Compañero/a 3 | Tú | Datos de cliente guardados y cancelación/reprogramación segura |
| 3 | Compañero/a 3 | Tú | Compañero/a 2 | Calendario dinámico y bloqueo de horarios |

### Responsabilidades del sprint actual

- **Tú, Developer:** la previsión está integrada en `main`. Las otras cuatro historias están implementadas en ramas locales apiladas, una por historia. La suite automatizada pasa; falta QA funcional independiente y revisión de los PR.
- **Compañero/a 2, Reviewer:** revisar la previsión y cada historia nueva en su PR. Comprobar autorización, privacidad, criterios de aceptación y pruebas; registrar comentarios antes de aprobar.
- **Compañero/a 3, QA:** verificar previsión, datos guardados, calendario, gestión segura de citas y bloqueos en escritorio y móvil. Adjuntar pasos, resultados y capturas relevantes.

## Cómo trabajaremos cada historia

1. Crear un Issue con la historia, criterios de aceptación y casos límite.
2. Analizar el flujo actual antes de pedirle a la IA que modifique código.
3. Crear una rama `feature/<issue>-<descripcion>` desde la rama principal.
4. Hacer un cambio pequeño y pedir a la IA tareas concretas. Revisar el código y no aceptar una respuesta solo porque compile.
5. Ejecutar pruebas automatizadas y pruebas manuales de aceptación.
6. Abrir un Pull Request, solicitar al Reviewer y a QA que dejen resultados y observaciones, y corregir antes de integrar.
7. Integrar solo cambios revisados y dejar commits identificables.

## Pruebas y criterios importantes

- Una franja ocupada o bloqueada no aparece como disponible y tampoco se puede reservar enviando una petición directa a la API.
- Dos reservas que se solapan no pueden confirmarse; las citas canceladas dejan de bloquear disponibilidad.
- Las acciones de administración requieren el token. Los datos personales no se consultan solo por teléfono.
- El calendario muestra estados claros, funciona en móvil y muestra un mensaje útil cuando no hay disponibilidad.
- La previsión excluye cancelaciones, indica el periodo usado y no aparenta certeza si no hay historial.
- Revisar flujos normales, datos inválidos, errores de red y ausencia de datos.

## Uso de IA y evidencia

Mantener `AI_DEVELOPMENT_LOG.md` con usos significativos, resultados y decisiones humanas. Registrar respuestas incorrectas y cambios rechazados solo cuando hayan ocurrido de verdad: explicar qué propuso la IA, por qué se rechazó y cómo se verificó la decisión. No inventar evidencia ni incluir secretos, tokens o datos personales.

## Acciones inmediatas

- Asignar los nombres reales a Compañero/a 2 y Compañero/a 3 y confirmar la rotación.
- Confirmar Issues y criterios de aceptación para las cinco historias; el repositorio del equipo está configurado como remoto.
- Publicar las ramas de las cuatro historias nuevas y abrir PRs en orden. La previsión ya está en `main`, por lo que no tiene un PR pendiente.
- Ejecutar QA funcional de todos los flujos antes de integrar los PRs; no subir cambios al repositorio original del autor.
- Preparar datos históricos de prueba para la demostración de la previsión; no insertar datos ficticios en producción.
- Preparar a los tres integrantes para presentar y responder preguntas sobre arquitectura, pruebas y decisiones de IA.
