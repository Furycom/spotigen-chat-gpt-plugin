import os, sys, types, importlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    import httpx  # type: ignore
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
    # Missing Authorization header should return 403
    assert r.status_code == 403
