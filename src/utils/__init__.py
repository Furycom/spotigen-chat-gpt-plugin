from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.spotify import SpotifyClient

from .http import safe_get  # re-export

bearer_scheme = HTTPBearer(auto_error=False)


def ensure_token_passed(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if not credentials or credentials.scheme != "Bearer" or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid or missing access token")
    return credentials.credentials


def get_spotify_client(access_token: str = Depends(ensure_token_passed)):
    return SpotifyClient(access_token)


def get_redis_spotify_client():
    from src.auth import valid_access_token

    token = valid_access_token()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return SpotifyClient(token)
