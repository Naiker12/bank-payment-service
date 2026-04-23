import redis
import os
import json

# Configuración desde variables de entorno
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

class RedisStateManager:
    def __init__(self):
        self.client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )

    def set_payment_status(self, trace_id, status, error=None):
        key = f"payment:{trace_id}"
        data = {"traceId": trace_id, "status": status}
        if error: data["error"] = error
        self.client.set(key, json.dumps(data), ex=3600)

    def get_payment_status(self, trace_id):
        key = f"payment:{trace_id}"
        data = self.client.get(key)
        return json.loads(data) if data else None

redis_manager = RedisStateManager()
