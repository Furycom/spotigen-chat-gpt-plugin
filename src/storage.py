import os, json
try:
    from upstash_redis import Redis
except ModuleNotFoundError:  # pragma: no cover - fallback for tests
    class _Dummy:
        def __init__(self):
            self.store = {}
        def set(self, k, v):
            self.store[k] = v
        def get(self, k):
            return self.store.get(k)
    def Redis(url=None, token=None):
        return _Dummy()

_redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

KEY = "spotify_tokens"


def save_tokens(tokens: dict):
    _redis.set(KEY, json.dumps(tokens))


def load_tokens() -> dict | None:
    val = _redis.get(KEY)
    return json.loads(val) if val else None

