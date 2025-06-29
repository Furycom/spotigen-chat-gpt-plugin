import os, sys, types, importlib, pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    import httpx
except ModuleNotFoundError:
    httpx = types.ModuleType("httpx")
    sys.modules["httpx"] = httpx
if hasattr(httpx, "ASGITransport"):
    _orig_init = httpx.Client.__init__
    def _patched_init(self, *args, app=None, **kwargs):
        if app is not None:
            kwargs.setdefault("transport", httpx.ASGITransport(app=app))
        _orig_init(self, *args, **kwargs)
    httpx.Client.__init__ = _patched_init  # type: ignore
class DummyAsyncClient:
    async def __aenter__(self):
        return self
    async def __aexit__(self, *a):
        pass
    async def get(self, *a, **k):
        return types.SimpleNamespace(status_code=200, json=lambda: {"tracks": {"items": [{"name": "Around the World"}]}})
httpx.AsyncClient = DummyAsyncClient
try:
    import openai
except ModuleNotFoundError:
    openai = types.ModuleType("openai")
    class _Chat:
        async def acreate(self, **kwargs):
            raise NotImplementedError
    openai.ChatCompletion = _Chat()
    sys.modules["openai"] = openai
from fastapi.testclient import TestClient


def test_search(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import api.index
    importlib.reload(api.index)
    client = TestClient(api.index.app)
    r = client.get("/search", params={"q": "Daft Punk", "limit": 5}, headers={"Authorization": "Bearer x"})
    assert r.status_code == 200
    assert len(r.json()) >= 1
