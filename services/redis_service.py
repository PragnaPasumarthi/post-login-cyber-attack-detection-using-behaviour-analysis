import redis
import json
import time
from core.config import settings

class RedisService:
    def __init__(self):
        try:
            self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.client.ping() # Check if it's actually alive
            self.use_fake = False
            print("SUCCESS: Redis Connected Successfully.")
        except Exception:
            self.use_fake = True
            self.fake_db = {}
            print("WARNING: Redis not found. Using 'Fake Memory' (Internal Dictionary).")
            print("   (Data will be lost if you restart the server)")

        self.action_window_ttl = 3600 
        self.risk_decay_rate = 0.95 

    def store_action(self, user_id, action_details):
        if self.use_fake:
            key = f"actions:{user_id}"
            if key not in self.fake_db: self.fake_db[key] = []
            self.fake_db[key].append(json.dumps(action_details))
            if len(self.fake_db[key]) > 100: self.fake_db[key].pop(0)
            return

        key = f"actions:{user_id}"
        self.client.rpush(key, json.dumps(action_details))
        self.client.expire(key, self.action_window_ttl)
        self.client.ltrim(key, -100, -1)

    def get_user_history(self, user_id):
        if self.use_fake:
            key = f"actions:{user_id}"
            history = self.fake_db.get(key, [])
            return [json.loads(a) for a in history]

        key = f"actions:{user_id}"
        history = self.client.lrange(key, 0, -1)
        return [json.loads(a) for a in history]

    def update_risk_score(self, user_id, increment: float):
        key = f"risk:{user_id}"
        if self.use_fake:
            current = self.fake_db.get(key, 0.0)
            new_val = (float(current) * self.risk_decay_rate) + float(increment)
            self.fake_db[key] = new_val
            return round(new_val, 2)

        # Apply decay first
        current = self.client.get(key)
        if current:
            decayed_val = float(current) * self.risk_decay_rate
            self.client.set(key, decayed_val)
        
        # Use Redis atomic float increment
        new_val = self.client.incrbyfloat(key, float(increment))
        return round(float(new_val), 2)

    def get_risk_score(self, user_id):
        key = f"risk:{user_id}"
        if self.use_fake:
            return float(self.fake_db.get(key, 0.0))
        val = self.client.get(key)
        return float(val) if val else 0.0

    def set_val(self, key, value, ex=None):
        if self.use_fake:
            self.fake_db[key] = value
            return
        self.client.set(key, value, ex=ex)

    def get_val(self, key):
        if self.use_fake:
            return self.fake_db.get(key)
        return self.client.get(key)

    def delete_val(self, key):
        if self.use_fake:
            self.fake_db.pop(key, None)
            return
        self.client.delete(key)

    def clear_session(self, user_id):
        self.delete_val(f"actions:{user_id}")
        self.delete_val(f"risk:{user_id}")
        self.delete_val(f"session:{user_id}")
