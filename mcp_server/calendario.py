import datetime
import os.path
import config
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]

SERVICE_ACCOUNT_INFO = config.CREDENTIALS

def getCalendarInstance():

    credentials = service_account.Credentials.from_service_account_info(json.load(SERVICE_ACCOUNT_INFO),scopes=SCOPES)

    try:
        service = build("calendar","v3",credentials=credentials)
        return service
    except HttpError as error:
        return None