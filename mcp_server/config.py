import os
from dotenv import load_dotenv


load_dotenv()


MCP_API_KEY: str | None = os.getenv("MCP_API_KEY")
CALENDAR_ID: str | None = os.getenv("CALENDAR_ID")
CREDENTIALS: str | None = os.getenv("CREDENTIALS")
SERVICIOS = {
    'Depilación':60,
    'Masaje':30
}