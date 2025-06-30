import os, sys, importlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient


def test_no_duplicate_recos(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import src.index, api.index
    import src.services.spotify as spotify

    class FakeRedis:
        def __init__(self):
            self.store = {"recommended:me": {"a"}}
        def smembers(self, k):
            return list(self.store.get(k, set()))
        def sadd(self, k, *vals):
            self.store.setdefault(k, set()).update(vals)
        def get(self, k):
            return None
        def set(self, *a, **k):
            pass

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
            return DummyResp({"tracks": [{"uri": "a"}, {"uri": "b"}]})

    monkeypatch.setattr(spotify.httpx, "AsyncClient", DummyAsyncClient)
    fake = FakeRedis()
    monkeypatch.setattr("src.services.spotify._redis", fake, raising=False)
    monkeypatch.setattr("src.storage._redis", fake, raising=False)
    import src.utils as utils
    monkeypatch.setattr(utils, "get_redis_spotify_client", lambda: spotify.SpotifyClient("token"))

    importlib.reload(src.services.spotify)
    importlib.reload(src.index)
    importlib.reload(api.index)

    client = TestClient(api.index.app)
    r = client.get("/recommend")
    assert r.status_code == 200
    assert r.json() == [{"uri": "b"}]
