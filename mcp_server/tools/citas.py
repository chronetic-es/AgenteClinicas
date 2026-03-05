from datetime import date, datetime, timedelta, time as time_type
import zoneinfo

from instance import mcp
from gcal import obtener_cliente_gcal, CALENDAR_ID
from config import SERVICIOS, HORARIO, TIMEZONE
from validators import (
    validar_telefono,
    validar_servicio,
    validar_fecha,
    validar_hora,
    dentro_de_horario,
    _normalizar_servicio,
)

_DIAS_ES_KEY = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
_DIAS_DISPLAY = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_HORAS_PALABRAS = ["doce", "una", "dos", "tres", "cuatro", "cinco",
                   "seis", "siete", "ocho", "nueve", "diez", "once"]


def _tz() -> zoneinfo.ZoneInfo:
    return zoneinfo.ZoneInfo(TIMEZONE)


def _dt(fecha: str, hora: str) -> datetime:
    return datetime.fromisoformat(f"{fecha}T{hora}:00").replace(tzinfo=_tz())


def _hora_en_palabras(h: int, m: int) -> str:
    h12 = h % 12
    art = "la" if h12 == 1 else "las"
    base = f"{art} {_HORAS_PALABRAS[h12]}"
    if m == 0:
        return f"{base} en punto"
    return f"{base} y {m} minutos"


def _format_dt(dt: datetime) -> str:
    dia = _DIAS_DISPLAY[dt.weekday()]
    mes = _MESES_ES[dt.month - 1]
    hora_num = dt.strftime('%H:%M')
    hora_palabras = _hora_en_palabras(dt.hour, dt.minute)
    return f"{dia} {dt.day} de {mes} de {dt.year} a las {hora_num} ({hora_palabras})"


def _overlaps_event(event: dict, slot_ini: datetime, slot_fin: datetime) -> bool:
    """Returns True if a calendar event overlaps with the half-open interval [slot_ini, slot_fin)."""
    try:
        e_start = datetime.fromisoformat(event["start"]["dateTime"])
        e_end = datetime.fromisoformat(event["end"]["dateTime"])
        return e_start < slot_fin and e_end > slot_ini
    except (KeyError, ValueError):
        return False


def _fetch_events_for_service(service, svc_key: str, dt_from: datetime, dt_to: datetime) -> list:
    result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=dt_from.isoformat(),
        timeMax=dt_to.isoformat(),
        singleEvents=True,
        privateExtendedProperty=f"servicio={svc_key}",
        maxResults=250,
    ).execute()
    return result.get("items", [])


@mcp.tool()
async def verificar_disponibilidad_cita(servicio: str, fecha: str, hora_inicio: str) -> str:
    """Comprueba si hay plaza disponible para un servicio en una fecha y hora concretas.
    servicio: nombre o clave del servicio (ej: 'depilacion', 'Fisioterapia').
    fecha: AAAA-MM-DD. hora_inicio: HH:MM."""
    svc_key = _normalizar_servicio(servicio)
    if svc_key is None:
        return validar_servicio(servicio)

    for err in [validar_fecha(fecha), validar_hora(hora_inicio)]:
        if err:
            return err

    svc = SERVICIOS[svc_key]
    duracion = svc["duracion_min"]

    if not dentro_de_horario(fecha, hora_inicio, duracion):
        return (
            f"El horario solicitado está fuera del horario de la clínica o la sesión "
            f"de {duracion} minutos no cabe completa en ese tramo. "
            f"Llame a obtener_horario_clinica para consultar el horario."
        )

    dt_inicio = _dt(fecha, hora_inicio)
    dt_fin = dt_inicio + timedelta(minutes=duracion)

    gcal = obtener_cliente_gcal()
    eventos = _fetch_events_for_service(gcal, svc_key, dt_inicio, dt_fin)
    count = len(eventos)
    max_p = svc["max_paralelo"]

    if count < max_p:
        libres = max_p - count
        return (
            f"Hay disponibilidad para {svc['nombre']} el {_format_dt(dt_inicio)}. "
            f"Plaza{'s' if libres > 1 else ''} libre{'s' if libres > 1 else ''}: {libres} de {max_p}."
        )
    return (
        f"No hay plaza disponible para {svc['nombre']} el {_format_dt(dt_inicio)}. "
        f"Puede consultar huecos alternativos con obtener_slots_disponibles."
    )


