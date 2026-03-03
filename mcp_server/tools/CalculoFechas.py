from datetime import date, timedelta,time,datetime,timezone
from zoneinfo import ZoneInfo
import json
import calendario
import config

from instance import mcp
from validators import validar_fechas, calcular_noches, formatear_precio


_DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

def check_event_overlap(date_to_check,events) -> bool:
    is_valid_time = True
    for event in events:
        if datetime.fromisoformat(event['start']['dateTime'])<= date_to_check< datetime.fromisoformat(event['end']['dateTime']):
            is_valid_time = False

    return is_valid_time

def date_to_text(date_hour,date_minute) -> str:
    hour_in_text = {
        9 : "Nueve",10 : "Diez" , 11 : "Once" , 12: "Doce" , 13: "Una" , 14 : "Dos",
        16 : "Cuatro" , 17 : "Cinco" , 18 : "Seis" , 19 : "Siete" , 20 : "Ocho"
    }
    minutes_in_text = {
        15: "Cuarto" , 30 :"Media", 45:"Menos cuarto"
    }

    return f"la{'s' if date_hour != 13 else ''} {hour_in_text.get(date_hour)} {'' if date_minute== 0 else 'y' + minutes_in_text.get(date_minute)}"


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

    start_time = time(hour=start_hour,minute=start_minutes)
    end_time = time(hour=end_hour,minute=end_minutes)

    time_frame_start =datetime.combine(start,start_time,tzinfo=ZoneInfo("Europe/Paris"))
    time_frame_end = datetime.combine(end,end_time,tzinfo=ZoneInfo("Europe/Paris"))


    events_result = (
        calendar_instance.events()
        .list(
            calendarId=config.CALENDAR_ID,
            timeMin=(time_frame_start - timedelta(minutes=1)).isoformat(),
            timeMax=(time_frame_end + timedelta(minutes=1)).isoformat(),
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items",[])

    results = {}

    for i in range(0,(end_date-start_date) +1 ,1 ):
        today = time_frame_start + timedelta(days=i)
        today_events = filter(lambda event: datetime.fromisoformat(event['start']['dateTime']).toordinal() == today.toordinal(),events)
        service_time = config.SERVICIOS.get(servicio)
        if today.weekday() == 6 : 
            continue
        if today.weekday() == 5 and today.hour >= 14:
             continue
        if start_hour == end_hour and start_minutes == end_minutes: 
            if check_event_overlap(temp,today_events):
                    results.update({f"{today.day}-{today.month}-{today.year}":
                                    {
                                        "alternativas":date_to_text(temp.hour,temp.minute),
                                        "alternativas_hhmm":f"{temp.hour}:{'00' if temp.minute == 0 else temp.minute}",
                                    }})     
                           
            temp = temp + timedelta(minutes=service_time)
            continue
        if today.hour < 14:
            temp = today
            for j in range((today.hour*60) + today.minute,(end_hour*60) if (end_hour*60) <(14*60)  else (14*60),service_time):

                if check_event_overlap(temp,today_events):
                    results.update({f"{today.day}-{today.month}-{today.year}":
                                    {
                                        "alternativas":date_to_text(temp.hour,temp.minute),
                                        "alternativas_hhmm":f"{temp.hour}:{'00' if temp.minute == 0 else temp.minute}",
                                    }})     
                           
                temp = temp + timedelta(minutes=service_time)

        if end_hour > 16 and start_hour < 16 :
            today = today.replace(hour=16,minute=0)

        if today.hour >= 16 and today.weekday()!= 5 :
            temp = today
            for j in range((today.hour*60) + today.minute, (end_hour*60) if (end_hour*60) < (20*60) else (20*60),service_time):  
                if check_event_overlap(temp,today_events):
                    results.update({f"{today.day}-{today.month}-{today.year}":
                                    {
                                        "alternativas":date_to_text(temp.hour,temp.minute),
                                        "alternativas_hhmm":f"{temp.hour}:{'00' if temp.minute == 0 else temp.minute}",
                                    }})     
                           
                temp = temp + timedelta(minutes=service_time)


    return results