# src/auth.py
from urllib.parse import urlencode, quote
import os, httpx, time
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from .storage import save_tokens, load_tokens

router = APIRouter(tags=["auth"])

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
if not REDIRECT_URI:
    raise ValueError("REDIRECT_URI env var missing; set it in Railway and Spotify dashboard")
REDIRECT_URI = REDIRECT_URI.strip()

SCOPES = (
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing "
    "user-read-recently-played "
    "user-top-read "
    "playlist-read-private "
    "playlist-read-collaborative "
    "playlist-modify-public "
    "playlist-modify-private "
    "user-library-read "
    "user-library-modify "
    "user-follow-read "
    "user-follow-modify "
    "user-read-playback-position"
)

# ---------- Internal helpers -------------------------------------------------



def valid_access_token() -> str | None:
    tokens = load_tokens()
    if not tokens:
        return None
    if tokens["expires_at"] > time.time():
        return tokens["access_token"]

    r = httpx.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if r.status_code == 200:
        new_tokens = tokens | r.json()
        if "expires_in" in new_tokens:
            new_tokens["expires_at"] = int(time.time()) + new_tokens["expires_in"] - 60
        save_tokens(new_tokens)
        return new_tokens["access_token"]
    return None

# ---------- Public routes ----------------------------------------------------

@router.get("/login")
def login():
    """Redirect user to Spotify authorization."""
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    }
    query = urlencode(params, quote_via=quote, safe="")
    return RedirectResponse("https://accounts.spotify.com/authorize?" + query)


@router.get("/callback")
def callback(code: str | None = None, error: str | None = None):
    """Spotify redirect URI used to exchange the `code` for tokens."""
    if error:
        raise HTTPException(400, f"Spotify auth error: {error}")

    r = httpx.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if r.status_code != 200:
        raise HTTPException(r.status_code, "Impossible d’obtenir le jeton Spotify")

    data = r.json()
    data["expires_at"] = int(time.time()) + data.get("expires_in", 0) - 60
    save_tokens(data)
    return JSONResponse({"message": "Authentification réussie."})


@router.get("/refresh")
def refresh():
    """Force refresh of the access token using the stored refresh token."""
    tok = load_tokens()
    if not tok:
        raise HTTPException(400, "Pas de refresh_token enregistré.")

    r = httpx.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": tok["refresh_token"],
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if r.status_code != 200:
        raise HTTPException(r.status_code, "Échec refresh_token")

    new_tok = tok | r.json()
    new_tok["expires_at"] = int(time.time()) + new_tok.get("expires_in", 0) - 60
    save_tokens(new_tok)
    return {"access_token": new_tok["access_token"]}
