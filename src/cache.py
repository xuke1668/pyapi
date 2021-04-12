# coding: utf-8
"""
缓存插件
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import json
from time import time

from cachelib import SimpleCache

try:
    import redis
except ImportError:
    raise RuntimeError('Redis module not found')


def dump_object(value):
    return json.dumps(value)


def load_object(value):
    if value is None:
        return None
    try:
        return json.loads(value)
    except TypeError:
        return None


class MemCache(SimpleCache):
    """内存缓存"""
    def __init__(self, app=None, key_prefix='', key_timeout=None, threshold=500):
        super().__init__(threshold)
        self.key_prefix = ''
        self.key_timeout = 0
        self.app = app
        if app is not None:
            self.init_app(app, key_prefix, key_timeout, threshold)

    def init_app(self, app, key_prefix='', key_timeout=None, threshold=5000):
        self._threshold = threshold
        self.key_prefix = key_prefix if key_prefix else app.config.get("MEM_CACHE_KEY_PREFIX", self.key_prefix)
        self.key_timeout = key_timeout if key_timeout else app.config.get("MEM_CACHE_KEY_TIMEOUT", self.key_timeout)

    def _normalize_timeout(self, timeout):
        if timeout is None:
            timeout = self.key_timeout
        elif timeout <= 0:
            timeout = 0
        else:
            timeout = time() + timeout
        return timeout

    def _key(self, key, key_prefix=True):
        if self.key_prefix and key_prefix:
            return self.key_prefix + key
        return key

    def get(self, key, key_prefix=True):
        data = self._cache.get(self._key(key, key_prefix))
        if not data:
            return None
        expires, value = data
        if expires == 0 or expires > time():
            return load_object(value)
        return None

    def set(self, key, value, key_prefix=True, timeout=None):
        self._prune()
        self._cache[self._key(key, key_prefix)] = (self._normalize_timeout(timeout), dump_object(value))
        return True

    def add(self, key, value, key_prefix=True, timeout=None):
        self._prune()
        if key in self._cache:
            return False
        item = (self._normalize_timeout(timeout), dump_object(value))
        self._cache.setdefault(self._key(key, key_prefix), item)
        return True

    def delete(self, key, key_prefix=True):
        return self._cache.pop(self._key(key, key_prefix), None) is not None

    def has(self, key, key_prefix=True):
        data = self._cache.get(self._key(key, key_prefix))
        if not data:
            return False
        expires, value = data
        return expires == 0 or expires > time()


class RedisCache(object):
    """redis缓存"""
    def __init__(self, app=None, redis_uri='', key_prefix='', key_timeout=None, **kwargs):
        self.redis_uri = 'redis://localhost:6379/0'
        self._client = None
        self.key_prefix = ''
        self.key_timeout = -1
        self.app = app
        if app is not None:
            self.init_app(app, redis_uri, key_prefix, key_timeout, **kwargs)

    def init_app(self, app, redis_uri='', key_prefix='', key_timeout=None, **kwargs):
        self.redis_uri = redis_uri if redis_uri else app.config.get("REDIS_URI", self.redis_uri)
        self.key_prefix = key_prefix if key_prefix else app.config.get("REDIS_KEY_PREFIX", self.key_prefix)
        self.key_timeout = key_timeout if key_timeout else app.config.get("REDIS_KEY_TIMEOUT", self.key_timeout)
        self._client = redis.StrictRedis.from_url(self.redis_uri, **kwargs)

    def _normalize_timeout(self, timeout):
        if timeout is None:
            timeout = self.key_timeout
        elif timeout == 0:
            timeout = -1
        return timeout

    def _key(self, key, key_prefix=True):
        if self.key_prefix and key_prefix:
            return self.key_prefix + key
        return key

    def get(self, key, key_prefix=True):
        return load_object(self._client.get(self._key(key, key_prefix)))

    def get_many(self, *keys, key_prefix=True):
        keys = [self._key(key, key_prefix) for key in keys]
        return [load_object(x) for x in self._client.mget(keys)]

    def get_dict(self, *keys, key_prefix=True):
        keys = [self._key(key, key_prefix) for key in keys]
        return dict(zip(keys, self.get_many(*keys)))

    def set(self, key, value, timeout=None, key_prefix=True):
        key = self._key(key, key_prefix)
        timeout = self._normalize_timeout(timeout)
        value = dump_object(value)
        if timeout == -1:
            result = self._client.set(name=key, value=value)
        else:
            result = self._client.setex(name=key, value=value, time=timeout)
        return result

    def add(self, key, value, timeout=None, key_prefix=True):
        key = self._key(key, key_prefix)
        timeout = self._normalize_timeout(timeout)
        value = dump_object(value)
        return (
            self._client.setnx(name=key, value=value) and
            self._client.expire(name=key, time=timeout)
        )

    def set_many(self, mapping, timeout=None, transaction=False, key_prefix=True):
        timeout = self._normalize_timeout(timeout)
        pipe = self._client.pipeline(transaction=transaction)
        for key, value in mapping:
            key = self._key(key, key_prefix)
            value = dump_object(value)
            if timeout == -1:
                pipe.set(name=key, value=value)
            else:
                pipe.setex(name=key, value=value, time=timeout)
        return pipe.execute()

    def delete(self, key, key_prefix=True):
        return self._client.delete(self._key(key, key_prefix))

    def delete_many(self, *keys, key_prefix=True):
        if not keys:
            return
        keys = [self._key(key, key_prefix) for key in keys]
        return self._client.delete(*keys)

    def has(self, key, key_prefix=True):
        return self._client.exists(self._key(key, key_prefix))

    def clear(self, key_prefix=True):
        status = False
        if self.key_prefix and key_prefix:
            keys = self._client.keys(self.key_prefix + '*')
            if keys:
                status = self._client.delete(*keys)
        else:
            status = self._client.flushdb()
        return status

    def inc(self, key, delta=1, key_prefix=True):
        return self._client.incr(self._key(key, key_prefix), delta)

    def dec(self, key, delta=1, key_prefix=True):
        return self._client.decr(self._key(key, key_prefix), delta)

    def zcard(self, key, key_prefix=True):
        return self._client.zcard(self._key(key, key_prefix))

    def zadd(self, key, key_prefix=True, **kwargs):
        return self._client.zadd(self._key(key, key_prefix), **kwargs)

    def zrem(self, key, *name, key_prefix=True,):
        return self._client.zrem(self._key(key, key_prefix), *name)

    def zincrby(self, key, name, amount=1, key_prefix=True):
        return self._client.zincrby(self._key(key, key_prefix), name, amount)

    def zrank(self, key, name, desc=False, key_prefix=True):
        key = self._key(key, key_prefix)
        if desc:
            return self._client.zrevrank(key, name)
        return self._client.zrank(key, name)

    def zscore(self, key, name, key_prefix=True):
        return self._client.zscore(self._key(key, key_prefix), name)

    def zrange(self, key, start, end, key_prefix=True, desc=False, withscores=False, score_cast_func=float):
        return self._client.zrange(self._key(key, key_prefix), start, end, desc, withscores, score_cast_func)

    def zrangebyscore(self, key, min_score, max_score, start=None, num=None, key_prefix=True, withscores=False, score_cast_func=float):
        return self._client.zrangebyscore(self._key(key, key_prefix), min_score, max_score, start, num, withscores, score_cast_func)
