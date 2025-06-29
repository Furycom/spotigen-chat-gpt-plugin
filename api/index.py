from src.index import app

from src.tracks import router as tracks_router

try:
    from api.auth import router as auth_router
except ModuleNotFoundError:
    from src.auth import router as auth_router

if not any(getattr(route, 'path', '').startswith('/auth') for route in app.router.routes):
    app.include_router(auth_router, prefix="/auth", tags=["auth"])

app.include_router(tracks_router)

__all__ = ["app"]
