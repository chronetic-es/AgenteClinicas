from instance import mcp
import calendario
import datetime
import config

@mcp.tool()
async def ResolverDuda() ->str:
    return ""


@mcp.tool()
async def crearEvento()->str:
    service = calendario.getCalendarInstance()

    start_time = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(hours=1)
    end_time = start_time + datetime.timedelta(hours=1)


    event = {
        'summary': 'Prueba',
        'description':'Esto es una prueba',
        'start':{
            'dateTime':start_time.isoformat(),
            'timezone':'UTC'
        },
        'end':{
            'dateTime':end_time.isoformat(),
            'timezone':'UTC'
        }
    }

    created_event = service.events().insert(
        calendarId=config.CALENDAR_ID,
        body=event
    ).execute()

    return "Evento creado con éxito"

@mcp.tool()
async def PruebaCalendario()->str:
    service = calendario.getCalendarInstance()
    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

    events_result = (
        service.events()
        .list(
            calendarId=config.CALENDAR_ID,
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events: 
        return "No hay eventos"

    
    for event in events: 
        return event["start"].get("dateTime", event["start"].get("date"))
    
    
    return "Error"