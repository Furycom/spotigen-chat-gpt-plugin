from src.index import app

try:
    from api.auth import router as auth_router
except ModuleNotFoundError:
    from src.auth import router as auth_router

if not any(getattr(route, 'path', '').startswith('/auth') for route in app.router.routes):
    app.include_router(auth_router, prefix="/auth", tags=["auth"])

__all__ = ["app"]
