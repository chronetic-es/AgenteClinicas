from datetime import date

from instance import mcp
from db import obtener_conexion_db
from validators import validar_fechas, validar_telefono, formatear_precio
from config import PRECIO_DESAYUNO_POR_NOCHE, PRECIO_TRANSPORTE_AEROPUERTO


@mcp.tool()
async def crear_reserva(
    nombre_completo: str,
    telefono: str,
    fecha_entrada: str,
    fecha_salida: str,
    tipo_habitacion: str,
    desayuno: bool = False,
    transporte: bool = False,
) -> str:
    """Crea la reserva y asigna una habitación física. Acepta opciones de desayuno incluido y transporte desde el aeropuerto."""
    error_fecha = validar_fechas(fecha_entrada, fecha_salida)
    if error_fecha:
        return error_fecha

    error_tel = validar_telefono(telefono)
    if error_tel:
        return error_tel

    if not nombre_completo.strip():
        return "El nombre completo es obligatorio."

    conn = await obtener_conexion_db()
    try:
        d_entrada = date.fromisoformat(fecha_entrada)
        d_salida = date.fromisoformat(fecha_salida)

        async with conn.transaction():
            tipo = await conn.fetchrow(
                "SELECT id, name, base_price FROM RoomTypes WHERE name ILIKE $1",
                f"%{tipo_habitacion}%",
            )
            if not tipo:
                return "No encontré ese tipo de habitación. Puede consultar las opciones disponibles."

            habitacion_id = await conn.fetchval(
                """
                SELECT id FROM Rooms WHERE room_type_id = $1 AND id NOT IN (
                    SELECT ra.room_id FROM RoomAssignments ra JOIN Bookings b ON ra.booking_id = b.id
                    WHERE (b.check_in_date, b.check_out_date) OVERLAPS ($2, $3)
                    AND b.status != 'Cancelled'
                ) LIMIT 1
                """,
                tipo["id"],
                d_entrada,
                d_salida,
            )

            if not habitacion_id:
                return "Lo siento, no quedan habitaciones disponibles de ese tipo para las fechas indicadas."

            noches = (d_salida - d_entrada).days
            base_price = float(tipo["base_price"])
            extra = (noches * PRECIO_DESAYUNO_POR_NOCHE if desayuno else 0) + (PRECIO_TRANSPORTE_AEROPUERTO if transporte else 0)
            total = noches * base_price + extra

            u_id = await conn.fetchval(
                """
                INSERT INTO Users (full_name, phone) VALUES ($1, $2)
                ON CONFLICT (phone) DO UPDATE SET full_name = $1 RETURNING id
                """,
                nombre_completo.strip(),
                telefono,
            )

            b_id = await conn.fetchval(
                """
                INSERT INTO Bookings (user_id, check_in_date, check_out_date, total_amount, status, desayuno_incluido, transporte_aeropuerto)
                VALUES ($1, $2, $3, $4, 'Confirmed', $5, $6) RETURNING id
                """,
                u_id,
                d_entrada,
                d_salida,
                total,
                desayuno,
                transporte,
            )

            await conn.execute(
                "INSERT INTO RoomAssignments (booking_id, room_id) VALUES ($1, $2)",
                b_id,
                habitacion_id,
            )

            extras_desc = []
            if desayuno:
                extras_desc.append("desayuno incluido")
            if transporte:
                extras_desc.append("transporte desde el aeropuerto")
            extras_str = ", con " + " y ".join(extras_desc) if extras_desc else ""

            return (
                f"Reserva confirmada. Número de reserva: {b_id}. "
                f"Nombre: {nombre_completo.strip()}. "
                f"Habitación: {tipo['name']}{extras_str}. "
                f"Entrada el {fecha_entrada}, salida el {fecha_salida}. "
                f"Total: {formatear_precio(total)}."
            )
    except Exception:
        return "No se pudo completar la reserva. Por favor, inténtelo de nuevo."
    finally:
        await conn.close()


@mcp.tool()
async def obtener_reservas_cliente(telefono: str) -> str:
    """Devuelve todas las reservas activas de un cliente dado su número de teléfono."""
    error_tel = validar_telefono(telefono)
    if error_tel:
        return error_tel

    conn = await obtener_conexion_db()
    try:
        filas = await conn.fetch(
            """
            SELECT b.id, b.check_in_date, b.check_out_date, b.total_amount, b.status,
                   b.desayuno_incluido, b.transporte_aeropuerto,
                   rt.name AS tipo_habitacion
            FROM Bookings b
            JOIN Users u ON b.user_id = u.id
            JOIN RoomAssignments ra ON ra.booking_id = b.id
            JOIN Rooms r ON ra.room_id = r.id
            JOIN RoomTypes rt ON r.room_type_id = rt.id
            WHERE u.phone = $1 AND b.status NOT IN ('Cancelled', 'Completed')
            ORDER BY b.check_in_date
            """,
            telefono,
        )

        if not filas:
            return "No encontré reservas activas para ese número de teléfono."

        partes = []
        for f in filas:
            extras = []
            if f["desayuno_incluido"]:
                extras.append("desayuno incluido")
            if f["transporte_aeropuerto"]:
                extras.append("transporte aeropuerto")
            extras_str = ", " + " y ".join(extras) if extras else ""
            partes.append(
                f"Reserva número {f['id']}: {f['tipo_habitacion']}{extras_str}, "
                f"entrada el {f['check_in_date']}, salida el {f['check_out_date']}, "
                f"total {formatear_precio(float(f['total_amount']))}."
            )
        plural = len(filas) != 1
        return (
            f"Tiene {len(filas)} reserva{'s' if plural else ''} activa{'s' if plural else ''}. "
            + " ".join(partes)
        )
    finally:
        await conn.close()


