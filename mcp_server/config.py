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
    "fisioterapia": {
        "nombre": "Fisioterapia",
        "duracion_min": 60,
        "max_paralelo": 2,   # plazas simultáneas para este servicio
    },
    "presoterapia": {
        "nombre": "Presoterapia",
        "duracion_min": 30,
        "max_paralelo": 1,
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Horario de la clínica.
# Cada día lleva una lista de tramos (hora_inicio, hora_fin) en formato "HH:MM".
# Día vacío = cerrado. Clave "miercoles" sin tilde para evitar problemas de encoding.
# ──────────────────────────────────────────────────────────────────────────────
HORARIO: dict[str, list[tuple[str, str]]] = {
    "lunes":     [("09:00", "14:00"), ("16:00", "21:00")],
    "martes":    [("09:00", "14:00"), ("16:00", "21:00")],
    "miercoles": [("09:00", "14:00"), ("16:00", "21:00")],
    "jueves":    [("09:00", "14:00"), ("16:00", "21:00")],
    "viernes":   [("09:00", "14:00"), ("16:00", "21:00")],
    "sabado":    [("10:00", "13:30")],
    "domingo":   [],
}

TIMEZONE: str = "Europe/Madrid"
