import sys, types
import os

try:
    import httpx  # type: ignore
except ModuleNotFoundError:  # fallback stub for offline envs
    httpx = types.ModuleType('httpx')
    sys.modules['httpx'] = httpx
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Patch httpx.Client to support the deprecated `app` parameter used by Starlette
if hasattr(httpx, "ASGITransport"):
    _orig_init = httpx.Client.__init__

    def _patched_init(self, *args, app=None, **kwargs):
        if app is not None:
            kwargs.setdefault("transport", httpx.ASGITransport(app=app))
        _orig_init(self, *args, **kwargs)

    httpx.Client.__init__ = _patched_init  # type: ignore

from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)

def test_login_route_redirect():
    response = client.get('/auth/login', allow_redirects=False)
    assert response.status_code in (302, 307)
