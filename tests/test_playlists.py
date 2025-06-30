import importlib
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient


def test_playlists(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import api.index
    import src.index
    import src.utils

    class DummyClient:
        async def get_playlists(self, limit=20, offset=0):
            return [{"id": "1"}]

    monkeypatch.setattr(src.utils, "get_redis_spotify_client", lambda: DummyClient())
    importlib.reload(src.index)
    importlib.reload(api.index)
    client = TestClient(api.index.app)
    r = client.get("/playlists")
    assert r.status_code == 200
    assert len(r.json()) > 0
