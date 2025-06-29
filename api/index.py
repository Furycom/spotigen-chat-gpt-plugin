from src.index import app
from fastapi.middleware.cors import CORSMiddleware

from src.tracks import router as tracks_router

try:
    from api.auth import router as auth_router
except ModuleNotFoundError:
    from src.auth import router as auth_router

if not any(getattr(route, 'path', '').startswith('/auth') for route in app.router.routes):
    app.include_router(auth_router, prefix="/auth", tags=["auth"])

app.include_router(tracks_router)

# Ensure CORS is enabled when the app is imported directly from this module.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

__all__ = ["app"]
