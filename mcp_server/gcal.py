import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import GOOGLE_CALENDAR_ID, GOOGLE_CREDENTIALS

_SCOPES = ["https://www.googleapis.com/auth/calendar"]

CALENDAR_ID: str = GOOGLE_CALENDAR_ID


def obtener_cliente_gcal():
    """Returns an authenticated Google Calendar API client."""
    info = json.loads(GOOGLE_CREDENTIALS)
    creds = service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)
