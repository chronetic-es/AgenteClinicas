from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import (
    GOOGLE_CALENDAR_ID,
    GOOGLE_SA_TYPE,
    GOOGLE_SA_PROJECT_ID,
    GOOGLE_SA_PRIVATE_KEY_ID,
    GOOGLE_SA_PRIVATE_KEY,
    GOOGLE_SA_CLIENT_EMAIL,
    GOOGLE_SA_CLIENT_ID,
    GOOGLE_SA_AUTH_URI,
    GOOGLE_SA_TOKEN_URI,
    GOOGLE_SA_AUTH_PROVIDER_CERT_URL,
    GOOGLE_SA_CLIENT_CERT_URL,
    GOOGLE_SA_UNIVERSE_DOMAIN,
)

_SCOPES = ["https://www.googleapis.com/auth/calendar"]

CALENDAR_ID: str = GOOGLE_CALENDAR_ID


def obtener_cliente_gcal():
    """Returns an authenticated Google Calendar API client."""
    info = {
        "type": GOOGLE_SA_TYPE,
        "project_id": GOOGLE_SA_PROJECT_ID,
        "private_key_id": GOOGLE_SA_PRIVATE_KEY_ID,
        "private_key": GOOGLE_SA_PRIVATE_KEY,
        "client_email": GOOGLE_SA_CLIENT_EMAIL,
        "client_id": GOOGLE_SA_CLIENT_ID,
        "auth_uri": GOOGLE_SA_AUTH_URI,
        "token_uri": GOOGLE_SA_TOKEN_URI,
        "auth_provider_x509_cert_url": GOOGLE_SA_AUTH_PROVIDER_CERT_URL,
        "client_x509_cert_url": GOOGLE_SA_CLIENT_CERT_URL,
        "universe_domain": GOOGLE_SA_UNIVERSE_DOMAIN,
    }
    creds = service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)
