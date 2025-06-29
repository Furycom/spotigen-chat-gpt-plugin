import os, sys, importlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient


def test_recent(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import src.index, src.tracks, api.index
    importlib.reload(src.index)
    importlib.reload(src.tracks)

    class DummyResp:
        status_code = 200
        def json(self):
            return {"items": list(range(20))}

    class DummyAsyncClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def get(self, *args, **kwargs):
            assert kwargs.get("params", {}).get("limit") == 20
            return DummyResp()

    monkeypatch.setattr(src.tracks, "valid_access_token", lambda: "abc")
    monkeypatch.setattr(src.tracks.httpx, "AsyncClient", DummyAsyncClient)
    importlib.reload(api.index)

    client = TestClient(api.index.app)
    r = client.get("/recent?limit=20")
    assert r.status_code == 200
    assert len(r.json()) == 20
