import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
MCP_API_KEY: str | None = os.getenv("MCP_API_KEY")
PRECIO_DESAYUNO_POR_NOCHE: float = float(os.getenv("PRECIO_DESAYUNO_POR_NOCHE", "15.00"))
PRECIO_TRANSPORTE_AEROPUERTO: float = float(os.getenv("PRECIO_TRANSPORTE_AEROPUERTO", "60.00"))
