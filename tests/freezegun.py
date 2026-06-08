import datetime as dt
import functools
import types
from datetime import datetime
from functools import lru_cache
from importlib import import_module
from unittest.mock import patch


@lru_cache(5)
def _is_dt_module(target: str) -> bool:
    module, attr = target.rsplit(".", 1)
    mod = import_module(module)
    obj = getattr(mod, attr)
    return isinstance(obj, types.ModuleType) and obj is dt


class _DatetimeMeta(type):
    def __instancecheck__(cls, instance):
        return type.__instancecheck__(cls, instance) or isinstance(instance, dt.datetime)


class _FakeDatetime(datetime, metaclass=_DatetimeMeta):
    frozen_: datetime = datetime(1900, 1, 1)

    @classmethod
    def now(cls, tz=None):
        if tz is not None:
            return cls.frozen_.astimezone(tz)
        return cls.frozen_

    def __hash__(self):
        return dt.datetime.__hash__(self)


class _FakeDatetimeModule:
    """Wraps the real datetime module, overriding datetime.now()."""

    class datetime(_FakeDatetime):  # noqa
        pass

    def __getattr__(self, name):
        return getattr(dt, name)


def freeze_time(frozen_dt: datetime, module, *, tz_offset=0):
    to_patch = f"{module}.datetime"
    if tz_offset:
        offset = dt.timezone(dt.timedelta(hours=-tz_offset))
        frozen_dt = frozen_dt.replace(tzinfo=offset).astimezone()

    def decorator(fn):
        if _is_dt_module(to_patch):

            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                _FakeDatetime.frozen_ = frozen_dt
                fake_module = _FakeDatetimeModule()
                fake_module.datetime.frozen_ = frozen_dt
                with patch(to_patch, fake_module):
                    return fn(*args, **kwargs)

        else:

            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                _FakeDatetime.frozen_ = frozen_dt
                with patch(to_patch, _FakeDatetime):
                    return fn(*args, **kwargs)

        return wrapper

    return decorator
