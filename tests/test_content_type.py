import importlib
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import importlib

from fastapi.testclient import TestClient

import src.index


def test_openapi_content_type(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    importlib.reload(src.index)
    client = TestClient(src.index.app)
    r = client.get("/spec.json?v=15")
    assert r.headers["content-type"].startswith("application/json")
