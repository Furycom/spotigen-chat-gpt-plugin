import os, sys, importlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient


def test_name_resolves_to_id(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import api.index
    import src.index
    import src.services.spotify as spotify

    class DummyResp:
        def __init__(self, data):
            self.status_code = 200
            self._data = data
            self.text = ""
        def json(self):
            return self._data

    class DummyAsyncClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def get(self, url, headers=None, params=None):
            if url.endswith("/me"):
                return DummyResp({"id": "me"})
            if url.startswith("https://api.spotify.com/v1/me/playlists"):
                return DummyResp({
                    "items": [
                        {"name": "House 2025", "id": "1234567890123456789012", "owner": {"id": "me"}}
                    ],
                    "next": None,
                })
            if url.startswith("https://api.spotify.com/v1/playlists/1234567890123456789012/tracks"):
                return DummyResp({"items": []})
            raise AssertionError(f"unexpected {url}")

    monkeypatch.setattr(spotify.httpx, "AsyncClient", DummyAsyncClient)
    importlib.reload(src.index)
    importlib.reload(api.index)
    client = TestClient(api.index.app)
    r = client.get("/playlist/House%202025/tracks", headers={"Authorization": "Bearer x"})
    assert r.status_code == 200

