import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.musicbrainz import MusicBrainz


def test_musicbrainz_year(monkeypatch):
    mb = MusicBrainz()
    monkeypatch.setattr("src.services.musicbrainz._redis", type("R", (), {"get": lambda s,k: None, "set": lambda *a, **kw: None})())
    class FakeResp:
        status_code = 200
        def json(self):
            return {"recordings": [{"releases": [{"date": "1984-01-01"}]}]}
    def fake_safe_get(url, params=None, headers=None):
        return FakeResp()
    monkeypatch.setattr("src.services.musicbrainz.safe_get", fake_safe_get)
    year = mb.first_release_year("a", "t")
    assert year == 1984
