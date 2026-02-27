import os
from dotenv import load_dotenv

load_dotenv()


MCP_API_KEY: str | None = os.getenv("MCP_API_KEY")
SERVICE_ACCOUNT_FILE = os.getenv("CREDENTIALS")
