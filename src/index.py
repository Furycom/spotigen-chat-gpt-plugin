import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.dtos.api import TrackTitles, TrackURIs
from src.services.spotify import SpotifyClient
from src.utils import get_spotify_client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    servers=[{"url": "https://spotigen-chat-gpt-plugin-production.up.railway.app"}],
    openapi_url=None,
    docs_url=None,
)

_ENV = os.getenv("VERCEL_ENV", "development")  # Railway → "production" / local → dev

origins = ["https://chat.openai.com"] if _ENV == "production" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (.well‑known + logo)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")

# ---------------------------------------------------------------------------
# Generic plugin endpoints (logo, openapi)
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    """Health‑check root."""
    return {"message": "Welcome to Spotigen – a ChatGPT plugin for Spotify!"}


@app.get("/logo.png", include_in_schema=False)
async def plugin_logo() -> FileResponse:
    """Serve the logo used by the plugin marketplace."""
    return FileResponse("static/logo.png", media_type="image/png")


@app.get("/spec.json", include_in_schema=False)
async def custom_openapi() -> FileResponse:
    """Serve the OpenAPI specification so ChatGPT can parse it."""
    return FileResponse(ROOT_DIR / "spec.json", media_type="application/json")


# ---------------------------------------------------------------------------
# Spotify business endpoints
# ---------------------------------------------------------------------------

@app.get("/playlist")
async def get_playlist(
    name: str,
    spotify_client: Annotated[SpotifyClient, Depends(get_spotify_client)],
):
    playlist = await spotify_client.find_playlist(name)
    if playlist is None:
        return JSONResponse(status_code=404, content={"message": "Playlist not found"})
    return playlist


@app.post("/playlist")
async def create_playlist(
    name: str,
    public: bool,
    spotify_client: Annotated[SpotifyClient, Depends(get_spotify_client)],
):
    playlist_id = await spotify_client.create_playlist(name, public)
    return {"playlist_id": playlist_id}


@app.get("/playlist/{playlist_id}/tracks")
async def get_playlist_tracks(
    playlist_id: str,
    spotify_client: Annotated[SpotifyClient, Depends(get_spotify_client)],
):
    return await spotify_client.get_tracks_from_playlist(playlist_id)


@app.post("/playlist/{playlist_id}/tracks")
async def add_tracks_to_playlist(
    playlist_id: str,
    track_titles: TrackTitles,
    spotify_client: Annotated[SpotifyClient, Depends(get_spotify_client)],
):
    await spotify_client.add_tracks_to_playlist(playlist_id, track_titles)
    return PlainTextResponse(status_code=200)


@app.delete("/playlist/{playlist_id}/tracks")
async def remove_tracks_from_playlist(
    playlist_id: str,
    track_uris: TrackURIs,
    spotify_client: Annotated[SpotifyClient, Depends(get_spotify_client)],
):
    await spotify_client.remove_tracks_from_playlist(playlist_id, track_uris)
    return PlainTextResponse(status_code=200)


@app.post("/play")
async def resume_playback(
    spotify_client: Annotated[SpotifyClient, Depends(get_spotify_client)],
):
    await spotify_client.play()
    return PlainTextResponse(status_code=200)


@app.post("/pause")
async def pause_playback(
    spotify_client: Annotated[SpotifyClient, Depends(get_spotify_client)],
):
    await spotify_client.pause()
    return PlainTextResponse(status_code=200)


@app.post("/next")
async def next_track(
    spotify_client: Annotated[SpotifyClient, Depends(get_spotify_client)],
):
    await spotify_client.next()
    return PlainTextResponse(status_code=200)


@app.post("/previous")
async def previous_track(
    spotify_client: Annotated[SpotifyClient, Depends(get_spotify_client)],
):
    await spotify_client.previous()
    return PlainTextResponse(status_code=200)
