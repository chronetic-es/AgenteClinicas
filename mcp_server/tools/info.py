from pathlib import Path

from instance import mcp

_INFO_FILE = Path(__file__).parent.parent / "clinic_info.txt"


@mcp.tool()
async def obtener_info_clinica() -> str:
    """Devuelve información general de la clínica (servicios, precios, políticas, ubicación, etc.)."""
    try:
        return _INFO_FILE.read_text(encoding="utf-8").strip() or "No hay información disponible todavía."
    except FileNotFoundError:
        return "No hay información disponible todavía."
