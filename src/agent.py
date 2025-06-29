from fastapi import APIRouter, Depends, HTTPException, Body
import json, os
import openai
from .services.spotify import SpotifyClient
from .utils import get_spotify_client

router = APIRouter()

functions = [
    {
        "name": "search",
        "description": "Search tracks on Spotify",
        "parameters": {
            "type": "object",
            "properties": {
                "q": {"type": "string"},
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["q"]
        },
    },
    {
        "name": "recommendations",
        "description": "Get track recommendations from seed tracks",
        "parameters": {
            "type": "object",
            "properties": {
                "seed_tracks": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 20}
            },
            "required": ["seed_tracks"]
        },
    },
    {
        "name": "audio_features",
        "description": "Get audio features for tracks",
        "parameters": {
            "type": "object",
            "properties": {
                "track_ids": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["track_ids"]
        },
    },
    {
        "name": "recent",
        "description": "Recently played tracks",
        "parameters": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 50}}
        },
    },
    {
        "name": "top_tracks",
        "description": "User top tracks",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 50},
                "time_range": {"type": "string", "default": "long_term"}
            }
        },
    },
    {
        "name": "top_artists",
        "description": "User top artists",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 50},
                "time_range": {"type": "string", "default": "long_term"}
            }
        },
    },
    {
        "name": "queue",
        "description": "Add track to playback queue",
        "parameters": {
            "type": "object",
            "properties": {"track_uri": {"type": "string"}},
            "required": ["track_uri"]
        },
    },
    {"name": "devices", "description": "List playback devices", "parameters": {"type": "object", "properties": {}}},
    {
        "name": "play",
        "description": "Start playback",
        "parameters": {
            "type": "object",
            "properties": {
                "track_uri": {"type": "string"},
                "device_id": {"type": "string"}
            }
        },
    },
    {
        "name": "pause",
        "description": "Pause playback",
        "parameters": {
            "type": "object",
            "properties": {"device_id": {"type": "string"}}
        },
    },
    {
        "name": "skip_next",
        "description": "Skip to next track",
        "parameters": {
            "type": "object",
            "properties": {"device_id": {"type": "string"}}
        },
    },
    {
        "name": "stats",
        "description": "User genres and average audio features",
        "parameters": {"type": "object", "properties": {}}
    },
]

_function_map = {
    "search": lambda c, **k: c.search_tracks(**k),
    "recommendations": lambda c, **k: c.get_recommendations(**k),
    "audio_features": lambda c, **k: c.audio_features(**k),
    "recent": lambda c, **k: c.recent_tracks(**k),
    "top_tracks": lambda c, **k: c.top_tracks(**k),
    "top_artists": lambda c, **k: c.top_artists(**k),
    "queue": lambda c, **k: c.queue(**k),
    "devices": lambda c, **k: c.devices(),
    "play": lambda c, **k: c.play(**k),
    "pause": lambda c, **k: c.pause(**k),
    "skip_next": lambda c, **k: c.skip_next(**k),
    "stats": lambda c, **k: c.stats(),
}


@router.post("/agent")
async def agent(prompt: str = Body(..., embed=True), spotify_client: SpotifyClient = Depends(get_spotify_client)):
    messages = [{"role": "user", "content": prompt}]
    for _ in range(3):
        resp = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo-0613",
            messages=messages,
            functions=functions,
        )
        msg = resp.choices[0].message
        if msg.get("function_call"):
            name = msg["function_call"]["name"]
            args = json.loads(msg["function_call"].get("arguments", "{}"))
            func = _function_map.get(name)
            if not func:
                raise HTTPException(400, f"Unknown function {name}")
            result = await func(spotify_client, **args)
            messages.append(msg)
            messages.append({"role": "function", "name": name, "content": json.dumps(result)})
        else:
            return {"response": msg.get("content")}
    return {"response": "Je ne peux pas"}