@mcp.tool()
async def modificar_reserva(
    reserva_id: int,
    nueva_fecha_entrada: str = "",
    nueva_fecha_salida: str = "",
    nuevo_tipo_habitacion: str = "",
    nuevo_desayuno: bool | None = None,
    nuevo_transporte: bool | None = None,
) -> str:
    """Modifica las fechas, el tipo de habitación o los servicios adicionales de una reserva existente."""
    if not nueva_fecha_entrada and not nueva_fecha_salida and not nuevo_tipo_habitacion \
            and nuevo_desayuno is None and nuevo_transporte is None:
        return "Debe indicar al menos un cambio."

    conn = await obtener_conexion_db()
    try:
        reserva = await conn.fetchrow(
            """
            SELECT b.id, b.check_in_date, b.check_out_date, b.status,
                   b.desayuno_incluido, b.transporte_aeropuerto,
                   rt.id AS tipo_id, rt.name AS tipo_nombre, rt.base_price
            FROM Bookings b
            JOIN RoomAssignments ra ON ra.booking_id = b.id
            JOIN Rooms r ON ra.room_id = r.id
            JOIN RoomTypes rt ON r.room_type_id = rt.id
            WHERE b.id = $1
            """,
            reserva_id,
        )

        if not reserva:
            return f"No encontré ninguna reserva con el número {reserva_id}."

        if reserva["status"] in ("Cancelled", "Completed"):
            return f"La reserva número {reserva_id} está {reserva['status'].lower()} y no puede modificarse."

        f_entrada = nueva_fecha_entrada if nueva_fecha_entrada else str(reserva["check_in_date"])
        f_salida = nueva_fecha_salida if nueva_fecha_salida else str(reserva["check_out_date"])

        error_fecha = validar_fechas(f_entrada, f_salida)
        if error_fecha:
            return error_fecha

        d_entrada = date.fromisoformat(f_entrada)
        d_salida = date.fromisoformat(f_salida)

        if nuevo_tipo_habitacion:
            tipo = await conn.fetchrow(
                "SELECT id, name, base_price FROM RoomTypes WHERE name ILIKE $1",
                f"%{nuevo_tipo_habitacion}%",
            )
            if not tipo:
                return f"No encontré el tipo de habitación {nuevo_tipo_habitacion}. Puede consultar las opciones disponibles."
        else:
            tipo = {
                "id": reserva["tipo_id"],
                "name": reserva["tipo_nombre"],
                "base_price": reserva["base_price"],
            }

        desayuno = nuevo_desayuno if nuevo_desayuno is not None else reserva["desayuno_incluido"]
        transporte = nuevo_transporte if nuevo_transporte is not None else reserva["transporte_aeropuerto"]

        async with conn.transaction():
            habitacion_id = await conn.fetchval(
                """
                SELECT id FROM Rooms WHERE room_type_id = $1 AND id NOT IN (
                    SELECT ra.room_id FROM RoomAssignments ra JOIN Bookings b ON ra.booking_id = b.id
                    WHERE b.id != $4
                    AND (b.check_in_date, b.check_out_date) OVERLAPS ($2, $3)
                    AND b.status != 'Cancelled'
                ) LIMIT 1
                """,
                tipo["id"],
                d_entrada,
                d_salida,
                reserva_id,
            )

            if not habitacion_id:
                return "No hay habitaciones disponibles de ese tipo para las nuevas fechas."

            noches = (d_salida - d_entrada).days
            base_price = float(tipo["base_price"])
            extra = (noches * PRECIO_DESAYUNO_POR_NOCHE if desayuno else 0) + (PRECIO_TRANSPORTE_AEROPUERTO if transporte else 0)
            total = noches * base_price + extra

            await conn.execute(
                """
                UPDATE Bookings
                SET check_in_date = $1, check_out_date = $2, total_amount = $3,
                    desayuno_incluido = $4, transporte_aeropuerto = $5
                WHERE id = $6
                """,
                d_entrada,
                d_salida,
                total,
                desayuno,
                transporte,
                reserva_id,
            )

            await conn.execute("DELETE FROM RoomAssignments WHERE booking_id = $1", reserva_id)
            await conn.execute(
                "INSERT INTO RoomAssignments (booking_id, room_id) VALUES ($1, $2)",
                reserva_id,
                habitacion_id,
            )

        extras = []
        if desayuno:
            extras.append("desayuno incluido")
        if transporte:
            extras.append("transporte aeropuerto")
        extras_str = ", con " + " y ".join(extras) if extras else ""

        return (
            f"La reserva número {reserva_id} ha sido actualizada. "
            f"Habitación: {tipo['name']}{extras_str}. "
            f"Nueva entrada el {f_entrada}, salida el {f_salida}. "
            f"Nuevo total: {formatear_precio(total)}."
        )
    except Exception:
        return "No se pudo modificar la reserva. Por favor, inténtelo de nuevo."
    finally:
        await conn.close()


@mcp.tool()
async def cancelar_reserva(reserva_id: int) -> str:
    """Cancela una reserva dado su identificador."""
    conn = await obtener_conexion_db()
    try:
        estado = await conn.fetchval(
            "SELECT status FROM Bookings WHERE id = $1", reserva_id
        )

        if estado is None:
            return f"No encontré ninguna reserva con el número {reserva_id}."
        if estado == "Cancelled":
            return f"La reserva número {reserva_id} ya estaba cancelada."
        if estado == "Completed":
            return f"La reserva número {reserva_id} ya está completada y no puede cancelarse."

        await conn.execute("UPDATE Bookings SET status = 'Cancelled' WHERE id = $1", reserva_id)
        return f"La reserva número {reserva_id} ha sido cancelada correctamente."
    finally:
        await conn.close()
