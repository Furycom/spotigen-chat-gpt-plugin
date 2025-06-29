import os
import sys
import types

# Ensure repository root is in sys.path for test imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import httpx  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - allow running tests without httpx
    httpx = types.ModuleType("httpx")

    class BaseTransport:
        pass

    class ASGITransport(BaseTransport):
        def __init__(self, app=None, **kwargs):
            self.app = app

    class Request:
        def __init__(self, *args, **kwargs):
            pass

    class Response:
        def __init__(self, status_code=200, text="", headers=None):
            self.status_code = status_code
            self.text = text
            self.headers = headers or {}
        def json(self):
            return {}

    class Client:
        def __init__(self, *args, **kwargs):
            pass

    httpx.BaseTransport = BaseTransport
    httpx.ASGITransport = ASGITransport
    httpx.Request = Request
    httpx.Response = Response
    httpx.Client = Client
    sys.modules["httpx"] = httpx

if hasattr(httpx, "ASGITransport") and hasattr(httpx, "Client"):
    _orig_init = httpx.Client.__init__

    def _patched_init(self, *args, app=None, **kwargs):
        if app is not None:
            kwargs.setdefault("transport", httpx.ASGITransport(app=app))
        _orig_init(self, *args, **kwargs)

    httpx.Client.__init__ = _patched_init  # type: ignore
