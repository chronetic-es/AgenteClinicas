# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A hotel booking backend exposed as an **MCP (Model Context Protocol) server**. It powers "Alicia", a Spanish-language AI hotel receptionist defined in [LLM.MD](LLM.MD). The MCP tools are the backend that the AI calls to create, modify, and cancel reservations.

Two Docker services:
- **db** — PostgreSQL, initialized by [database/init-db.sql](database/init-db.sql)
- **mcp_server** — Python/FastMCP server on port 8000, served via uvicorn

## Commands

```bash
# Start everything (rebuilds images)
docker-compose up --build

# Start in background
docker-compose up -d --build

# Start only the database (useful when running the server locally)
docker-compose up db

# Run the MCP server locally (from mcp_server/)
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Reset the database (drops and recreates all tables + seed data)
docker-compose down -v && docker-compose up --build
```

There is no test suite currently.

## Architecture

### Request flow

```
LLM (Alicia) → MCP client → HTTP POST /mcp (Bearer token) → FastMCP → tool function → asyncpg → PostgreSQL
```

### Key files

| File | Role |
|------|------|
| [mcp_server/server.py](mcp_server/server.py) | ASGI app: mounts FastMCP, adds CORS + Bearer auth middleware |
| [mcp_server/instance.py](mcp_server/instance.py) | Single `FastMCP("HotelBookings")` instance shared by all tools |
| [mcp_server/tools/__init__.py](mcp_server/tools/__init__.py) | Imports both tool modules to register them on the `mcp` instance |
| [mcp_server/tools/habitaciones.py](mcp_server/tools/habitaciones.py) | Room/date tools: `obtener_fecha_actual`, `calcular_fecha`, `obtener_opciones_habitacion`, `verificar_disponibilidad`, `calcular_presupuesto` |
| [mcp_server/tools/reservas.py](mcp_server/tools/reservas.py) | Booking CRUD: `crear_reserva`, `obtener_reservas_cliente`, `modificar_reserva`, `cancelar_reserva` |
| [mcp_server/db.py](mcp_server/db.py) | `obtener_conexion_db()` — creates a fresh `asyncpg` connection per call (no pool) |
| [mcp_server/validators.py](mcp_server/validators.py) | Pure helpers: `validar_fechas`, `validar_telefono`, `calcular_noches`, `formatear_precio` |
| [mcp_server/config.py](mcp_server/config.py) | Reads env vars: `DATABASE_URL`, `MCP_API_KEY`, `PRECIO_DESAYUNO_POR_NOCHE`, `PRECIO_TRANSPORTE_AEROPUERTO` |
| [database/init-db.sql](database/init-db.sql) | Schema DDL + seed data (room types, sample rooms, sample users/bookings) |
| [LLM.MD](LLM.MD) | System prompt for the Alicia AI — defines conversation flows A (new booking) and B (manage existing) |

### Database schema

```
RoomTypes  ←  Rooms  ←  RoomAssignments  →  Bookings  →  Users
```

- **RoomTypes**: id, name, base_price, max_occupancy, description
- **Rooms**: room_number, room_type_id, status (Available/Dirty/Maintenance)
- **Users**: full_name, phone (unique — upserted on each booking)
- **Bookings**: user_id, check_in_date, check_out_date, total_amount, status, desayuno_incluido, transporte_aeropuerto
- **RoomAssignments**: booking_id → room_id (a specific physical room is assigned per booking)

Availability is checked by finding rooms whose `id` does NOT appear in `RoomAssignments` for overlapping confirmed bookings.

### Adding a new tool

1. Add a `@mcp.tool()` async function in the appropriate file in `mcp_server/tools/`.
2. Import `mcp` from `instance`, `obtener_conexion_db` from `db`, and helpers from `validators`/`config` as needed.
3. Tools must return a plain string (it will be read aloud by the AI).
4. Always `await conn.close()` in a `finally` block.

### Environment variables (`.env`)

```
DB_USER, DB_PASSWORD, DB_NAME       # PostgreSQL credentials
MCP_API_KEY                          # Bearer token for the MCP endpoint (set to empty string to disable auth)
PRECIO_DESAYUNO_POR_NOCHE            # Breakfast add-on price per night (default 15.00)
PRECIO_TRANSPORTE_AEROPUERTO         # Airport transfer flat fee (default 60.00)
```

### `formatear_precio`

All prices returned to the LLM use `formatear_precio()` which produces TTS-friendly strings like `"120 euros"` or `"15 euros con 50 céntimos"` instead of decimal numbers.
