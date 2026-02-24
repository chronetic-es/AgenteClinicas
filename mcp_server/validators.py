from datetime import date


def calcular_noches(entrada: str, salida: str) -> int:
    d1 = date.fromisoformat(entrada)
    d2 = date.fromisoformat(salida)
    return (d2 - d1).days


def validar_fechas(fecha_entrada: str, fecha_salida: str) -> str | None:
    """Valida formato y lógica de fechas. Devuelve mensaje de error o None si son válidas."""
    try:
        d_entrada = date.fromisoformat(fecha_entrada)
        d_salida = date.fromisoformat(fecha_salida)
    except ValueError:
        return "Las fechas deben estar en formato AAAA-MM-DD."

    if d_entrada < date.today():
        return "La fecha de entrada no puede ser en el pasado."
    if d_salida <= d_entrada:
        return "La fecha de salida debe ser posterior a la fecha de entrada."
    return None


def formatear_precio(valor: float) -> str:
    """Convierte un precio decimal a texto legible por TTS: 123 euros con 45 céntimos."""
    centimos_total = round(valor * 100)
    euros = centimos_total // 100
    cts = centimos_total % 100
    if cts == 0:
        return f"{euros} euros"
    return f"{euros} euros con {cts} céntimos"


def validar_telefono(telefono: str) -> str | None:
    """Valida que el teléfono sea razonablemente válido."""
    digitos = "".join(c for c in telefono if c.isdigit())
    if len(digitos) < 7 or len(telefono) > 25:
        return "El número de teléfono no parece válido."
    return None
