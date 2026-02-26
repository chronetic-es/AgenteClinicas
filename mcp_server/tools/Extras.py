from instance import mcp
import calendario
import datetime

@mcp.tool()
async def ResolverDuda() ->str:
    return ""


@mcp.tool()
async def PruebaCalendario()->str:
    service = calendario.getCalendarInstance()
    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

    events_result = (
        service.events()
        .list(
            calendarId="primary",
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