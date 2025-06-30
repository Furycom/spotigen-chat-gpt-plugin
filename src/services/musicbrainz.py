"""Minimal MusicBrainz helper to fetch original release year."""
from __future__ import annotations

import hashlib
import json
from typing import Optional

from src.storage import _redis
from src.utils.http import safe_get


class MusicBrainz:
    base = "https://musicbrainz.org/ws/2/"

    def _cache_key(self, artist: str, title: str) -> str:
        data = json.dumps({"a": artist, "t": title}, sort_keys=True)
        return "mb:recording:" + hashlib.sha1(data.encode()).hexdigest()

    def first_release_year(self, artist: str, title: str) -> Optional[int]:
        """Return the earliest release year for ``artist`` and ``title``."""
        key = self._cache_key(artist, title)
        cached = _redis.get(key)
        if cached:
            return int(cached)
        query = f'artist:"{artist}" AND recording:"{title}"'
        params = {"query": query, "fmt": "json", "inc": "releases", "limit": 1}
        resp = safe_get(self.base + "recording", params=params, headers={"User-Agent": "spotigen"})
        if resp.status_code != 200:
            return None
        data = resp.json()
        years = []
        for rec in data.get("recordings", []):
            for rel in rec.get("releases", []):
                date = rel.get("date")
                if date:
                    try:
                        years.append(int(date.split("-")[0]))
                    except ValueError:
                        pass
        year = min(years) if years else None
        if year is not None:
            try:
                _redis.set(key, str(year), ex=172800)
            except Exception:
                pass
        return year
