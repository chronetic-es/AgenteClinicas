from datetime import date, timedelta,time,datetime,timezone
import json
import calendario
import config

from instance import mcp
from validators import validar_fechas, calcular_noches, formatear_precio


_DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


@mcp.tool()
async def obtener_fecha_actual() -> str:
    """Devuelve la fecha actual con el día de la semana en español, para calcular fechas relativas."""
    hoy = date.today()
    dia_semana = _DIAS_ES[hoy.weekday()]
    mes = _MESES_ES[hoy.month - 1]
    return (
        f"Hoy es {dia_semana}, {hoy.day} de {mes} de {hoy.year}. "
        f"Fecha ISO: {hoy.isoformat()}."
    )


@mcp.tool()
async def calcular_fecha(dias_desde_hoy: int) -> str:
    """Devuelve la fecha ISO y el día de la semana correspondiente a N días desde hoy.
    Úsalo para verificar cualquier fecha relativa: mañana=1, pasado mañana=2, 1 semana=7, etc."""
    d = date.today() + timedelta(days=dias_desde_hoy)
    dia = _DIAS_ES[d.weekday()]
    mes = _MESES_ES[d.month - 1]
    return f"{dia} {d.day} de {mes} de {d.year} → {d.isoformat()}"




@mcp.tool()
async def consultar_disponibilidad(
    start_date:int,end_date:int,
    start_hour:int,end_hour:int,
    start_minutes:int,end_minutes:int,
    servicio:str,
    ) -> dict:
    """Consulta la disponibilidad en el calendario de google.Úsalo cuando tengas un rango de fechas o una fecha exacta.
    """
    calendar_instance = calendario.getCalendarInstance()

    start= date.today() + timedelta(days=start_date)
    end= date.today() + timedelta(days=end_date)

    start_time = time(hour=start_hour-1,minute=59 if start_minutes == 0 else start_minutes-1)
    end_time = time(hour=end_hour,minute=end_minutes+1)

    time_frame_start =datetime.combine(start,start_time,tzinfo=timezone.utc)
    time_frame_end = datetime.combine(end,end_time,tzinfo=timezone.utc)


    events_result = (
        calendar_instance.events()
        .list(
            calendarId=config.CALENDAR_ID,
            timeMin=time_frame_start.isoformat(),
            timeMax=time_frame_end.isoformat(),
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items",[])

    results = {}

    for i in range((end_date - start_date) + 1 ):
        today = time_frame_start + timedelta(days=i)
        today_events = filter(lambda event: datetime.fromisoformat(event['start']['dateTime']).toordinal() == today.toordinal(),events)
        service_time = config.SERVICIOS.get(servicio)
        if today.weekday() == 6 : 
            continue
        if today.weekday() == 5 and today.hour() >= 14:
             continue
        if today.hour < 14:
            temp = today 
            for j in range((today.hour*60) + today.minute,14*60,service_time):
                for event in today_events:
                    if  datetime.fromisoformat(event['start']['dateTime']) <= temp + timedelta(minutes=1) <= datetime.fromisoformat(event['end']['dateTime'])  :  
                        results[f"{today.day}-{today.month}-{today.year}"] = results.get(f"{today.day}-{today.month}-{today.year}") or []
                        results[f"{today.day}-{today.month}-{today.year}"].append(f"{temp.hour+1 if temp.minute+1 == 60 else temp.hour}:{'00' if temp.minute+1==60 else temp.minute+1}")
                        break
                temp = temp + timedelta(minutes=service_time)

        if end_hour > 14:
            today = today.replace(hour=16)

        if today.hour > 16 and today.weekday()!= 5 :
            temp = today
            for j in range((today.hour*60) + today.minute,20*60,service_time):  
                if datetime.fromisoformat(event['start']['dateTime']) <= temp + timedelta(minutes=1) <= datetime.fromisoformat(event['end']['dateTime'])  :
                    results[f"{today.day}-{today.month}-{today.year}"] = results.get(f"{today.day}-{today.month}-{today.year}") or []
                    results[f"{today.day}-{today.month}-{today.year}"].append(f"{temp.hour+1 if temp.minute+1 == 60 else temp.hour}:{'00' if temp.minute+1==60 else temp.minute+1}")
                    break
                temp = temp + timedelta(minutes=service_time)


    return results