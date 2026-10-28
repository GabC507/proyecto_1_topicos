# Previsión de demanda Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar una previsión administrativa de siete días basada en el promedio histórico del mismo día de semana, excluir cancelaciones y presentarla en el panel.

**Architecture:** Un cálculo aislado en `backend/app/forecast.py` recibe reservas y una fecha controlada; el router administrativo existente consulta la ventana histórica y lo expone con token. El panel HTML obtiene el endpoint con su token y dibuja barras CSS responsivas, incluyendo estados de carga, error y falta de historial.

**Tech Stack:** Python 3, FastAPI, SQLAlchemy, pytest, HTML/CSS/JavaScript sin framework.

---

## Archivos y responsabilidades

- `backend/app/forecast.py` (nuevo): cálculo puro, con fecha explícita, promedio por día de semana y respuesta sin historial.
- `backend/app/routers/admin.py`: endpoint protegido y consulta del período histórico.
- `backend/tests/test_booking.py`: pruebas de cálculo, autenticación, validación del período y respuesta HTTP.
- `frontend/admin.html`: tarjeta, estilos y carga/renderizado del gráfico.
- `docs/superpowers/specs/2026-10-25-demand-forecast-design.md`: especificación aprobada.
- `docs/superpowers/plans/2026-10-25-demand-forecast.md`: este plan.
- `AI_DEVELOPMENT_LOG.md`: registro factual del uso significativo de IA para esta historia.
- `docs/demand-forecast-desktop.png` y `docs/demand-forecast-mobile.png`: evidencia visual QA capturada con PowerShell usando solo la ventana demo.

## Task 1: Preparar la base de pruebas y escribir pruebas que fallen primero

**Files:**
- Modify: `backend/tests/test_booking.py`

- [ ] **Step 1: Usar el directorio temporal del sistema para la base de pruebas**

En `backend/tests/test_booking.py`, configurar `DATABASE_URL` antes de importar la aplicación:

```python
import tempfile
from pathlib import Path

TEST_DB_PATH = Path(tempfile.gettempdir()) / "citafacil_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
```

Esto conserva una base aislada y permite que pytest funcione tanto en Windows como en POSIX.

- [ ] **Step 2: Añadir pruebas unitarias para promedio, cancelación y fechas fuera del historial**

Añadir imports `date`, `datetime`, `time` y `SimpleNamespace`; mantener la importación del cálculo dentro de una función auxiliar para que el estado RED sea un test fallido y no un error de colección:

```python
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
```

A continuación añadir:

```python
def _forecast_appointment(day, status="pending"):
    return SimpleNamespace(
        start_at=datetime.combine(day, time(10, 0)),
        status=status,
    )


def _build_demand_forecast(appointments, today, history_weeks):
    from app.forecast import build_demand_forecast

    return build_demand_forecast(appointments, today, history_weeks)


def test_forecast_averages_same_weekday_and_ignores_cancelled_and_future():
    appointments = [
        _forecast_appointment(date(2026, 10, 11)),
        _forecast_appointment(date(2026, 10, 11)),
        _forecast_appointment(date(2026, 10, 12)),
        _forecast_appointment(date(2026, 10, 12)),
        _forecast_appointment(date(2026, 10, 12), "cancelled"),
        _forecast_appointment(date(2026, 10, 19), "done"),
        _forecast_appointment(date(2026, 10, 19), "done"),
        _forecast_appointment(date(2026, 10, 19), "done"),
        _forecast_appointment(date(2026, 10, 19), "done"),
        _forecast_appointment(date(2026, 10, 19), "cancelled"),
        _forecast_appointment(date(2026, 10, 25)),
        _forecast_appointment(date(2026, 10, 27)),
    ]

    result = _build_demand_forecast(
        appointments, today=date(2026, 10, 25), history_weeks=2
    )

    assert result["has_history"] is True
    assert result["forecast_start"] == "2026-10-26"
    assert result["forecast_end"] == "2026-11-01"
    assert len(result["estimates"]) == 7
    assert result["estimates"][0] == {
        "date": "2026-10-26",
        "weekday": "lunes",
        "average_appointments": 3.0,
    }
    assert result["estimates"][1]["average_appointments"] == 0.0
    assert result["estimates"][-1]["average_appointments"] == 1.0


def test_forecast_returns_empty_estimates_without_eligible_history():
    result = _build_demand_forecast(
        [
            _forecast_appointment(date(2026, 10, 20), "cancelled"),
            _forecast_appointment(date(2026, 10, 25)),
            _forecast_appointment(date(2026, 10, 27)),
        ],
        today=date(2026, 10, 25),
        history_weeks=2,
    )

    assert result["has_history"] is False
    assert result["estimates"] == []
    assert result["message"] == "Aún no hay historial de reservas suficiente para calcular una previsión."
```

- [ ] **Step 3: Ejecutar las pruebas nuevas y confirmar que fallan por el módulo aún no implementado**

