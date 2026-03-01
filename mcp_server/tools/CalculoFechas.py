from datetime import date, timedelta,time,datetime
import json
import calendario
import config

from instance import mcp
from validators import validar_fechas, calcular_noches, formatear_precio


_DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


@mcp.tool()
async def obtener_fecha_actual() -> str:
    """Devuelve la fecha actual con el día de la semana en español, para calcular fechas relativas."""
    hoy = date.today()
    dia_semana = _DIAS_ES[hoy.weekday()]
    mes = _MESES_ES[hoy.month - 1]
    return (
        f"Hoy es {dia_semana}, {hoy.day} de {mes} de {hoy.year}. "
        f"Fecha ISO: {hoy.isoformat()}."
    )


@mcp.tool()
async def calcular_fecha(dias_desde_hoy: int) -> str:
    """Devuelve la fecha ISO y el día de la semana correspondiente a N días desde hoy.
    Úsalo para verificar cualquier fecha relativa: mañana=1, pasado mañana=2, 1 semana=7, etc."""
    d = date.today() + timedelta(days=dias_desde_hoy)
    dia = _DIAS_ES[d.weekday()]
    mes = _MESES_ES[d.month - 1]
    return f"{dia} {d.day} de {mes} de {d.year} → {d.isoformat()}"




@mcp.tool()
async def consultar_disponibilidad(start_date:int,end_date:int) -> list:
    service = calendario.getCalendarInstance()
    open_time = time(hour=9)
    closing_time = time(hour=22)
    start= date.today() + timedelta(days=start_date)
    end= date.today() + timedelta(days=end_date)

    events_result = (
        service.events()
        .list(
            calendarId = config.CALENDAR_ID,
            timeMin = datetime.combine(start,open_time).isoformat(),
            timeMax = datetime.combine(end,closing_time).isoformat(),
            maxResults = 10,
            singleEvents=True,
            orderBy = "startTime",
        ).execute()
    )
    events = events_result().get("items",[])

    return events