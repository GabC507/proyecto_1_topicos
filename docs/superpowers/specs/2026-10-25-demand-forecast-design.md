# Diseño: previsión de demanda

## Objetivo

Completar la historia del Sprint 1 para que el administrador consulte una estimación sencilla de reservas para los próximos siete días y pueda entender de qué datos se deriva. La estimación es descriptiva y no debe presentarse como una predicción confiable cuando no hay historial.

## Historia de usuario

Como administrador, quiero ver la demanda estimada por día de la semana, calculada a partir de reservas históricas, para orientar decisiones de capacidad y precios.

## Diseño aprobado

### API y cálculo

- Exponer `GET /api/admin/forecast?history_weeks=8` desde la API administrativa existente. Hereda el requisito de `X-Admin-Token` del router de administración.
- Validar `history_weeks` en el intervalo inclusivo de 1 a 52 semanas; el valor predeterminado es 8.
- Mantener el cálculo aislado en `backend/app/forecast.py` para que pueda probarse aparte de HTTP.
- Usar la fecha local del negocio y reservas con `start_at` en los días históricos completos previos a hoy. Las fechas futuras y el día actual no forman parte del historial.
- Para cada una de las próximas siete fechas completas (desde mañana), calcular el promedio de reservas del mismo día de la semana en las últimas `history_weeks` semanas. Cada fecha histórica de ese mismo día de la semana cuenta en el denominador, incluso si tuvo cero reservas.
- Excluir citas con estado `cancelled`; considerar los demás estados como demanda histórica.
- Conservar el promedio como número decimal en la respuesta, en vez de redondear la estimación al número entero de citas.

Respuesta con historial:

```json
{
  "has_history": true,
  "history_weeks": 8,
  "forecast_start": "YYYY-MM-DD",
  "forecast_end": "YYYY-MM-DD",
  "estimates": [
    {
      "date": "YYYY-MM-DD",
      "weekday": "lunes",
      "average_appointments": 1.25
    }
  ],
  "message": null
}
```

Cuando no haya reservas no canceladas dentro de la ventana histórica, devolver `has_history: false`, `estimates: []` y un mensaje explícito de que no hay historial suficiente. No inventar valores ni mostrar barras de predicción en ese caso.

### Panel de administración

- Añadir una tarjeta de previsión al panel existente `frontend/admin.html`, usando la API y el token que ya maneja el panel.
- Presentar siete barras responsivas, una por fecha futura, con etiqueta del día y promedio numérico. Añadir una nota de que se usa un promedio histórico del mismo día de semana, el período analizado y que las cancelaciones se excluyen.
- No agregar dependencia externa de gráficos; dibujar las barras con HTML/CSS para mantener el frontend liviano.
- Mostrar estados visibles de carga, ausencia de historial y error de red/API. Mantener la presentación utilizable en móvil y escritorio.

## Criterios de aceptación

1. Sin `X-Admin-Token`, el endpoint no devuelve previsiones; con token inválido responde no autorizado.
2. Con token válido, el endpoint produce siete fechas futuras consecutivas, comenzando mañana según fecha local.
3. Cada promedio usa únicamente el mismo día de semana dentro del período seleccionado; los días sin reservas cuentan como cero.
4. Las citas canceladas y las fechas de hoy/futuras no alteran los promedios históricos.
5. `history_weeks` por defecto es 8; valores menores que 1 o mayores que 52 se rechazan con validación HTTP.
6. Si no hay historial elegible, el endpoint indica `has_history: false` y el panel comunica que no hay datos suficientes sin presentar un gráfico engañoso.
7. El panel muestra las siete estimaciones y comunica el período y la exclusión de cancelaciones; sus estados de error/carga no dejan contenido engañoso.
8. El gráfico se adapta a móvil y escritorio.

## Estrategia de pruebas y revisión

- Pruebas de API: autenticación ausente/incorrecta, ventana predeterminada y límites, fechas devueltas y período futuro excluido, promedio por semana-día, reservas canceladas excluidas e historial vacío.
- Probar la función de cálculo con fechas controladas para que el resultado sea determinista.
- QA ejecuta `python -m pytest` desde `backend/` y revisa el panel en escritorio y móvil con historial y sin historial.
- Reviewer verifica protección administrativa, límites de fechas, denominador del promedio, exclusión de cancelaciones y claridad del estado vacío/gráfico.

## Fuera de alcance

- Guardar datos de contacto, calendario dinámico, cancelar/reprogramar citas y bloquear horarios.
- Modelos estadísticos avanzados, recomendaciones automáticas de precios/inventario o garantías de precisión.
- Cambios al esquema de base de datos.
