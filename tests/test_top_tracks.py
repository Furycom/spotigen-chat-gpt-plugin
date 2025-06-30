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


def test_top_tracks_with_token(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import src.index, src.tracks, api.index
    importlib.reload(src.index)
    importlib.reload(src.tracks)

    class DummyResp:
        status_code = 200
        def json(self):
            return ["ok"]

    class DummyAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, *args, **kwargs):
            return DummyResp()

    monkeypatch.setattr(src.tracks, "valid_access_token", lambda: "abc")
    monkeypatch.setattr(src.tracks.httpx, "AsyncClient", DummyAsyncClient)
    importlib.reload(api.index)

    client = TestClient(api.index.app)
    r = client.get("/top_tracks")
    assert r.status_code == 200


def test_top_tracks_params(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import src.index, src.tracks, api.index
    importlib.reload(src.index)
    importlib.reload(src.tracks)

    class DummyResp:
        status_code = 200
        def json(self):
            return list(range(50))

    class DummyAsyncClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def get(self, *args, **kwargs):
            assert kwargs.get("params", {}).get("limit") == 50
            assert kwargs.get("params", {}).get("time_range") == "long_term"
            return DummyResp()

    monkeypatch.setattr(src.tracks, "valid_access_token", lambda: "abc")
    monkeypatch.setattr(src.tracks.httpx, "AsyncClient", DummyAsyncClient)
    importlib.reload(api.index)

    client = TestClient(api.index.app)
    r = client.get("/top_tracks?limit=50&time_range=long_term")
    assert r.status_code == 200
    assert len(r.json()) == 50
