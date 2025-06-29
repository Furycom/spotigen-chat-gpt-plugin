from fastapi import APIRouter, HTTPException
from .auth import valid_access_token
import httpx

router = APIRouter()

@router.get("/top_tracks")
async def top_tracks():
    token = valid_access_token()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.spotify.com/v1/me/top/tracks?limit=5",
            headers={"Authorization": f"Bearer {token}"}
        )
    return r.json()
