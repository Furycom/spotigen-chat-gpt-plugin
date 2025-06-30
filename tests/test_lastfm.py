import os
import sys
import importlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.lastfm import LastFMService


def test_lastfm_tags(monkeypatch):
    service = LastFMService()
    monkeypatch.setattr(service, "api_key", "x")
    
    class FakeResp:
        status_code = 200
        def json(self):
            return {"toptags": {"tag": [{"name": "rock"}, {"name": "pop"}]}}

    def fake_cached(params, ttl=21600):
        return FakeResp().json()

    monkeypatch.setattr(service, "_cached", fake_cached)
    tags = service.track_tags("artist", "title")
    assert tags == ["rock", "pop"]
