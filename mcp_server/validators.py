from datetime import date, datetime, time, timedelta
from config import HORARIO, SERVICIOS

_DIAS_ES = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


def validar_telefono(telefono: str) -> str | None:
    """Valida que el teléfono tenga al menos 7 dígitos y no supere 25 caracteres."""
    digitos = "".join(c for c in telefono if c.isdigit())
    if len(digitos) < 7 or len(telefono) > 25:
        return "El número de teléfono no parece válido."
    return None


def validar_servicio(servicio: str) -> str | None:
    """Valida que el servicio existe. Devuelve mensaje de error o None."""
    if _normalizar_servicio(servicio) is None:
        nombres = ", ".join(v["nombre"] for v in SERVICIOS.values())
        return f"Servicio no reconocido. Los servicios disponibles son: {nombres}."
    return None


def validar_fecha(fecha: str) -> str | None:
    """Valida formato ISO y que la fecha no sea en el pasado."""
    try:
        d = date.fromisoformat(fecha)
    except ValueError:
        return "La fecha debe estar en formato AAAA-MM-DD."
    if d < date.today():
        return "La fecha no puede ser en el pasado."
    return None


def validar_hora(hora: str) -> str | None:
    """Valida que la hora esté en formato HH:MM."""
    try:
        time.fromisoformat(hora)
    except ValueError:
        return "La hora debe estar en formato HH:MM."
    return None


def dentro_de_horario(fecha: str, hora_inicio: str, duracion_min: int) -> bool:
    """Devuelve True si el slot [hora_inicio, hora_inicio+duracion_min) cabe
    completamente dentro de un tramo del horario de la clínica en ese día."""
    try:
        d = date.fromisoformat(fecha)
        t_ini = time.fromisoformat(hora_inicio)
    except ValueError:
        return False

    dia_key = _DIAS_ES[d.weekday()]
    tramos = HORARIO.get(dia_key, [])

    dt_base = datetime.combine(d, t_ini)
    t_fin = (dt_base + timedelta(minutes=duracion_min)).time()

    for tramo_ini_str, tramo_fin_str in tramos:
        t_a = time.fromisoformat(tramo_ini_str)
        t_b = time.fromisoformat(tramo_fin_str)
        if t_a <= t_ini and t_fin <= t_b:
            return True
    return False


def _normalizar_servicio(servicio: str) -> str | None:
    """Convierte un nombre o clave de servicio a la clave interna, o None si no existe."""
    s = servicio.lower().strip()
    if s in SERVICIOS:
        return s
    for key, val in SERVICIOS.items():
        if val["nombre"].lower() == s:
            return key
    return None
