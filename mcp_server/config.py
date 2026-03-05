import os
from dotenv import load_dotenv

load_dotenv()

MCP_API_KEY: str | None = os.getenv("MCP_API_KEY")
GOOGLE_CALENDAR_ID: str = os.getenv("GOOGLE_CALENDAR_ID", "")
GOOGLE_CREDENTIALS: str = os.getenv("GOOGLE_CREDENTIALS", "")

# ──────────────────────────────────────────────────────────────────────────────
# Servicios disponibles en la clínica.
# Edita aquí para cambiar nombre, duración o número de plazas simultáneas.
# ──────────────────────────────────────────────────────────────────────────────
SERVICIOS: dict[str, dict] = {
    "depilacion": {
        "nombre": "Depilación",
        "duracion_min": 30,
        "max_paralelo": 2,   # plazas simultáneas para este servicio
    },
    "fisioterapia": {
        "nombre": "Fisioterapia",
        "duracion_min": 60,
        "max_paralelo": 1,
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Horario de la clínica.
# Cada día lleva una lista de tramos (hora_inicio, hora_fin) en formato "HH:MM".
# Día vacío = cerrado. Clave "miercoles" sin tilde para evitar problemas de encoding.
# ──────────────────────────────────────────────────────────────────────────────
HORARIO: dict[str, list[tuple[str, str]]] = {
    "lunes":     [("09:00", "13:00"), ("16:00", "20:00")],
    "martes":    [("09:00", "13:00"), ("16:00", "20:00")],
    "miercoles": [("09:00", "13:00"), ("16:00", "20:00")],
    "jueves":    [("09:00", "13:00"), ("16:00", "20:00")],
    "viernes":   [("09:00", "13:00"), ("16:00", "20:00")],
    "sabado":    [("09:00", "13:00")],
    "domingo":   [],
}

TIMEZONE: str = "Europe/Madrid"