Run desde `backend/`: `python -m pytest tests/test_booking.py -k forecast -q`

Expected: FAIL al importar `app.forecast`; todavía no hay implementación.

## Task 2: Implementar el cálculo aislado

**Files:**
- Create: `backend/app/forecast.py`
- Test: `backend/tests/test_booking.py`

- [ ] **Step 1: Crear la función pura `build_demand_forecast`**

Implementar esta lógica en `backend/app/forecast.py`:

```python
from collections import Counter
from datetime import date, timedelta

WEEKDAYS_ES = (
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"
)


def build_demand_forecast(appointments, today: date, history_weeks: int) -> dict:
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
            estimates.append({
                "date": forecast_date.isoformat(),
                "weekday": WEEKDAYS_ES[forecast_date.weekday()],
                "average_appointments": float(average),
            })

    return {
        "has_history": bool(eligible_count),
        "history_weeks": history_weeks,
        "forecast_start": forecast_dates[0].isoformat(),
        "forecast_end": forecast_dates[-1].isoformat(),
        "estimates": estimates,
        "message": None if eligible_count else (
            "Aún no hay historial de reservas suficiente para calcular una previsión."
        ),
    }
```

- [ ] **Step 2: Ejecutar las pruebas puras hasta que pasen**

Run desde `backend/`: `python -m pytest tests/test_booking.py -k forecast -q`

Expected: PASS para promedio semanal, exclusión de cancelaciones/futuro y ausencia de historial.

## Task 3: Exponer la API administrativa y probar HTTP

**Files:**
- Modify: `backend/app/routers/admin.py`
- Modify: `backend/tests/test_booking.py`

- [ ] **Step 1: Añadir pruebas de autenticación, límites y respuesta vacía**

Añadir pruebas a `backend/tests/test_booking.py` usando el `client` y la fixture `fresh_db` ya existentes:

```python
def test_admin_forecast_requires_valid_token():
    assert client.get("/api/admin/forecast").status_code == 422
    assert client.get(
        "/api/admin/forecast", headers={"X-Admin-Token": "malo"}
    ).status_code == 401


def test_admin_forecast_validates_history_weeks():
    headers = {"X-Admin-Token": "test-token"}
    assert client.get("/api/admin/forecast?history_weeks=0", headers=headers).status_code == 422
    assert client.get("/api/admin/forecast?history_weeks=53", headers=headers).status_code == 422


def test_admin_forecast_returns_empty_state_without_history():
    response = client.get(
        "/api/admin/forecast", headers={"X-Admin-Token": "test-token"}
    )

    assert response.status_code == 200
    assert response.json()["has_history"] is False
    assert response.json()["history_weeks"] == 8
    assert response.json()["estimates"] == []
    assert response.json()["message"]
```

- [ ] **Step 2: Ejecutar las nuevas pruebas HTTP y verificar que fallan por ruta ausente**

Run desde `backend/`: `python -m pytest tests/test_booking.py -k admin_forecast -q`

Expected: FAIL porque `/api/admin/forecast` todavía no está registrada.

- [ ] **Step 3: Añadir endpoint con período acotado al router admin existente**

En `admin.py`, importar `datetime`, `time`, `timedelta`, `Query`, `Appointment`, `build_demand_forecast` y `local_now`; añadir:

```python
@router.get("/forecast", summary="Previsión de demanda")
def demand_forecast(
    history_weeks: int = Query(8, ge=1, le=52),
    db: Session = Depends(get_db),
):
    today = local_now().date()
    window_start = today - timedelta(days=history_weeks * 7)
    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.start_at >= datetime.combine(window_start, time.min),
            Appointment.start_at < datetime.combine(today, time.min),
        )
        .all()
    )
    return build_demand_forecast(appointments, today, history_weeks)
```

- [ ] **Step 4: Ejecutar de nuevo las pruebas HTTP**

Run desde `backend/`: `python -m pytest tests/test_booking.py -k admin_forecast -q`

Expected: PASS; authentication is inherited from the existing admin router, invalid windows return 422, and an empty database returns an explicit empty state.

## Task 4: Añadir previsión visual responsiva al panel

**Files:**
- Modify: `frontend/admin.html`

- [ ] **Step 1: Añadir estilos y tarjeta de previsión**

Después de los estilos existentes añadir:

```css
.forecast-chart{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:10px;align-items:end}
.forecast-day{min-width:0;text-align:center;color:var(--muted);font-size:.78rem}
.forecast-day .value{display:block;color:var(--text);font-weight:700;margin-bottom:7px}
.forecast-track{height:130px;display:flex;align-items:end;background:var(--bg);border-radius:9px;margin-bottom:7px;overflow:hidden}
.forecast-bar{width:100%;height:var(--bar-height);background:var(--grad);border-radius:8px 8px 0 0}
@media(max-width:680px){.forecast-chart{gap:4px}.forecast-day{font-size:.66rem}.forecast-track{height:100px}}
```

Después de `<div class="stats" id="stats"></div>` añadir la tarjeta:

