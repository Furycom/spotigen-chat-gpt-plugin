import importlib
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient


def test_profile(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import api.index
    import src.index
    import src.utils

    class DummyClient:
        async def get_profile(self):
            return {"display_name": "Bob"}

    monkeypatch.setattr(src.utils, "get_redis_spotify_client", lambda: DummyClient())
    importlib.reload(src.index)
    importlib.reload(api.index)
    client = TestClient(api.index.app)
    r = client.get("/profile")
    assert r.status_code == 200
    assert "display_name" in r.json()
