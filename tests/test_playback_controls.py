import os, sys, importlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient


def test_pause_requires_auth(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import src.index, api.index
    importlib.reload(src.index)
    importlib.reload(api.index)
    client = TestClient(api.index.app)
    r = client.post("/pause")
    assert r.status_code == 401
