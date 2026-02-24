from instance import mcp
import tools  # noqa: F401 — registers all tools on mcp
from config import MCP_API_KEY
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

app = mcp.http_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id"],
)


class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if MCP_API_KEY and request.method != "OPTIONS":
            auth = request.headers.get("Authorization", "")
            print(f"[AUTH] received='{auth}' expected='Bearer {MCP_API_KEY}'", flush=True)
            if not auth.startswith("Bearer ") or auth[7:] != MCP_API_KEY:
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)


app.add_middleware(BearerAuthMiddleware)
