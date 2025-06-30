"""Thin wrapper around the Last.fm API."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, List, Dict

from src.storage import _redis
from src.utils.http import safe_get
class LastFMService:
    def __init__(self):
        self.api_key = os.getenv("LASTFM_API_KEY")
        self.user = os.getenv("LASTFM_USERNAME")
        self.base = "https://ws.audioscrobbler.com/2.0/"

    def recent_tracks(self, limit: int = 50) -> Dict[str, Any]:
        if not self.api_key or not self.user:
            return {}
        params = {
            "method": "user.getrecenttracks",
            "user": self.user,
            "api_key": self.api_key,
            "format": "json",
            "limit": limit,
        }
        return self._cached(params)

    # ------------------------------------------------------------------
    def _cached(self, params: Dict[str, Any], ttl: int = 21600) -> Dict[str, Any]:
        """Return cached JSON response for the given parameters."""
        key = "lastfm:raw:" + hashlib.sha1(json.dumps(params, sort_keys=True).encode()).hexdigest()
        cached = _redis.get(key)
        if cached:
            return json.loads(cached)
        resp = safe_get(self.base, params=params)
        data = resp.json()
        try:
            _redis.set(key, json.dumps(data), ex=ttl)
        except Exception:
            pass
        return data

    def track_tags(self, artist: str, title: str, limit: int = 5) -> List[str]:
        """Return top tags for a track using ``track.getTopTags``."""
        if not self.api_key:
            return []
        params = {
            "method": "track.getTopTags",
            "artist": artist,
            "track": title,
            "api_key": self.api_key,
            "format": "json",
        }
        data = self._cached(params)
        tags = data.get("toptags", {}).get("tag", [])
        return [t.get("name") for t in tags[:limit] if isinstance(t, dict)]

    def scrobble_history(self, from_ts: int, to_ts: int) -> List[Dict[str, Any]]:
        """Return listening history between two timestamps."""
        if not self.api_key or not self.user:
            return []
        params = {
            "method": "user.getrecenttracks",
            "user": self.user,
            "api_key": self.api_key,
            "format": "json",
            "from": int(from_ts),
            "to": int(to_ts),
            "limit": 200,
        }
        data = self._cached(params)
        return data.get("recenttracks", {}).get("track", [])
