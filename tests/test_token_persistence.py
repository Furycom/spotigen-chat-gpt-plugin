from src.storage import save_tokens, load_tokens

def test_token_persistence(tmp_path, monkeypatch):
    dummy = {"access_token": "X", "refresh_token": "Y", "expires_at": 123}
    # Upstash client uses env vars; patch Redis to use tmp file
    class FakeRedis:
        def __init__(self):
            self.store = {}
        def set(self, k, v):
            self.store[k] = v
        def get(self, k):
            return self.store.get(k)
    monkeypatch.setattr("src.storage._redis", FakeRedis())
    save_tokens(dummy)
    assert load_tokens() == dummy
