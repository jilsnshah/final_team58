import json

import redis

r = redis.Redis(host="redis", port=6379, decode_responses=True)


def cache_get(key):
    data = r.get(key)
    return json.loads(data) if data else None


def cache_set(key, value):
    r.set(key, json.dumps(value), ex=300)
