from datetime import date, timedelta

from instance import mcp
from config import HORARIO, SERVICIOS, TIMEZONE

_DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Map from HORARIO key (no accent) to display name (with accent)
_DIAS_DISPLAY = {
    "lunes": "lunes", "martes": "martes", "miercoles": "miércoles",
    "jueves": "jueves", "viernes": "viernes", "sabado": "sábado", "domingo": "domingo",
}


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
async def obtener_horario_clinica() -> str:
    """Devuelve el horario de apertura de la clínica y los servicios disponibles con sus duraciones."""
    lineas = ["Horario de la clínica:"]
    for dia_key, tramos in HORARIO.items():
        dia_display = _DIAS_DISPLAY[dia_key].capitalize()
        if tramos:
            tramos_str = " y ".join(f"{a} a {b}" for a, b in tramos)
            lineas.append(f"  {dia_display}: {tramos_str}")
        else:
            lineas.append(f"  {dia_display}: cerrado")

    lineas.append("")
    lineas.append("Servicios disponibles:")
    for svc in SERVICIOS.values():
        lineas.append(
            f"  {svc['nombre']}: sesiones de {svc['duracion_min']} minutos "
            f"({svc['max_paralelo']} plaza{'s' if svc['max_paralelo'] > 1 else ''} simultánea{'s' if svc['max_paralelo'] > 1 else ''})"
        )

    lineas.append(f"\nZona horaria: {TIMEZONE}.")
    return "\n".join(lineas)
