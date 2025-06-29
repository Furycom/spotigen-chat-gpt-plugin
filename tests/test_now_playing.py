import os, sys, importlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient


def _setup(monkeypatch, resp):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import src.index, src.tracks, api.index
    importlib.reload(src.index)
    importlib.reload(src.tracks)

    class DummyAsyncClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def get(self, *args, **kwargs):
            return resp

    monkeypatch.setattr(src.tracks, "valid_access_token", lambda: "abc")
    monkeypatch.setattr(src.tracks.httpx, "AsyncClient", DummyAsyncClient)
    importlib.reload(api.index)
    return TestClient(api.index.app)


def test_currently_playing_none(monkeypatch):
    class Resp:
        status_code = 204
        def json(self):
            return {}
    client = _setup(monkeypatch, Resp())
    r = client.get("/currently_playing")
    assert r.status_code == 204


def test_currently_playing_track(monkeypatch):
    class Resp:
        status_code = 200
        def json(self):
            return {"is_playing": True}
    client = _setup(monkeypatch, Resp())
    r = client.get("/currently_playing")
    assert r.status_code == 200
    assert r.json() == {"is_playing": True}