@mcp.tool()
async def crear_cita(
    servicio: str,
    fecha: str,
    hora_inicio: str,
    nombre_cliente: str,
    telefono: str,
) -> str:
    """Crea una nueva cita en el calendario de la clínica.
    servicio: nombre o clave del servicio. fecha: AAAA-MM-DD. hora_inicio: HH:MM.
    nombre_cliente: nombre completo. telefono: número de teléfono del cliente."""
    svc_key = _normalizar_servicio(servicio)
    if svc_key is None:
        return validar_servicio(servicio)

    for err in [validar_fecha(fecha), validar_hora(hora_inicio), validar_telefono(telefono)]:
        if err:
            return err

    if not nombre_cliente.strip():
        return "El nombre del cliente no puede estar vacío."

    svc = SERVICIOS[svc_key]
    duracion = svc["duracion_min"]

    if not dentro_de_horario(fecha, hora_inicio, duracion):
        return (
            f"El horario solicitado está fuera del horario de la clínica o la sesión "
            f"de {duracion} minutos no cabe completa en ese tramo."
        )

    dt_inicio = _dt(fecha, hora_inicio)
    dt_fin = dt_inicio + timedelta(minutes=duracion)

    gcal = obtener_cliente_gcal()
    eventos = _fetch_events_for_service(gcal, svc_key, dt_inicio, dt_fin)
    if len(eventos) >= svc["max_paralelo"]:
        return (
            f"No hay plaza disponible para {svc['nombre']} el {_format_dt(dt_inicio)}. "
            f"Elija otra fecha u hora."
        )

    event_body = {
        "summary": f"[{svc['nombre']}] {nombre_cliente.strip()}",
        "description": f"telefono: {telefono}\nservicio: {svc_key}",
        "start": {"dateTime": dt_inicio.isoformat(), "timeZone": TIMEZONE},
        "end":   {"dateTime": dt_fin.isoformat(),   "timeZone": TIMEZONE},
        "extendedProperties": {
            "private": {
                "telefono": telefono,
                "servicio": svc_key,
            }
        },
    }

    gcal.events().insert(calendarId=CALENDAR_ID, body=event_body).execute()
    return (
        f"Cita confirmada. {svc['nombre']} para {nombre_cliente.strip()} "
        f"el {_format_dt(dt_inicio)} (duración: {duracion} minutos). "
        f"Puede gestionar su cita llamando con el teléfono {telefono}."
    )


@mcp.tool()
async def obtener_citas_cliente(telefono: str) -> str:
    """Devuelve las próximas citas de un cliente buscando por su número de teléfono."""
    err = validar_telefono(telefono)
    if err:
        return err

    now = datetime.now(_tz()).isoformat()
    gcal = obtener_cliente_gcal()
    result = gcal.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        singleEvents=True,
        orderBy="startTime",
        privateExtendedProperty=f"telefono={telefono}",
        maxResults=50,
    ).execute()

    eventos = result.get("items", [])
    if not eventos:
        return f"No se encontraron citas próximas para el teléfono {telefono}."

    lineas = [f"Citas próximas para {telefono}:"]
    for e in eventos:
        dt_start = datetime.fromisoformat(e["start"]["dateTime"])
        svc_key = e.get("extendedProperties", {}).get("private", {}).get("servicio", "")
        svc = SERVICIOS.get(svc_key, {})
        nombre_svc = svc.get("nombre", svc_key)
        duracion = svc.get("duracion_min", 0)
        dt_end = dt_start + timedelta(minutes=duracion)
        lineas.append(
            f"- {nombre_svc} | {_format_dt(dt_start)} "
            f"hasta las {dt_end.strftime('%H:%M')} ({_hora_en_palabras(dt_end.hour, dt_end.minute)})"
        )

    return "\n".join(lineas)


