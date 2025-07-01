import json

import httpx
from fastapi import HTTPException

from src.dtos.api import TrackTitles, TrackURIs


class InvalidAccessToken(Exception):
    pass


class SpotifyAPIError(Exception):
    pass


class SpotifyClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.spotify.com/v1"
        self._user_id = None

    def _auth_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def get_my_user_id(self):
        if self._user_id is not None:
            return self._user_id
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/me", headers=self._auth_headers()
            )
        if response.status_code != 200:
            raise HTTPException(
                status_code=401, detail="Invalid or missing access token"
            )
        user_data = response.json()
        self._user_id = user_data["id"]
        return self._user_id

    async def search_track(self, query: str, limit=10):
        params = {"q": query, "type": "track", "limit": limit}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search", headers=self._auth_headers(), params=params
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to search track. Error: {response.text}",
            )
        return response.json()["tracks"]["items"]

    async def get_user_playlists(self):
        playlists = []
        offset = 0
        limit = 50
        user_id = await self.get_my_user_id()
        url = f"{self.base_url}/users/{user_id}/playlists?limit={limit}&offset={offset}"
        content = {"next": url}
        while len(playlists) < 500 and content["next"]:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    content["next"], headers=self._auth_headers()
                )
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get user playlists. Error: {response.text}",
                )
            content = response.json()
            for playlist in response.json()["items"]:
                playlists.append(playlist)
        return playlists

    async def find_playlist(self, name: str) -> dict | None:
        playlists = await self.get_user_playlists()
        for playlist in playlists:
            if name.lower() in playlist["name"].lower():
                return playlist

        return None

    async def playlist_by_name(self, name: str) -> dict:
        """Return the user's playlist matching ``name`` exactly."""
        offset = 0
        limit = 50
        while True:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/me/playlists",
                    headers=self._auth_headers(),
                    params={"limit": limit, "offset": offset},
                )
            if resp.status_code == 404:
                raise HTTPException(404, "Playlist not found")
            if resp.status_code != 200:
                raise HTTPException(401, "Invalid or missing access token")
            data = resp.json()
            for pl in data.get("items", []):
                if pl.get("name", "").lower() == name.lower():
                    return pl
            if not data.get("next"):
                break
            offset += limit
        raise HTTPException(404, "Playlist not found")

    async def create_playlist(self, name: str, public: bool):
        data = {"name": name, "public": public}
        user_id = await self.get_my_user_id()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/users/{user_id}/playlists",
                headers=self._auth_headers(),
                json=data,
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create playlist. Error: {response.text}",
            )
        return response.json()["id"]

    async def _playlist_id(self, pid_or_name: str) -> str:
        """Return a valid Spotify playlist ID from either a name or ID.

        ``pid_or_name`` may already be a playlist ID. If it instead looks like a
        human readable name, the user's playlists are searched (up to two pages)
        for an exact case-insensitive match where the playlist owner is the
        current user.  If still unresolved, a single ``/search`` query is issued
        and the first result owned by the user is selected.  ``HTTPException``
        with ``404`` is raised if no match can be found.
        """

        # Spotify IDs are typically 22 alphanumeric characters.
        if len(pid_or_name) == 22 and pid_or_name.isalnum():
            return pid_or_name

        pl = await self.playlist_by_name(pid_or_name)
        return pl["id"]

    async def get_tracks_from_playlist(self, playlist_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/playlists/{playlist_id}/tracks",
                headers=self._auth_headers(),
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get tracks from playlist. Error: {response.text}",
            )

        tracks = []
        for track in response.json()["items"]:
            dct = {}
            dct["title"] = track["track"]["name"]
            dct["track_uri"] = track["track"]["uri"]
            dct["album_name"] = track["track"]["album"]["name"]
            dct["artists"] = track["track"]["artists"]
            dct["duration_ms"] = track["track"]["duration_ms"]
            dct["explicit"] = track["track"]["explicit"]
            tracks.append(dct)

        return {"tracks": tracks}

    async def add_tracks_to_playlist(self, playlist_id: str, track_titles: TrackTitles):
        tracks_uris = []
        for title in track_titles.titles:
            tracks = await self.search_track(title, limit=10)
            if len(tracks) > 0:
                tracks_uris.append(tracks[0]["uri"])
            else:
                print(f"No tracks found for {title}")
        data = {"uris": tracks_uris}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/playlists/{playlist_id}/tracks",
                headers=self._auth_headers(),
                json=data,
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to add tracks to playlist. Error: {response.text}",
            )

    async def remove_tracks_from_playlist(
        self, playlist_id: str, track_uris: TrackURIs
    ):
        data = {"tracks": [{"uri": uri} for uri in track_uris.track_uris]}
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/playlists/{playlist_id}/tracks",
                headers=self._auth_headers(),
                json=data,
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to remove tracks from playlist. Error: {response.text}",
            )

    async def recent(self, limit: int = 20):
        params = {"limit": limit}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/me/player/recently-played",
                headers=self._auth_headers(),
                params=params,
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json().get("items", [])

    async def currently_playing(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/me/player/currently-playing",
                headers=self._auth_headers(),
            )
        if response.status_code == 204:
            return None
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

    async def play(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/me/player/play",
                headers=self._auth_headers(),
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    async def pause(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/me/player/pause",
                headers=self._auth_headers(),
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    async def next(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/me/player/next",
                headers=self._auth_headers(),
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    async def previous(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/me/player/previous",
                headers=self._auth_headers(),
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    async def get_playlists(self, limit: int = 20, offset: int = 0):
        params = {"limit": limit, "offset": offset}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/me/playlists",
                headers=self._auth_headers(),
                params=params,
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json().get("items", [])

    async def get_library_tracks(self, limit: int = 50, offset: int = 0):
        params = {"limit": limit, "offset": offset}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/me/tracks",
                headers=self._auth_headers(),
                params=params,
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json().get("items", [])

    async def get_library_albums(self, limit: int = 50, offset: int = 0):
        params = {"limit": limit, "offset": offset}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/me/albums",
                headers=self._auth_headers(),
                params=params,
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json().get("items", [])

    async def get_followed_artists(self, limit: int = 50, after: str | None = None):
        params = {"type": "artist", "limit": limit}
        if after:
            params["after"] = after
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/me/following",
                headers=self._auth_headers(),
                params=params,
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json().get("artists", {}).get("items", [])

    async def follow_artist(self, artist_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/me/following",
                headers=self._auth_headers(),
                params={"type": "artist", "ids": artist_id},
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    async def unfollow_artist(self, artist_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/me/following",
                headers=self._auth_headers(),
                params={"type": "artist", "ids": artist_id},
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    async def search(self, q: str, type: str = "track,artist,album", limit: int = 10):
        params = {"q": q, "type": type, "limit": limit}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search",
                headers=self._auth_headers(),
                params=params,
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

    async def recommendations(
        self,
        seed_tracks: str = "",
        seed_artists: str = "",
        seed_genres: str = "",
        limit: int = 20,
    ):
        params = {
            "seed_tracks": seed_tracks,
            "seed_artists": seed_artists,
            "seed_genres": seed_genres,
            "limit": limit,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/recommendations",
                headers=self._auth_headers(),
                params=params,
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        tracks = response.json().get("tracks", [])

        # Filter out URIs already recommended for this user
        try:
            from src.storage import _redis

            user_id = await self.get_my_user_id()
            seen = set(_redis.smembers(f"recommended:{user_id}") or [])
            fresh = [t for t in tracks if t.get("uri") not in seen]
            if fresh:
                _redis.sadd(f"recommended:{user_id}", *[t.get("uri") for t in fresh])
            return fresh
        except Exception:
            return tracks

    async def get_profile(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/me", headers=self._auth_headers()
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
