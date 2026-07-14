from .tz import (
    UTC,
    TzFile,
    TzIcal,
    TzLocal,
    TzOffset,
    TzRange,
    TzStr,
    TzUTC,
    datetime_ambiguous,
    datetime_exists,
    gettz,
    resolve_imaginary,
)
from .win import TzWin, TzWinLocal, tzwin, tzwinlocal

# fmt: off
__all__ = ["TzFile", "TzIcal", "TzLocal", "TzOffset", "TzRange", "TzStr", "TzUTC",
           "tzutc", "gettz", "enfold", "datetime_ambiguous", "datetime_exists",
           "resolve_imaginary", "UTC", "DeprecatedTzFormatWarning",
           "TzWin", "TzWinLocal"]
# fmt: on


class DeprecatedTzFormatWarning(Warning):
    """Warning raised when time zones are parsed from deprecated formats."""


# Alias
tzstr = TzStr
tzfile = TzFile
tzical = TzIcal
tzlocal = TzLocal
tzoffset = TzOffset
tzrange = TzRange
tzutc = TzUTC
