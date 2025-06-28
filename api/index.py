from src.index import app
app.include_router(auth_router, prefix="/auth")
