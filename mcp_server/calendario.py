import datetime
import os.path
import config

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def getCalendarInstance():

    credentials = service_account.Credentials.from_service_account_file(config.SERVICE_ACCOUNT_FILE,scopes=SCOPES)

    try:
        service = build("calendar","v3",credentials=credentials)
        return service
    except HttpError as error:
        return None