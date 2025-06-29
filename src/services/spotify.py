import json
import httpx
from src.dtos.api import TrackTitles, TrackURIs
from fastapi import HTTPException

class InvalidAccessToken(Exception):
    pass

class SpotifyAPIError(Exception):
    pass

class SpotifyClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://api.spotify.com/v1'
        self._user_id = None

    def _auth_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }


    async def get_my_user_id(self):
        if self._user_id is not None:
            return self._user_id
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{self.base_url}/me', headers=self._auth_headers())
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid or missing access token")
        user_data = response.json()
        self._user_id = user_data["id"]
        return self._user_id
    
    async def search_track(self, query: str, limit=10):
        params = {
            'q': query,
            'type': 'track',
            'limit': limit
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{self.base_url}/search', headers=self._auth_headers(), params=params)
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to search track. Error: {response.text}")
        return response.json()['tracks']['items']

    async def get_user_playlists(self):
        playlists = []
        offset = 0
        limit = 50
        user_id = await self.get_my_user_id()
        url = f'{self.base_url}/users/{user_id}/playlists?limit={limit}&offset={offset}'
        content = {"next": url}
        while len(playlists) < 500 and content['next']:
            async with httpx.AsyncClient() as client:
                response = await client.get(content['next'], headers=self._auth_headers())
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=f"Failed to get user playlists. Error: {response.text}")
            content = response.json()
            for playlist in response.json()['items']:
                playlists.append(playlist)
        return playlists

    async def find_playlist(self, name: str):
        playlists = await self.get_user_playlists()
        for playlist in playlists:
            if playlist['name'] == name:
                return playlist

        return None

    async def create_playlist(self, name: str, public: bool):
        data = {
            'name': name,
            'public': public
        }
        user_id = await self.get_my_user_id()
        async with httpx.AsyncClient() as client:
            response = await client.post(f'{self.base_url}/users/{user_id}/playlists', headers=self._auth_headers(), json=data)
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to create playlist. Error: {response.text}")
        return response.json()['id']

    async def get_tracks_from_playlist(self, playlist_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{self.base_url}/playlists/{playlist_id}/tracks', headers=self._auth_headers())
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to get tracks from playlist. Error: {response.text}")

        tracks = []
        for track in response.json()['items']:
            dct = {}
            dct['title'] = track['track']['name']
            dct['track_uri'] = track['track']['uri']
            dct['album_name'] = track['track']['album']['name']
            dct['artists'] = track['track']['artists']
            dct['duration_ms'] = track['track']['duration_ms']
            dct['explicit'] = track['track']['explicit']
            tracks.append(dct)

        return {"tracks": tracks}

    async def add_tracks_to_playlist(self, playlist_id: str, track_titles: TrackTitles):
        tracks_uris = []
        for title in track_titles.titles:
            tracks = await self.search_track(title, limit=10)
            if len(tracks) > 0:
                tracks_uris.append(tracks[0]['uri'])
            else:
                print(f'No tracks found for {title}')
        data = {
            'uris': tracks_uris
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(f'{self.base_url}/playlists/{playlist_id}/tracks', headers=self._auth_headers(), json=data)
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to add tracks to playlist. Error: {response.text}")

    async def remove_tracks_from_playlist(self, playlist_id: str, track_uris: TrackURIs):
        data = {
            'tracks': [{'uri': uri} for uri in track_uris.track_uris]
        }
        async with httpx.AsyncClient() as client:
            response = await client.delete(f'{self.base_url}/playlists/{playlist_id}/tracks', headers=self._auth_headers(), json=data)
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to remove tracks from playlist. Error: {response.text}")