```html
<div class="card" id="forecastCard">
  <h2><i class="fa-solid fa-chart-column"></i> Previsión de demanda</h2>
  <p id="forecastStatus" class="empty" aria-live="polite">Cargando previsión…</p>
  <div id="forecastChart"></div>
</div>
```

- [ ] **Step 2: Añadir carga y estados del gráfico con la API existente**

Añadir `loadForecast()` a la sección DATA y sumarla al `Promise.all` de `refreshAll()`. La función debe llamar `api("/api/admin/forecast")`, mostrar estado de carga antes de `await`, y después:

```javascript
async function loadForecast(){
  const status = $("forecastStatus"), chart = $("forecastChart");
  status.textContent = "Cargando previsión…";
  chart.innerHTML = "";
  try{
    const data = await api("/api/admin/forecast");
    if(!data.has_history){ status.textContent = data.message; return; }
    status.textContent = `Estimación por día de la semana para los próximos 7 días; promedio del mismo día en las últimas ${data.history_weeks} semanas. Cancelaciones excluidas.`;
    const max = Math.max(...data.estimates.map(item => item.average_appointments), 1);
    chart.innerHTML = `<div class="forecast-chart">${data.estimates.map(item => {
      const height = item.average_appointments ? (item.average_appointments / max * 100) : 0;
      const day = new Date(item.date + "T12:00:00").toLocaleDateString("es-CL", {day:"2-digit", month:"2-digit"});
      return `<div class="forecast-day"><span class="value">${item.average_appointments.toFixed(1)}</span>
        <div class="forecast-track" aria-hidden="true"><div class="forecast-bar" style="--bar-height:${height}%"></div></div>
        <span>${item.weekday.slice(0,3)} ${day}</span></div>`;
    }).join("")}</div>`;
  }catch(e){
    if(e.status === 401){ logout(); return; }
    status.textContent = "No se pudo cargar la previsión: " + e.message;
    chart.innerHTML = "";
  }
}
```

Actualizar `refreshAll()` para cargar `loadForecast()` junto con los otros datos:

```javascript
async function refreshAll(){ await Promise.all([loadStats(), loadAppointments(), loadServices(), loadForecast()]); }
```

Los valores cero se muestran en texto como `0.0`; las barras con altura cero dejan visible la línea de base del track. Las etiquetas contienen el día de semana y la fecha, así como el promedio numérico, no solo un atributo `title`.

- [ ] **Step 3: Revisar manualmente los estados del frontend**

Con el backend y token activos, verificar el gráfico con historial, el mensaje sin historial, error de red y el cambio de anchura móvil/escritorio. Confirmar que no se necesitan dependencias JavaScript adicionales. Usar PowerShell `System.Drawing.Graphics.CopyFromScreen` para capturar únicamente la ventana de la app demo y guardar evidencia en `docs/demand-forecast-desktop.png` y `docs/demand-forecast-mobile.png`; no capturar otras ventanas del escritorio.

## Task 5: Ejecutar suite completa y revisar el cambio

**Files:**
- Verify: `backend/app/forecast.py`
- Verify: `backend/app/routers/admin.py`
- Verify: `backend/tests/test_booking.py`
- Verify: `frontend/admin.html`
- Verify: `AI_DEVELOPMENT_LOG.md`
- Verify: `docs/demand-forecast-desktop.png`, `docs/demand-forecast-mobile.png`

- [ ] **Step 1: Ejecutar toda la suite backend**

Run desde `backend/`: `python -m pytest`

Expected: PASS sin regresiones en reservas, disponibilidad ni autenticación.

- [ ] **Step 2: Revisar diff y estado antes de stage**

Run desde la raíz: `git status --short` y `git diff --check` y `git diff`.

Expected: solo cambios de especificación/plan y los archivos de la previsión; los dos PDF no se agregan al stage.

## Task 6: Crear el commit solicitado

**Files:** solo archivos del diseño, plan, registro IA, capturas de evidencia, endpoint, cálculo, pruebas y panel.

- [ ] **Step 1: Stage explícitamente los archivos de esta historia**

```powershell
git add docs/superpowers/specs/2026-10-25-demand-forecast-design.md docs/superpowers/plans/2026-10-25-demand-forecast.md AI_DEVELOPMENT_LOG.md docs/demand-forecast-desktop.png docs/demand-forecast-mobile.png backend/app/forecast.py backend/app/routers/admin.py backend/tests/test_booking.py frontend/admin.html
```

- [ ] **Step 2: Verificar el stage y crear el commit**

Run: `git status --short` y `git diff --cached --check`; confirmar que no estén staged los PDF. Después ejecutar:

```powershell
git commit -m "feat: agregar previsión de demanda"
```

- [ ] **Step 3: Verificar el commit creado**

Run: `git status --short` y `git log -1 --oneline`.

Expected: el commit contiene solo la primera implementación de previsión y sus documentos; los PDF permanecen fuera del commit.
