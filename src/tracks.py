from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from .auth import valid_access_token
import httpx

router = APIRouter()

@router.get("/top_tracks")
async def top_tracks(limit: int = 5, time_range: str = "medium_term"):
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 50")
    token = valid_access_token()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.spotify.com/v1/me/top/tracks",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": limit, "time_range": time_range},
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@router.get("/recent")
async def recent(limit: int = 20):
    token = valid_access_token()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.spotify.com/v1/me/player/recently-played",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": limit},
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json().get("items", [])


@router.get("/currently_playing")
async def currently_playing():
    token = valid_access_token()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.spotify.com/v1/me/player/currently-playing",
            headers={"Authorization": f"Bearer {token}"},
        )
    if r.status_code == 204:
        return PlainTextResponse(status_code=204)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()
