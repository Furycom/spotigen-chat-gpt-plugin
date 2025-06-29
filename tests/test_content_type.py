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
from fastapi.testclient import TestClient

import src.index
import importlib

def test_openapi_content_type(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    importlib.reload(src.index)
    client = TestClient(src.index.app)
    r = client.get("/spec.json?v=7")
    assert r.headers["content-type"].startswith("application/json")
