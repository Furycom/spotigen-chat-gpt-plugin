import os, sys, urllib.parse, re, importlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient


def test_login_redirect(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/auth/callback")
    import src.auth, api.index
    importlib.reload(src.auth)
    importlib.reload(api.index)
    client = TestClient(api.index.app)
    r = client.get("/auth/login", allow_redirects=False)
    assert r.status_code in (302, 307)
    loc = r.headers["location"]
    parsed = urllib.parse.urlparse(loc)
    qs = urllib.parse.parse_qs(parsed.query)
    assert parsed.netloc == "accounts.spotify.com"
    assert qs["redirect_uri"][0] == "https://example.com/auth/callback"
    assert re.search(r"scope=[^&]*%20", parsed.query)
