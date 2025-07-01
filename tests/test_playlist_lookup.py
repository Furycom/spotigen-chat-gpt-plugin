import os, sys, importlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient


def test_playlist_lookup(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import api.index
    import src.index
    import src.services.spotify as spotify

    class DummyResp:
        def __init__(self, data, status=200):
            self.status_code = status
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
            if url.startswith("https://api.spotify.com/v1/users/me/playlists"):
                return DummyResp({
                    "items": [
                        {"name": "House 2025", "id": "abcd", "owner": {"id": "me"}}
                    ],
                    "next": None,
                })
            raise AssertionError(f"unexpected {url}")

    monkeypatch.setattr(spotify.httpx, "AsyncClient", DummyAsyncClient)
    importlib.reload(src.index)
    importlib.reload(api.index)
    client = TestClient(api.index.app)

    ok = client.get("/playlist", params={"name": "House 2025"}, headers={"Authorization": "Bearer x"})
    assert ok.status_code == 200
    assert "id" in ok.json()

    not_found = client.get("/playlist", params={"name": "missing"}, headers={"Authorization": "Bearer x"})
    assert not_found.status_code == 404
