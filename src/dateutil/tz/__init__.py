# -*- coding: utf-8 -*-
from .tz import (
    UTC,
    datetime_ambiguous,
    datetime_exists,
    enfold,
    gettz,
    resolve_imaginary,
    tzfile,
    tzical,
    tzlocal,
    tzoffset,
    tzrange,
    tzstr,
    tzutc,
    tzwin,
    tzwinlocal,
)

# fmt: off
__all__ = ["tzutc", "tzoffset", "tzlocal", "tzfile", "tzrange",
           "tzstr", "tzical", "tzwin", "tzwinlocal", "gettz",
           "enfold", "datetime_ambiguous", "datetime_exists",
           "resolve_imaginary", "UTC", "DeprecatedTzFormatWarning"]

# fmt: on


class DeprecatedTzFormatWarning(Warning):
    """Warning raised when time zones are parsed from deprecated formats."""
