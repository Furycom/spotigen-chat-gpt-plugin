import os, sys, importlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient


def test_top_tracks_no_token(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import src.index, src.tracks, api.index
    importlib.reload(src.index)
    importlib.reload(src.tracks)
    monkeypatch.setattr(src.tracks, "valid_access_token", lambda: None)
    importlib.reload(api.index)
    client = TestClient(api.index.app)
    r = client.get("/top_tracks")
    # Missing Authorization header should return 401
    assert r.status_code == 401
