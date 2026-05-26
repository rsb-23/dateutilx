import sys

import pytest

MODULE_TYPE = type(sys)


# Tests live in datetutil/test which cause a RuntimeWarning for Python2 builds.
# But since we expect lazy imports tests to fail for Python < 3.7  we'll ignore those
# warnings with this filter.


def filter_import_warning(f):
    return f


@pytest.fixture(scope="function")
def clean_import():
    """Create a somewhat clean import base for lazy import tests"""
    du_modules = {mod_name: mod for mod_name, mod in sys.modules.items() if mod_name.startswith("dateutil")}

    other_modules = {mod_name for mod_name in sys.modules if mod_name not in du_modules}

    for mod_name in du_modules:
        del sys.modules[mod_name]

    yield

    # Delete anything that wasn't in the origin sys.modules list
    for mod_name in list(sys.modules):
        if mod_name not in other_modules:
            del sys.modules[mod_name]

    # Restore original modules
    for mod_name, mod in du_modules.items():
        sys.modules[mod_name] = mod


@filter_import_warning
@pytest.mark.parametrize("module", ["easter", "parser", "relativedelta", "rrule", "tz", "utils", "zoneinfo"])
def test_lazy_import(clean_import, module):
    """Test that dateutil.[submodule] works for py version > 3.7"""

    import importlib

    import dateutil

    if sys.version_info < (3, 7):
        pytest.xfail("Lazy loading does not work for Python < 3.7")

    mod_obj = getattr(dateutil, module, None)
    assert isinstance(mod_obj, MODULE_TYPE)

    mod_imported = importlib.import_module("dateutil.%s" % module)
    assert mod_obj is mod_imported


HOST_IS_WINDOWS = sys.platform.startswith("win")


def test_import_version_str():
    """Test that dateutil.__version__ can be imported"""


def test_import_version_root():
    import dateutil

    assert hasattr(dateutil, "__version__")


# Test that dateutil.easter-related imports work properly
def test_import_easter_direct():
    pass


def test_import_easter_from():
    pass


def test_import_easter_start():
    pass


#  Test that dateutil.parser-related imports work properly
def test_import_parser_direct():
    pass


def test_import_parser_from():
    pass


def test_import_parser_all():
    # All interface
    # Other public classes
    from dateutil.parser import parse, parser, parserinfo

    for var in (parse, parserinfo, parser):
        assert var is not None


# Test that dateutil.relativedelta-related imports work properly
def test_import_relative_delta_direct():
    pass


def test_import_relative_delta_from():
    pass


def test_import_relative_delta_all():
    from dateutil.relativedelta import FR, MO, SA, SU, TH, TU, WE, relativedelta

    for var in (relativedelta, MO, TU, WE, TH, FR, SA, SU):
        assert var is not None

    # In the public interface but not in all
    from dateutil.relativedelta import weekday

    assert weekday is not None


# Test that dateutil.rrule related imports work properly
def test_import_rrule_direct():
    pass


def test_import_rrule_from():
    pass


def test_import_rrule_all():
    # fmt: off
    from dateutil.rrule import (
        DAILY,
        FR,
        HOURLY,
        MINUTELY,
        MO,
        MONTHLY,
        SA,
        SECONDLY,
        SU,
        TH,
        TU,
        WE,
        WEEKLY,
        YEARLY,
        rrule,
        rruleset,
        rrulestr,
    )

    rr_all = (rrule, rruleset, rrulestr,
              YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY, MINUTELY, SECONDLY,
              MO, TU, WE, TH, FR, SA, SU)
    # fmt: on

    for var in rr_all:
        assert var is not None

    # In the public interface but not in all
    from dateutil.rrule import weekday

    assert weekday is not None


# Test that dateutil.tz related imports work properly
def test_import_tztest_direct():
    pass


def test_import_tz_from():
    pass


def test_import_tz_all():
    # fmt: off
    from dateutil.tz import (  # noqa: F401
        UTC,
        datetime_ambiguous,
        datetime_exists,
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

    tz_all = ["tzutc", "tzoffset", "tzlocal", "tzfile", "tzrange",
              "tzstr", "tzical", "gettz", "datetime_ambiguous",
              "datetime_exists", "resolve_imaginary", "UTC"]
    # fmt: on

    tz_all += ["tzwin", "tzwinlocal"] if sys.platform.startswith("win") else []
    lvars = locals()

    for var in tz_all:
        assert lvars[var] is not None


# Test that dateutil.tzwin related imports work properly
@pytest.mark.skipif(not HOST_IS_WINDOWS, reason="Requires Windows")
def test_import_tz_windows_direct():
    pass


@pytest.mark.skipif(not HOST_IS_WINDOWS, reason="Requires Windows")
def test_import_tz_windows_from():
    pass


@pytest.mark.skipif(not HOST_IS_WINDOWS, reason="Requires Windows")
def test_import_tz_windows_star():
    from dateutil.tzwin import tzwin, tzwinlocal

    tzwin_all = [tzwin, tzwinlocal]

    for var in tzwin_all:
        assert var is not None


# Test imports of Zone Info
def test_import_zone_info_direct():
    pass


def test_import_zone_info_from():
    pass


def test_import_zone_info_star():
    from dateutil.zoneinfo import gettz, gettz_db_metadata, rebuild

    zi_all = (gettz, gettz_db_metadata, rebuild)

    for var in zi_all:
        assert var is not None