@mcp.tool()
async def modificar_cita(
    telefono: str,
    fecha_actual: str,
    hora_actual: str,
    nuevo_servicio: str = "",
    nueva_fecha: str = "",
    nueva_hora: str = "",
) -> str:
    """Modifica una cita existente identificada por teléfono, fecha y hora actuales.
    Solo se actualizan los campos proporcionados (nuevo_servicio, nueva_fecha, nueva_hora).
    telefono: debe coincidir con el de la cita. fecha_actual/hora_actual: identifican la cita."""
    err = validar_telefono(telefono)
    if err:
        return err

    for err in [validar_fecha(fecha_actual), validar_hora(hora_actual)]:
        if err:
            return err

    dt_cita = _dt(fecha_actual, hora_actual)
    gcal = obtener_cliente_gcal()
    result = gcal.events().list(
        calendarId=CALENDAR_ID,
        timeMin=dt_cita.isoformat(),
        timeMax=(dt_cita + timedelta(minutes=1)).isoformat(),
        singleEvents=True,
        privateExtendedProperty=f"telefono={telefono}",
        maxResults=5,
    ).execute()
    eventos = [
        e for e in result.get("items", [])
        if datetime.fromisoformat(e["start"]["dateTime"]).replace(tzinfo=_tz()) == dt_cita
    ]
    if not eventos:
        return "No se encontró ninguna cita con esa fecha y hora para este teléfono."

    evento = eventos[0]
    evento_id = evento["id"]

    # Resolve current values
    svc_actual = evento.get("extendedProperties", {}).get("private", {}).get("servicio", "")

    # Resolve new values
    svc_key = _normalizar_servicio(nuevo_servicio) if nuevo_servicio.strip() else svc_actual
    if nuevo_servicio.strip() and svc_key is None:
        return validar_servicio(nuevo_servicio)

    fecha = nueva_fecha.strip() if nueva_fecha.strip() else fecha_actual
    hora = nueva_hora.strip() if nueva_hora.strip() else hora_actual

    if nueva_fecha.strip():
        err = validar_fecha(nueva_fecha)
        if err:
            return err
    if nueva_hora.strip():
        err = validar_hora(nueva_hora)
        if err:
            return err

    cambia_slot = bool(nuevo_servicio.strip() or nueva_fecha.strip() or nueva_hora.strip())
    if not cambia_slot:
        return "No se indicó ningún cambio. La cita permanece sin modificar."

    svc = SERVICIOS[svc_key]
    duracion = svc["duracion_min"]

    if not dentro_de_horario(fecha, hora, duracion):
        return (
            f"El nuevo horario está fuera del horario de la clínica o la sesión "
            f"de {duracion} minutos no cabe completa en ese tramo."
        )

    dt_nuevo_inicio = _dt(fecha, hora)
    dt_nuevo_fin = dt_nuevo_inicio + timedelta(minutes=duracion)

    # Check availability, excluding the current event
    eventos_conflicto = _fetch_events_for_service(gcal, svc_key, dt_nuevo_inicio, dt_nuevo_fin)
    conflictos = [e for e in eventos_conflicto if e["id"] != evento_id]
    if len(conflictos) >= svc["max_paralelo"]:
        return (
            f"No hay plaza disponible para {svc['nombre']} el {_format_dt(dt_nuevo_inicio)}. "
            f"Elija otra fecha u hora."
        )

    # Preserve client name from the existing summary
    nombre_cliente = evento.get("summary", "").split("] ", 1)[-1] if "] " in evento.get("summary", "") else evento.get("summary", "")

    patch = {
        "summary": f"[{svc['nombre']}] {nombre_cliente}",
        "description": f"telefono: {telefono}\nservicio: {svc_key}",
        "start": {"dateTime": dt_nuevo_inicio.isoformat(), "timeZone": TIMEZONE},
        "end":   {"dateTime": dt_nuevo_fin.isoformat(),   "timeZone": TIMEZONE},
        "extendedProperties": {
            "private": {
                "telefono": telefono,
                "servicio": svc_key,
            }
        },
    }
    gcal.events().patch(calendarId=CALENDAR_ID, eventId=evento_id, body=patch).execute()

    return (
        f"Cita modificada. {svc['nombre']} el {_format_dt(dt_nuevo_inicio)} "
        f"(duración: {duracion} minutos)."
    )


@mcp.tool()
async def cancelar_cita(telefono: str, fecha: str, hora: str) -> str:
    """Cancela una cita existente identificada por teléfono, fecha y hora de inicio.
    telefono: debe coincidir con el de la cita. fecha: AAAA-MM-DD. hora: HH:MM."""
    err = validar_telefono(telefono)
    if err:
        return err

    for err in [validar_fecha(fecha), validar_hora(hora)]:
        if err:
            return err

    dt_cita = _dt(fecha, hora)
    gcal = obtener_cliente_gcal()
    result = gcal.events().list(
        calendarId=CALENDAR_ID,
        timeMin=dt_cita.isoformat(),
        timeMax=(dt_cita + timedelta(minutes=1)).isoformat(),
        singleEvents=True,
        privateExtendedProperty=f"telefono={telefono}",
        maxResults=5,
    ).execute()
    eventos = [
        e for e in result.get("items", [])
        if datetime.fromisoformat(e["start"]["dateTime"]).replace(tzinfo=_tz()) == dt_cita
    ]
    if not eventos:
        return "No se encontró ninguna cita con esa fecha y hora para este teléfono."

    evento = eventos[0]
    dt_start = datetime.fromisoformat(evento["start"]["dateTime"])
    svc_key = evento.get("extendedProperties", {}).get("private", {}).get("servicio", "")
    nombre_svc = SERVICIOS.get(svc_key, {}).get("nombre", svc_key)

    gcal.events().delete(calendarId=CALENDAR_ID, eventId=evento["id"]).execute()

    return f"Cita de {nombre_svc} del {_format_dt(dt_start)} cancelada correctamente."


