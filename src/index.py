import os
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from src.dtos.api import TrackTitles, TrackURIs
from src.services.spotify import SpotifyClient
from src.services.lastfm import LastFMService
from src.utils import get_redis_spotify_client, get_spotify_client

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
    return FileResponse("static/spec.json", media_type="application/json")


# ---------------------------------------------------------------------------
# Last.fm helper endpoints
# ---------------------------------------------------------------------------


@app.get("/lastfm/tags")
async def lastfm_tags(artist: str, title: str, limit: int = 5):
    service = LastFMService()
    return service.track_tags(artist, title, limit)


@app.get("/lastfm/scrobbles")
async def lastfm_scrobbles(start: int, end: int):
    service = LastFMService()
    return service.scrobble_history(start, end)


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
        raise HTTPException(404, "Playlist not found")
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
    true_id = await spotify_client._playlist_id(playlist_id)
    return await spotify_client.get_tracks_from_playlist(true_id)


@app.post("/playlist/{playlist_id}/tracks")
async def add_tracks_to_playlist(
    playlist_id: str,
    track_titles: TrackTitles,
    spotify_client: Annotated[SpotifyClient, Depends(get_spotify_client)],
):
    true_id = await spotify_client._playlist_id(playlist_id)
    await spotify_client.add_tracks_to_playlist(true_id, track_titles)
    return PlainTextResponse(status_code=200)


@app.delete("/playlist/{playlist_id}/tracks")
async def remove_tracks_from_playlist(
    playlist_id: str,
    track_uris: TrackURIs,
    spotify_client: Annotated[SpotifyClient, Depends(get_spotify_client)],
):
    true_id = await spotify_client._playlist_id(playlist_id)
    await spotify_client.remove_tracks_from_playlist(true_id, track_uris)
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


@app.get("/playlists")
async def playlists(
    spotify_client: Annotated[SpotifyClient, Depends(get_redis_spotify_client)],
    limit: int = 20,
    offset: int = 0,
):
    return await spotify_client.get_playlists(limit=limit, offset=offset)


@app.get("/library/tracks")
async def library_tracks(
    spotify_client: Annotated[SpotifyClient, Depends(get_redis_spotify_client)],
    limit: int = 50,
    offset: int = 0,
):
    return await spotify_client.get_library_tracks(limit=limit, offset=offset)


@app.get("/library/albums")
async def library_albums(
    spotify_client: Annotated[SpotifyClient, Depends(get_redis_spotify_client)],
    limit: int = 50,
    offset: int = 0,
):
    return await spotify_client.get_library_albums(limit=limit, offset=offset)


@app.get("/follow/artists")
async def followed_artists(
    spotify_client: Annotated[SpotifyClient, Depends(get_redis_spotify_client)],
    limit: int = 50,
    after: str | None = None,
):
    return await spotify_client.get_followed_artists(limit=limit, after=after)


@app.put("/follow/artists/{artist_id}")
async def follow_artist(
    artist_id: str,
    spotify_client: Annotated[SpotifyClient, Depends(get_redis_spotify_client)],
):
    await spotify_client.follow_artist(artist_id)
    return PlainTextResponse(status_code=200)


@app.delete("/follow/artists/{artist_id}")
async def unfollow_artist(
    artist_id: str,
    spotify_client: Annotated[SpotifyClient, Depends(get_redis_spotify_client)],
):
    await spotify_client.unfollow_artist(artist_id)
    return PlainTextResponse(status_code=200)


@app.get("/search")
async def search(
    spotify_client: Annotated[SpotifyClient, Depends(get_redis_spotify_client)],
    q: str,
    type: str = "track,artist,album",
    limit: int = 10,
):
    return await spotify_client.search(q, type=type, limit=limit)


@app.get("/recommend")
async def recommend(
    spotify_client: Annotated[SpotifyClient, Depends(get_redis_spotify_client)],
    seed_tracks: str = "",
    seed_artists: str = "",
    seed_genres: str = "",
    limit: int = 20,
):
    return await spotify_client.recommendations(
        seed_tracks=seed_tracks,
        seed_artists=seed_artists,
        seed_genres=seed_genres,
        limit=limit,
    )


@app.get("/profile")
async def profile(
    spotify_client: Annotated[SpotifyClient, Depends(get_redis_spotify_client)],
):
    return await spotify_client.get_profile()
