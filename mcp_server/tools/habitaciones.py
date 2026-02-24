from datetime import date, timedelta

from instance import mcp
from db import obtener_conexion_db
from validators import validar_fechas, calcular_noches, formatear_precio
from config import PRECIO_DESAYUNO_POR_NOCHE, PRECIO_TRANSPORTE_AEROPUERTO

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
async def obtener_opciones_habitacion() -> str:
    """Lista los tipos de habitaciones disponibles, sus precios y los servicios adicionales disponibles."""
    conn = await obtener_conexion_db()
    try:
        filas = await conn.fetch("SELECT id, name, base_price, description FROM RoomTypes")
        opciones = [
            f"{f['name']} (id:{f['id']}), {formatear_precio(float(f['base_price']))} por noche. {f['description']}"
            for f in filas
        ]
        addons = (
            f"También ofrecemos desayuno incluido por {formatear_precio(PRECIO_DESAYUNO_POR_NOCHE)} por noche, "
            f"y servicio de transporte desde el aeropuerto por {formatear_precio(PRECIO_TRANSPORTE_AEROPUERTO)}."
        )
        return "Tenemos " + str(len(opciones)) + " tipos de habitación. " + " ".join(opciones) + " " + addons
    finally:
        await conn.close()


@mcp.tool()
async def calcular_presupuesto(
    fecha_entrada: str,
    fecha_salida: str,
    tipo_habitacion_id: int,
    desayuno: bool = False,
    transporte: bool = False,
) -> str:
    """Calcula el costo total de una estancia sin realizar la reserva. Incluye opciones de desayuno y transporte."""
    error = validar_fechas(fecha_entrada, fecha_salida)
    if error:
        return error

    conn = await obtener_conexion_db()
    try:
        tipo = await conn.fetchrow(
            "SELECT name, base_price FROM RoomTypes WHERE id = $1",
            tipo_habitacion_id,
        )
        if not tipo:
            return "No encontré ese tipo de habitación. Puede consultar las opciones disponibles."

        noches = calcular_noches(fecha_entrada, fecha_salida)
        base_price = float(tipo["base_price"])
        extra = (noches * PRECIO_DESAYUNO_POR_NOCHE if desayuno else 0) + (PRECIO_TRANSPORTE_AEROPUERTO if transporte else 0)
        total = noches * base_price + extra

        desglose = []
        desglose.append(f"habitación {noches} noches a {formatear_precio(base_price)} por noche: {formatear_precio(noches * base_price)}")
        if desayuno:
            desglose.append(f"desayuno {noches} noches a {formatear_precio(PRECIO_DESAYUNO_POR_NOCHE)} por noche: {formatear_precio(noches * PRECIO_DESAYUNO_POR_NOCHE)}")
        if transporte:
            desglose.append(f"transporte aeropuerto: {formatear_precio(PRECIO_TRANSPORTE_AEROPUERTO)}")

        return (
            f"Presupuesto para {tipo['name']}, {noches} noches. "
            + ", ".join(desglose)
            + f". Total: {formatear_precio(total)}."
        )
    finally:
        await conn.close()


@mcp.tool()
async def verificar_disponibilidad(fecha_entrada: str, fecha_salida: str, tipo_habitacion_id: int) -> str:
    """Verifica si hay habitaciones libres de un tipo específico."""
    error = validar_fechas(fecha_entrada, fecha_salida)
    if error:
        return error

    conn = await obtener_conexion_db()
    try:
        tipo = await conn.fetchrow(
            "SELECT id, name FROM RoomTypes WHERE id = $1",
            tipo_habitacion_id,
        )
        if not tipo:
            return "No reconozco ese tipo de habitación. Puede consultar las opciones disponibles."

        d_entrada = date.fromisoformat(fecha_entrada)
        d_salida = date.fromisoformat(fecha_salida)

        query = """
            SELECT COUNT(*) FROM Rooms r
            WHERE r.room_type_id = $1
            AND r.id NOT IN (
                SELECT ra.room_id FROM RoomAssignments ra
                JOIN Bookings b ON ra.booking_id = b.id
                WHERE (b.check_in_date, b.check_out_date) OVERLAPS ($2, $3)
                AND b.status != 'Cancelled'
            )
        """
        cantidad = await conn.fetchval(query, tipo["id"], d_entrada, d_salida)
        if cantidad > 0:
            return f"Hay {cantidad} habitaciones de tipo {tipo['name']} disponibles para esas fechas."
        return f"Lo sentimos, no hay habitaciones de tipo {tipo['name']} disponibles para esas fechas."
    finally:
        await conn.close()
