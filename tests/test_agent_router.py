import os, sys, types, importlib
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


def test_agent_pause(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "dummy")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    import src.agent as agent
    import src.index as src_index
    import api.index
    importlib.reload(agent)
    importlib.reload(src_index)
    importlib.reload(api.index)

    called = {}

    async def fake_pause(self, device_id=None):
        called['yes'] = True

    async def fake_acreate(**kwargs):
        class R:
            choices = [types.SimpleNamespace(message={"function_call": {"name": "pause", "arguments": "{}"}})]
        return R()

    monkeypatch.setattr(agent.SpotifyClient, "pause", fake_pause)
    monkeypatch.setattr(agent.openai.ChatCompletion, "acreate", fake_acreate)
    client = TestClient(api.index.app)
    r = client.post("/agent", json={"prompt": "mets Pause"}, headers={"Authorization": "Bearer x"})
    assert r.status_code == 200
    assert called.get('yes')
