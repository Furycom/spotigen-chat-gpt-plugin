import os, sys, importlib, urllib.parse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
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
    # allow query parameters like /spec.json?v=10
    assert urllib.parse.urlparse(openapi_url).path.endswith("/spec.json")
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