@mcp.tool()
async def obtener_slots_disponibles(
    servicio: str,
    fecha_inicio: str,
    fecha_fin: str = "",
) -> str:
    """Devuelve los huecos libres para un servicio en un día o rango de fechas.
    Si fecha_fin se omite, devuelve los huecos del día fecha_inicio.
    Útil cuando el cliente pregunta qué hay disponible para una fecha o semana concreta.
    servicio: nombre o clave del servicio. fecha_inicio/fin: AAAA-MM-DD."""
    svc_key = _normalizar_servicio(servicio)
    if svc_key is None:
        return validar_servicio(servicio)

    err = validar_fecha(fecha_inicio)
    if err:
        return err

    fecha_fin_efectiva = fecha_fin.strip() if fecha_fin.strip() else fecha_inicio
    if fecha_fin.strip():
        err = validar_fecha(fecha_fin_efectiva)
        if err:
            return err

    d_inicio = date.fromisoformat(fecha_inicio)
    d_fin = date.fromisoformat(fecha_fin_efectiva)

    if d_fin < d_inicio:
        return "La fecha de fin debe ser igual o posterior a la fecha de inicio."

    svc = SERVICIOS[svc_key]
    duracion = svc["duracion_min"]
    tz = _tz()

    # One API call for the entire range
    dt_rango_ini = datetime.combine(d_inicio, time_type(0, 0), tzinfo=tz)
    dt_rango_fin = datetime.combine(d_fin, time_type(23, 59, 59), tzinfo=tz)
    gcal = obtener_cliente_gcal()
    eventos = _fetch_events_for_service(gcal, svc_key, dt_rango_ini, dt_rango_fin)

    bloques: list[str] = []
    current = d_inicio

    while current <= d_fin:
        dia_key = _DIAS_ES_KEY[current.weekday()]
        tramos = HORARIO.get(dia_key, [])
        slots_libres: list[str] = []

        for tramo_ini_str, tramo_fin_str in tramos:
            t_tramo_ini = time_type.fromisoformat(tramo_ini_str)
            t_tramo_fin = time_type.fromisoformat(tramo_fin_str)
            slot_dt = datetime.combine(current, t_tramo_ini, tzinfo=tz)
            tramo_fin_dt = datetime.combine(current, t_tramo_fin, tzinfo=tz)

            while slot_dt + timedelta(minutes=duracion) <= tramo_fin_dt:
                slot_fin_dt = slot_dt + timedelta(minutes=duracion)
                solapados = sum(1 for e in eventos if _overlaps_event(e, slot_dt, slot_fin_dt))
                if solapados < svc["max_paralelo"]:
                    hora_num = slot_dt.strftime("%H:%M")
                    slots_libres.append(f"{hora_num} ({_hora_en_palabras(slot_dt.hour, slot_dt.minute)})")
                slot_dt += timedelta(minutes=duracion)

        if slots_libres:
            dia_display = _DIAS_DISPLAY[current.weekday()]
            mes = _MESES_ES[current.month - 1]
            bloques.append(f"{dia_display} {current.day} de {mes}: {', '.join(slots_libres)}")

        current += timedelta(days=1)

    if not bloques:
        meses = _MESES_ES
        if d_inicio == d_fin:
            rango = f"el {d_inicio.day} de {meses[d_inicio.month - 1]}"
        else:
            rango = f"entre el {d_inicio.day} de {meses[d_inicio.month - 1]} y el {d_fin.day} de {meses[d_fin.month - 1]}"
        return (
            f"No hay huecos disponibles para {svc['nombre']} {rango}. "
            f"¿Desea consultar otras fechas?"
        )

    return f"Huecos disponibles para {svc['nombre']}:\n" + "\n".join(bloques)
