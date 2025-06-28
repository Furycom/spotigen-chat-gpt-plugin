import sys, types

try:
    import httpx  # type: ignore
except ModuleNotFoundError:  # fallback stub for offline envs
    httpx = types.ModuleType('httpx')
    sys.modules['httpx'] = httpx
import pytest
from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)

def test_login_route_redirect():
    response = client.get('/auth/login', allow_redirects=False)
    assert response.status_code in (302, 307)
