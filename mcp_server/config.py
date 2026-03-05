import os
from dotenv import load_dotenv

load_dotenv()

MCP_API_KEY: str | None = os.getenv("MCP_API_KEY")
GOOGLE_CALENDAR_ID: str = os.getenv("GOOGLE_CALENDAR_ID", "")

# Google Service Account credentials
GOOGLE_SA_TYPE: str = os.getenv("GOOGLE_SA_TYPE", "service_account")
GOOGLE_SA_PROJECT_ID: str = os.getenv("GOOGLE_SA_PROJECT_ID", "")
GOOGLE_SA_PRIVATE_KEY_ID: str = os.getenv("GOOGLE_SA_PRIVATE_KEY_ID", "")
GOOGLE_SA_PRIVATE_KEY: str = os.getenv("GOOGLE_SA_PRIVATE_KEY", "")
GOOGLE_SA_CLIENT_EMAIL: str = os.getenv("GOOGLE_SA_CLIENT_EMAIL", "")
GOOGLE_SA_CLIENT_ID: str = os.getenv("GOOGLE_SA_CLIENT_ID", "")
GOOGLE_SA_AUTH_URI: str = os.getenv("GOOGLE_SA_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
GOOGLE_SA_TOKEN_URI: str = os.getenv("GOOGLE_SA_TOKEN_URI", "https://oauth2.googleapis.com/token")
GOOGLE_SA_AUTH_PROVIDER_CERT_URL: str = os.getenv("GOOGLE_SA_AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs")
GOOGLE_SA_CLIENT_CERT_URL: str = os.getenv("GOOGLE_SA_CLIENT_CERT_URL", "")
GOOGLE_SA_UNIVERSE_DOMAIN: str = os.getenv("GOOGLE_SA_UNIVERSE_DOMAIN", "googleapis.com")

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
