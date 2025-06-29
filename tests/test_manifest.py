import os, sys, types, importlib, urllib.parse
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
import json
import re


def test_manifest(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import api.index
    client = TestClient(api.index.app)

    resp = client.get("/.well-known/ai-plugin.json")
    assert resp.status_code == 200
    manifest = resp.json()

    openapi_url = manifest["api"]["url"]
    assert openapi_url.endswith("/openapi.json")
    path = urllib.parse.urlparse(openapi_url).path
    spec_resp = client.get(path)
    assert spec_resp.status_code == 200
    if path.endswith(".json"):
        spec = spec_resp.json()
        servers = [s.get("url", "") for s in spec.get("servers", [])]
        assert any(url.startswith("https://spotigen-chat-gpt-plugin-production.") for url in servers)
    else:
        # YAML or plain text fallback
        assert re.search(r"https://spotigen-chat-gpt-plugin-production\.", spec_resp.text)
