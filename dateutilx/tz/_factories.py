import weakref
from collections import OrderedDict
from datetime import timedelta


class _TzSingleton(type):
    def __init__(cls, *args, **kwargs):
        cls.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(cls):
        if cls.__instance is None:
            cls.__instance = super().__call__()
        return cls.__instance


class _TzFactory(type):
    def instance(cls, *args, **kwargs):
        """Alternate constructor that returns a fresh instance"""
        return type.__call__(cls, *args, **kwargs)


class _TzCachedFactory(_TzFactory):
    """Factory with a weak identity cache plus a small strong LRU cache
    to keep the most recently used instances alive."""

    _strong_cache_size = 8

    def __init__(cls, *args, **kwargs):
        cls._instances = weakref.WeakValueDictionary()
        cls._strong_cache = OrderedDict()
        super().__init__(*args, **kwargs)

    def _cache_key(cls, *args, **kwargs):
        """Subclasses define how constructor args map to a cache key."""
        raise NotImplementedError

    def __call__(cls, *args, **kwargs):
        key = cls._cache_key(*args, **kwargs)

        instance = cls._instances.get(key)
        if instance is None:
            instance = cls._instances.setdefault(key, cls.instance(*args, **kwargs))

        cls._strong_cache[key] = cls._strong_cache.pop(key, instance)
        if len(cls._strong_cache) > cls._strong_cache_size:
            cls._strong_cache.popitem(last=False)

        return instance


class _TzOffsetFactory(_TzCachedFactory):
    def _cache_key(cls, name, offset):
        if isinstance(offset, timedelta):
            offset = offset.total_seconds()
        return name, offset


class _TzStrFactory(_TzCachedFactory):
    def _cache_key(cls, s, posix_offset=False):
        return s, posix_offset
