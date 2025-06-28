# src/auth.py
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
import requests, os, time, json

router = APIRouter(tags=["auth"])

CLIENT_ID      = os.getenv("CLIENT_ID")
CLIENT_SECRET  = os.getenv("CLIENT_SECRET")
REDIRECT_URI   = os.getenv("REDIRECT_URI") or "https://spotigen-chat-gpt-plugin-production.up.railway.app/callback"
SCOPES         = "user-top-read playlist-modify-public playlist-modify-private"

TOKEN_FILE     = "/tmp/spotify_tokens.json"        # ← stockage simple côté serveur

# ---------- Outils internes --------------------------------------------------

def _save_tokens(tokens: dict):
    tokens["expires_at"] = int(time.time()) + tokens["expires_in"] - 60
    with open(TOKEN_FILE, "w") as f: json.dump(tokens, f)

def _load_tokens() -> dict | None:
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        return json.load(f)

def valid_access_token() -> str | None:
    tokens = _load_tokens()
    if not tokens:
        return None
    if tokens["expires_at"] > time.time():
        return tokens["access_token"]

    # → expiré : on rafraîchit
    r = requests.post(
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
    if r.ok:
        new_tokens = tokens | r.json()
        _save_tokens(new_tokens)
        return new_tokens["access_token"]
    return None

# ---------- Routes publiques -------------------------------------------------

@router.get("/login")
def login():
    """Redirige l’utilisateur vers la page d’autorisation Spotify."""
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    }
    return RedirectResponse(
        url="https://accounts.spotify.com/authorize?" + urlencode(params)
    )


@router.get("/callback")
def callback(code: str | None = None, error: str | None = None):
    """Point de retour Spotify : échange le `code` contre des jetons."""
    if error:
        raise HTTPException(400, f"Spotify auth error: {error}")

    r = requests.post(
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
    if not r.ok:
        raise HTTPException(r.status_code, "Impossible d’obtenir le jeton Spotify")

    _save_tokens(r.json())
    return JSONResponse({"message": "Authentification réussie."})


@router.get("/refresh")
def refresh():
    """Forcé : rafraîchir le jeton d’accès avec le refresh_token."""
    tok = _load_tokens()
    if not tok:
        raise HTTPException(400, "Pas de refresh_token enregistré.")

    r = requests.post(
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
    if not r.ok:
        raise HTTPException(r.status_code, "Échec refresh_token")

    new_tok = tok | r.json()
    _save_tokens(new_tok)
    return {"access_token": new_tok["access_token"]}
