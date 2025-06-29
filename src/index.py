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
    return FileResponse(ROOT_DIR / "openapi.json", media_type="application/json")


# ---------------------------------------------------------------------------
# Spotify business endpoints
# ---------------------------------------------------------------------------

@app.get("/playlist")
async def get_playlist(
    name: str,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    playlist = await spotify_client.find_playlist(name)
    if playlist is None:
        return JSONResponse(status_code=404, content={"message": "Playlist not found"})
    return playlist


@app.post("/playlist")
async def create_playlist(
    name: str,
    public: bool,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    playlist_id = await spotify_client.create_playlist(name, public)
    return {"playlist_id": playlist_id}


@app.get("/playlist/{playlist_id}/tracks")
async def get_playlist_tracks(
    playlist_id: str,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    return await spotify_client.get_tracks_from_playlist(playlist_id)


@app.post("/playlist/{playlist_id}/tracks")
async def add_tracks_to_playlist(
    playlist_id: str,
    track_titles: TrackTitles,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    await spotify_client.add_tracks_to_playlist(playlist_id, track_titles)
    return PlainTextResponse(status_code=200)


@app.delete("/playlist/{playlist_id}/tracks")
async def remove_tracks_from_playlist(
    playlist_id: str,
    track_uris: TrackURIs,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    await spotify_client.remove_tracks_from_playlist(playlist_id, track_uris)
    return PlainTextResponse(status_code=200)


# ---------------------------------------------------------------------------
# Additional Spotify endpoints
# ---------------------------------------------------------------------------


@app.get("/search")
async def search_tracks(
    q: str,
    limit: int = 10,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    return await spotify_client.search_tracks(q, limit)


@app.get("/recommendations")
async def recommendations(
    seed_tracks: list[str],
    limit: int = 20,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    return await spotify_client.get_recommendations(seed_tracks, limit)


@app.get("/audio_features")
async def audio_features(
    track_ids: list[str],
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    return await spotify_client.audio_features(track_ids)


@app.get("/recent")
async def recent_tracks(
    limit: int = 50,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    return await spotify_client.recent_tracks(limit)


@app.get("/top_tracks")
async def top_tracks(
    limit: int = 50,
    time_range: str = "long_term",
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    return await spotify_client.top_tracks(limit, time_range)


@app.get("/top_artists")
async def top_artists(
    limit: int = 50,
    time_range: str = "long_term",
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    return await spotify_client.top_artists(limit, time_range)


@app.get("/stats")
async def stats(
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    return await spotify_client.stats()


@app.post("/queue")
async def add_queue(
    track_uri: str,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    await spotify_client.queue(track_uri)
    return PlainTextResponse(status_code=200)


@app.get("/devices")
async def devices(
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    return await spotify_client.devices()


@app.post("/play")
async def play(
    track_uri: str | None = None,
    device_id: str | None = None,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    await spotify_client.play(track_uri, device_id)
    return PlainTextResponse(status_code=200)


@app.post("/pause")
async def pause(
    device_id: str | None = None,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    await spotify_client.pause(device_id)
    return PlainTextResponse(status_code=200)


@app.post("/skip_next")
async def skip_next(
    device_id: str | None = None,
    spotify_client: SpotifyClient = Depends(get_spotify_client),
):
    await spotify_client.skip_next(device_id)
    return PlainTextResponse(status_code=200)

