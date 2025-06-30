import os, requests
class LastFMService:
    def __init__(self):
        self.api_key = os.getenv("LASTFM_API_KEY")
        self.user = os.getenv("LASTFM_USERNAME")
        self.base = "https://ws.audioscrobbler.com/2.0/"

    def recent_tracks(self, limit=50):
        if not self.api_key or not self.user:
            return []
        params = {
            "method": "user.getrecenttracks",
            "user": self.user,
            "api_key": self.api_key,
            "format": "json",
            "limit": limit,
        }
        return requests.get(self.base, params=params, timeout=10).json()
