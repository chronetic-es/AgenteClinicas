from datetime import date

from instance import mcp
from validators import validar_fechas, validar_telefono, formatear_precio

@mcp.tool()
async def AgendarCita() -> str:
    return ""

@mcp.tool()
async def RecordarCita() -> str:
    return ""

@mcp.tool()
async def CancelarCita() -> str:
    return ""






