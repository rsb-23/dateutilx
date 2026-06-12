import base64
import contextlib
import copy
import gc
import os
import unittest
import weakref
from datetime import datetime, time, timedelta, tzinfo
from functools import partial
from io import BytesIO, StringIO

import pytest

from dateutilx import tz, zoneinfo
from dateutilx.helper import is_windows_os
from dateutilx.parser import parse
from dateutilx.relativedelta import SU, TH, RelativeDelta

from ._common import COMPARES_EQUAL, PicklableMixin, TZEnvContext
from ._data import (
    EUROPE_HELSINKI,
    NEW_YORK,
    TZ_AEST,
    TZ_EST,
    TZ_LON,
    TZ_PST,
    TZFILE_EST5EDT,
    TZICAL_EST5EDT,
    TZICAL_PST8PDT,
)

relativedelta = RelativeDelta

IS_WIN = is_windows_os()

MISSING_TARBALL = "This test fails if you don't have the dateutil timezone file installed. Please read the README"

UTC = tz.UTC
EST_TUPLE = ("EST", timedelta(hours=-5), timedelta(hours=0))
EDT_TUPLE = ("EDT", timedelta(hours=-4), timedelta(hours=1))


# Helper functions
mark_tzlocal_nix = pytest.mark.skipif(IS_WIN, reason="requires Unix")(pytest.mark.tzlocal)


def get_timezone_tuple(dt):
    """Retrieve a (tzname, utcoffset, dst) tuple for a given DST"""
    return dt.tzname(), dt.utcoffset(), dt.dst()


class TzFoldMixin:
    """Mix-in class for testing ambiguous times"""

    def gettz(self, tzname):
        raise NotImplementedError

    def _get_tzname(self, tzname):
        return tzname

    def _gettz_context(self, tzname):
        return contextlib.nullcontext()

    def test_fold_positive_utc_offset(self):
        # Test that we can resolve ambiguous times
        tzname = self._get_tzname("Australia/Sydney")

        with self._gettz_context(tzname):
            SYD = self.gettz(tzname)

            t0_u = datetime(2012, 3, 31, 15, 30, tzinfo=tz.UTC)  # AEST
            t1_u = datetime(2012, 3, 31, 16, 30, tzinfo=tz.UTC)  # AEDT

            t0_syd0 = t0_u.astimezone(SYD)
            t1_syd1 = t1_u.astimezone(SYD)

            self.assertEqual(t0_syd0.replace(tzinfo=None), datetime(2012, 4, 1, 2, 30))

            self.assertEqual(t1_syd1.replace(tzinfo=None), datetime(2012, 4, 1, 2, 30))

            self.assertEqual(t0_syd0.utcoffset(), timedelta(hours=11))
            self.assertEqual(t1_syd1.utcoffset(), timedelta(hours=10))

    def test_gap_positive_utc_offset(self):
        # Test that we don't have a problem around gaps.
        tzname = self._get_tzname("Australia/Sydney")

        with self._gettz_context(tzname):
            SYD = self.gettz(tzname)

            t0_u = datetime(2012, 10, 6, 15, 30, tzinfo=tz.UTC)  # AEST
            t1_u = datetime(2012, 10, 6, 16, 30, tzinfo=tz.UTC)  # AEDT

            t0 = t0_u.astimezone(SYD)
            t1 = t1_u.astimezone(SYD)

            self.assertEqual(t0.replace(tzinfo=None), datetime(2012, 10, 7, 1, 30))

            self.assertEqual(t1.replace(tzinfo=None), datetime(2012, 10, 7, 3, 30))

            self.assertEqual(t0.utcoffset(), timedelta(hours=10))
            self.assertEqual(t1.utcoffset(), timedelta(hours=11))

    def test_fold_negative_utc_offset(self):
        # Test that we can resolve ambiguous times
        tzname = self._get_tzname("America/Toronto")

        with self._gettz_context(tzname):
            TOR = self.gettz(tzname)

            t0_u = datetime(2011, 11, 6, 5, 30, tzinfo=tz.UTC)
            t1_u = datetime(2011, 11, 6, 6, 30, tzinfo=tz.UTC)

            t0_tor = t0_u.astimezone(TOR)
            t1_tor = t1_u.astimezone(TOR)

            self.assertEqual(t0_tor.replace(tzinfo=None), datetime(2011, 11, 6, 1, 30))

            self.assertEqual(t1_tor.replace(tzinfo=None), datetime(2011, 11, 6, 1, 30))

            self.assertNotEqual(t0_tor.tzname(), t1_tor.tzname())
            self.assertEqual(t0_tor.utcoffset(), timedelta(hours=-4.0))
            self.assertEqual(t1_tor.utcoffset(), timedelta(hours=-5.0))

    def test_gap_negative_utc_offset(self):
        # Test that we don't have a problem around gaps.
        tzname = self._get_tzname("America/Toronto")

        with self._gettz_context(tzname):
            TOR = self.gettz(tzname)

            t0_u = datetime(2011, 3, 13, 6, 30, tzinfo=tz.UTC)
            t1_u = datetime(2011, 3, 13, 7, 30, tzinfo=tz.UTC)

            t0 = t0_u.astimezone(TOR)
            t1 = t1_u.astimezone(TOR)

            self.assertEqual(t0.replace(tzinfo=None), datetime(2011, 3, 13, 1, 30))

            self.assertEqual(t1.replace(tzinfo=None), datetime(2011, 3, 13, 3, 30))

            self.assertNotEqual(t0, t1)
            self.assertEqual(t0.utcoffset(), timedelta(hours=-5.0))
            self.assertEqual(t1.utcoffset(), timedelta(hours=-4.0))

    def test_fold_london(self):
        tzname = self._get_tzname("Europe/London")

        with self._gettz_context(tzname):
            LON = self.gettz(tzname)

            t0_u = datetime(2013, 10, 27, 0, 30, tzinfo=UTC)  # BST
            t1_u = datetime(2013, 10, 27, 1, 30, tzinfo=UTC)  # GMT

            t0 = t0_u.astimezone(LON)
            t1 = t1_u.astimezone(LON)

            self.assertEqual(t0.replace(tzinfo=None), datetime(2013, 10, 27, 1, 30))

            self.assertEqual(t1.replace(tzinfo=None), datetime(2013, 10, 27, 1, 30))

            self.assertEqual(t0.utcoffset(), timedelta(hours=1))
            self.assertEqual(t1.utcoffset(), timedelta(hours=0))

    def test_fold_independence(self):
        tzname = self._get_tzname("America/New_York")

        with self._gettz_context(tzname):
            NYC = self.gettz(tzname)

            hour = timedelta(hours=1)

            # Firmly 2015-11-01 0:30 EDT-4
            pre_dst = datetime(2015, 11, 1, 0, 30, tzinfo=NYC)

            # Ambiguous between 2015-11-01 1:30 EDT-4 and 2015-11-01 1:30 EST-5
            in_dst = pre_dst + hour
            in_dst_tzname_0 = in_dst.tzname()  # Stash the tzname - EDT

            # Doing the arithmetic in UTC creates a date that is unambiguously
            # 2015-11-01 1:30 EDT-5
            in_dst_via_utc = (pre_dst.astimezone(UTC) + 2 * hour).astimezone(NYC)

            # Make sure the dates are actually ambiguous
            self.assertEqual(in_dst, in_dst_via_utc)

            # Make sure we got the right folding behavior
            self.assertNotEqual(in_dst_via_utc.tzname(), in_dst_tzname_0)

            # Now check to make sure in_dst's tzname hasn't changed
            self.assertEqual(in_dst_tzname_0, in_dst.tzname())

    def test_in_zone_fold_equality(self):
        # Two datetimes in the same zone are considered to be equal if their
        # wall times are equal, even if they have different absolute times.

        tzname = self._get_tzname("America/New_York")

        with self._gettz_context(tzname):
            NYC = self.gettz(tzname)

            dt0 = datetime(2011, 11, 6, 1, 30, tzinfo=NYC)
            dt1 = tz.enfold(dt0, fold=1)

            # Make sure these actually represent different times
            self.assertNotEqual(dt0.astimezone(UTC), dt1.astimezone(UTC))

            # Test that they compare equal
            self.assertEqual(dt0, dt1)

    def _test_ambiguous_time(self, dt, tzid, ambiguous):
        # This is a test to check that the individual is_ambiguous values
        # on the _tzinfo subclasses work.
        tzname = self._get_tzname(tzid)

        with self._gettz_context(tzname):
            tzi = self.gettz(tzname)

            self.assertEqual(tz.datetime_ambiguous(dt, tz=tzi), ambiguous)

    def test_ambiguous_negative_utc_offset(self):
        self._test_ambiguous_time(datetime(2015, 11, 1, 1, 30), "America/New_York", True)

    def test_ambiguous_positive_utc_offset(self):
        self._test_ambiguous_time(datetime(2012, 4, 1, 2, 30), "Australia/Sydney", True)

    def test_unambiguous_negative_utc_offset(self):
        self._test_ambiguous_time(datetime(2015, 11, 1, 2, 30), "America/New_York", False)

    def test_unambiguous_positive_utc_offset(self):
        self._test_ambiguous_time(datetime(2012, 4, 1, 3, 30), "Australia/Sydney", False)

    def test_unambiguous_gap_negative_utc_offset(self):
        # Imaginary time
        self._test_ambiguous_time(datetime(2011, 3, 13, 2, 30), "America/New_York", False)

    def test_unambiguous_gap_positive_utc_offset(self):
        # Imaginary time
        self._test_ambiguous_time(datetime(2012, 10, 7, 2, 30), "Australia/Sydney", False)

    def _test_imaginary_time(self, dt, tzid, exists):
        tzname = self._get_tzname(tzid)
        with self._gettz_context(tzname):
            tzi = self.gettz(tzname)

            self.assertEqual(tz.datetime_exists(dt, tz=tzi), exists)

    def test_imaginary_negative_utc_offset(self):
        self._test_imaginary_time(datetime(2011, 3, 13, 2, 30), "America/New_York", False)

    def test_not_imaginary_negative_utc_offset(self):
        self._test_imaginary_time(datetime(2011, 3, 13, 1, 30), "America/New_York", True)

    def test_imaginary_positive_utc_offset(self):
        self._test_imaginary_time(datetime(2012, 10, 7, 2, 30), "Australia/Sydney", False)

    def test_not_imaginary_positive_utc_offset(self):
        self._test_imaginary_time(datetime(2012, 10, 7, 1, 30), "Australia/Sydney", True)

    def test_not_imaginary_fold_negative_utc_offset(self):
        self._test_imaginary_time(datetime(2015, 11, 1, 1, 30), "America/New_York", True)

    def test_not_imaginary_fold_positive_utc_offset(self):
        self._test_imaginary_time(datetime(2012, 4, 1, 3, 30), "Australia/Sydney", True)

    def test_equal_ambiguous_comparison(self):
        tzname = self._get_tzname("Australia/Sydney")

        with self._gettz_context(tzname):
            SYD0 = self.gettz(tzname)
            SYD1 = self.gettz(tzname)

            t0_u = datetime(2012, 3, 31, 14, 30, tzinfo=tz.UTC)  # AEST

            t0_syd0 = t0_u.astimezone(SYD0)
            t0_syd1 = t0_u.astimezone(SYD1)

            # This is considered an "inter-zone comparison" because it's an
            # ambiguous datetime.
            self.assertEqual(t0_syd0, t0_syd1)


###
# Test Cases
class TzUTCTest(unittest.TestCase):
    def test_offset(self):
        ct = datetime(2009, 4, 1, 12, 11, 13, tzinfo=tz.tzutc())

        self.assertEqual(ct.utcoffset(), timedelta(seconds=0))

    def test_dst(self):
        ct = datetime(2009, 4, 1, 12, 11, 13, tzinfo=tz.tzutc())

        self.assertEqual(ct.dst(), timedelta(seconds=0))

    def test_tz_name(self):
        ct = datetime(2009, 4, 1, 12, 11, 13, tzinfo=tz.tzutc())
        self.assertEqual(ct.tzname(), "UTC")

    def test_equality(self):
        UTC0 = tz.tzutc()
        UTC1 = tz.tzutc()

        self.assertIs(UTC0, UTC1)
        self.assertEqual(UTC0, UTC1)

    def test_inequality(self):
        UTC = tz.tzutc()
        UTCp4 = tz.tzoffset("UTC+4", 14400)

        self.assertNotEqual(UTC, UTCp4)

    def test_inequality_integer(self):
        self.assertFalse(tz.tzutc() == 7)
        self.assertNotEqual(tz.tzutc(), 7)

    def test_inequality_unsupported(self):
        self.assertEqual(tz.tzutc(), COMPARES_EQUAL)

    def test_repr(self):
        self.assertEqual(repr(tz.tzutc()), "tzutc()")

    def test_time_only_utc(self):
        # https://github.com/dateutil/dateutil/issues/132
        # tzutc doesn't care
        tz_utc = tz.tzutc()
        self.assertEqual(time(13, 20, tzinfo=tz_utc).utcoffset(), timedelta(0))

    def test_ambiguity(self):
        # Pick an arbitrary datetime, this should always return False.
        dt = datetime(2011, 9, 1, 2, 30, tzinfo=tz.tzutc())

        self.assertFalse(tz.datetime_ambiguous(dt))


@pytest.mark.tzoffset
class TzOffsetTest(unittest.TestCase):
    def test_timedelta_offset(self):
        est = tz.tzoffset("EST", timedelta(hours=-5))
        est_s = tz.tzoffset("EST", -18000)

        self.assertEqual(est, est_s)

    def test_tz_name_none(self):
        gmt5 = tz.tzoffset(None, -18000)  # -5:00
        self.assertIs(datetime(2003, 10, 26, 0, 0, tzinfo=gmt5).tzname(), None)

    def test_time_only_offset(self):
        # tzoffset doesn't care
        tz_offset = tz.tzoffset("+3", 3600)
        self.assertEqual(time(13, 20, tzinfo=tz_offset).utcoffset(), timedelta(seconds=3600))

    def test_tz_offset_repr(self):
        tname = "EST"
        tzo = tz.tzoffset(tname, -5 * 3600)
        self.assertEqual(repr(tzo), "TzOffset(" + repr(tname) + ", -18000)")

    def test_equality(self):
        utc = tz.tzoffset("UTC", 0)
        gmt = tz.tzoffset("GMT", 0)

        self.assertEqual(utc, gmt)

    def test_utc_equality(self):
        utc = tz.UTC
        o_utc = tz.tzoffset("UTC", 0)

        self.assertEqual(utc, o_utc)
        self.assertEqual(o_utc, utc)

    def test_inequality_invalid(self):
        tzo = tz.tzoffset("-3", -3 * 3600)
        self.assertFalse(tzo == -3)
        self.assertNotEqual(tzo, -3)

    def test_inequality_unsupported(self):
        tzo = tz.tzoffset("-5", -5 * 3600)

        self.assertTrue(tzo == COMPARES_EQUAL)
        self.assertFalse(tzo != COMPARES_EQUAL)
        self.assertEqual(tzo, COMPARES_EQUAL)

    def test_ambiguity(self):
        # Pick an arbitrary datetime, this should always return False.
        dt = datetime(2011, 9, 1, 2, 30, tzinfo=tz.tzoffset("EST", -5 * 3600))

        self.assertFalse(tz.datetime_ambiguous(dt))

    def test_tz_offset_instance(self):
        tz1 = tz.tzoffset.instance("EST", timedelta(hours=-5))
        tz2 = tz.tzoffset.instance("EST", timedelta(hours=-5))

        assert tz1 is not tz2

    def test_tz_offset_singleton_different(self):
        tz1 = tz.tzoffset("EST", timedelta(hours=-5))
        tz2 = tz.tzoffset("EST", -18000)

        assert tz1 is tz2


@pytest.mark.smoke
@pytest.mark.tzoffset
def test_tzoffset_weakref():
    UTC1 = tz.tzoffset("UTC", 0)
    UTC_ref = weakref.ref(tz.tzoffset("UTC", 0))
    _ = UTC1 is UTC_ref()
    del UTC1
    gc.collect()

    assert UTC_ref() is not None  # Should be in the strong cache
    assert UTC_ref() is tz.tzoffset("UTC", 0)

    # Fill the strong cache with other items
    for offset in range(5, 15):
        tz.tzoffset("RandomZone", offset)

    gc.collect()
    assert UTC_ref() is None
    assert UTC_ref() is not tz.tzoffset("UTC", 0)


@pytest.mark.tzoffset
@pytest.mark.parametrize(
    "args", [("UTC", 0), ("EST", -18000), ("EST", timedelta(hours=-5)), (None, timedelta(hours=3))]
)
def test_tzoffset_singleton(args):
    tz1 = tz.tzoffset(*args)
    tz2 = tz.tzoffset(*args)

    assert tz1 is tz2


@pytest.mark.tzoffset
def test_tzoffset_sub_minute():
    delta = timedelta(hours=12, seconds=30)
    test_datetime = datetime(2000, 1, 1, tzinfo=tz.tzoffset(None, delta))
    assert test_datetime.utcoffset() == delta


@pytest.mark.tzlocal
class TzLocalTest(unittest.TestCase):
    def test_equality(self):
        tz1 = tz.tzlocal()
        tz2 = tz.tzlocal()

        # Explicitly calling == and != here to ensure the operators work
        self.assertTrue(tz1 == tz2)
        self.assertFalse(tz1 != tz2)

    def test_inequality_fixed_offset(self):
        tzl = tz.tzlocal()
        tzos = tz.tzoffset("LST", tzl._std_offset.total_seconds())
        tzod = tz.tzoffset("LDT", tzl._std_offset.total_seconds())

        self.assertFalse(tzl == tzos)
        self.assertFalse(tzl == tzod)
        self.assertTrue(tzl != tzos)
        self.assertTrue(tzl != tzod)

    def test_inequality_invalid(self):
        tzl = tz.tzlocal()

        self.assertTrue(tzl != 1)
        self.assertFalse(tzl == 1)

        # TODO: Use some sort of universal local mocking so that it's clear
        # that we're expecting tzlocal to *not* be Pacific/Kiritimati
        LINT = tz.gettz("Pacific/Kiritimati")
        self.assertTrue(tzl != LINT)
        self.assertFalse(tzl == LINT)

    def test_inequality_unsupported(self):
        tzl = tz.tzlocal()

        self.assertTrue(tzl == COMPARES_EQUAL)
        self.assertFalse(tzl != COMPARES_EQUAL)

    def test_repr(self):
        tzl = tz.tzlocal()

        self.assertEqual(repr(tzl), "TzLocal()")


@pytest.mark.parametrize(
    "args,kwargs",
    [
        (("EST", -18000), {}),
        (("EST", timedelta(hours=-5)), {}),
        (("EST",), {"offset": -18000}),
        (("EST",), {"offset": timedelta(hours=-5)}),
        (tuple(), {"name": "EST", "offset": -18000}),
    ],
)
def test_tzoffset_is(args, kwargs):
    tz_ref = tz.tzoffset("EST", -18000)
    assert tz.tzoffset(*args, **kwargs) is tz_ref


def test_tzoffset_is_not():
    assert tz.tzoffset("EDT", -14400) is not tz.tzoffset("EST", -18000)


@mark_tzlocal_nix
class TzLocalNixTest(unittest.TestCase, TzFoldMixin):
    # This is a set of tests for `tzlocal()` on *nix systems

    # POSIX string indicating change to summer time on the 2nd Sunday in March
    # at 2AM, and ending the 1st Sunday in November at 2AM. (valid >= 2007)
    TZ_EST = "EST+5EDT,M3.2.0/2,M11.1.0/2"

    # POSIX string for AEST/AEDT (valid >= 2008)
    TZ_AEST = "AEST-10AEDT,M10.1.0/2,M4.1.0/3"

    # POSIX string for BST/GMT
    TZ_LON = "GMT0BST,M3.5.0,M10.5.0"

    # POSIX string for UTC
    UTC = "UTC"

    def gettz(self, tzname):
        # Actual time zone changes are handled by the _gettz_context function
        return tz.tzlocal()

    def _gettz_context(self, tzname):
        tzname_map = {
            "Australia/Sydney": self.TZ_AEST,
            "America/Toronto": self.TZ_EST,
            "America/New_York": self.TZ_EST,
            "Europe/London": self.TZ_LON,
        }

        return TZEnvContext(tzname_map.get(tzname, tzname))

    def _test_tz_func(self, tzval, func, std_val, dst_val):
        """
        This generates tests about how the behavior of a function ``func``
        changes between STD and DST (e.g. utcoffset, tzname, dst).

        It assume that DST starts the 2nd Sunday in March and ends the 1st
        Sunday in November
        """
        with TZEnvContext(tzval):
            dt1 = datetime(2015, 2, 1, 12, 0, tzinfo=tz.tzlocal())  # STD
            dt2 = datetime(2015, 5, 1, 12, 0, tzinfo=tz.tzlocal())  # DST

            self.assertEqual(func(dt1), std_val)
            self.assertEqual(func(dt2), dst_val)

    def _test_tz_name(self, tzval, std_name, dst_name):
        func = datetime.tzname

        self._test_tz_func(tzval, func, std_name, dst_name)

    def test_tz_name_dst(self):
        # Test tzname in a zone with DST
        self._test_tz_name(self.TZ_EST, "EST", "EDT")

    def test_tz_name_utc(self):
        # Test tzname in a zone without DST
        self._test_tz_name(self.UTC, "UTC", "UTC")

    def _test_offset(self, tzval, std_off, dst_off):
        func = datetime.utcoffset

        self._test_tz_func(tzval, func, std_off, dst_off)

    def test_offset_dst(self):
        self._test_offset(self.TZ_EST, timedelta(hours=-5), timedelta(hours=-4))

    def test_offset_utc(self):
        self._test_offset(self.UTC, timedelta(0), timedelta(0))

    def _test_dst(self, tzval, dst_dst):
        func = datetime.dst
        std_dst = timedelta(0)

        self._test_tz_func(tzval, func, std_dst, dst_dst)

    def test_dst_dst(self):
        self._test_dst(self.TZ_EST, timedelta(hours=1))

    def test_dst_utc(self):
        self._test_dst(self.UTC, timedelta(0))

    def test_time_only_offset_local_utc(self):
        with TZEnvContext(self.UTC):
            self.assertEqual(time(13, 20, tzinfo=tz.tzlocal()).utcoffset(), timedelta(0))

    def test_time_only_offset_local_dst(self):
        with TZEnvContext(self.TZ_EST):
            self.assertIs(time(13, 20, tzinfo=tz.tzlocal()).utcoffset(), None)

    def test_time_only_dst_local_utc(self):
        with TZEnvContext(self.UTC):
            self.assertEqual(time(13, 20, tzinfo=tz.tzlocal()).dst(), timedelta(0))

    def test_time_only_dst_local_dst(self):
        with TZEnvContext(self.TZ_EST):
            self.assertIs(time(13, 20, tzinfo=tz.tzlocal()).dst(), None)

    def test_utc_equality(self):
        with TZEnvContext(self.UTC):
            assert tz.tzlocal() == tz.UTC


@mark_tzlocal_nix
@pytest.mark.parametrize("tzvar", ["UTC", "GMT0", "UTC0"])
def test_tzlocal_utc_equal(tzvar):
    with TZEnvContext(tzvar):
        assert tz.tzlocal() == tz.UTC


@mark_tzlocal_nix
@pytest.mark.parametrize("tzvar", ["Europe/London", "America/New_York", "GMT0BST", "EST5EDT"])
def test_tzlocal_utc_unequal(tzvar):
    with TZEnvContext(tzvar):
        assert tz.tzlocal() != tz.UTC


@mark_tzlocal_nix
def test_tzlocal_local_time_trim_colon():
    with TZEnvContext(":/etc/localtime"):
        assert tz.gettz() is not None


@mark_tzlocal_nix
@pytest.mark.parametrize(
    "tzvar, tzoff",
    [
        ("EST5", tz.tzoffset("EST", -18000)),
        ("GMT0", tz.tzoffset("GMT", 0)),
        ("YAKT-9", tz.tzoffset("YAKT", timedelta(hours=9))),
        ("JST-9", tz.tzoffset("JST", timedelta(hours=9))),
    ],
)
def test_tzlocal_offset_equal(tzvar, tzoff):
    with TZEnvContext(tzvar):
        # Including both to test both __eq__ and __ne__
        assert tz.tzlocal() == tzoff
        assert not (tz.tzlocal() != tzoff)


@mark_tzlocal_nix
@pytest.mark.parametrize(
    "tzvar, tzoff",
    [
        ("EST5EDT", tz.tzoffset("EST", -18000)),
        ("GMT0BST", tz.tzoffset("GMT", 0)),
        ("EST5", tz.tzoffset("EST", -14400)),
        ("YAKT-9", tz.tzoffset("JST", timedelta(hours=9))),
        ("JST-9", tz.tzoffset("YAKT", timedelta(hours=9))),
    ],
)
def test_tzlocal_offset_unequal(tzvar, tzoff):
    with TZEnvContext(tzvar):
        # Including both to test both __eq__ and __ne__
        assert tz.tzlocal() != tzoff
        assert not (tz.tzlocal() == tzoff)


@pytest.mark.gettz
class GettzTest(unittest.TestCase, TzFoldMixin):
    gettz = staticmethod(tz.gettz)

    def test_gettz(self):
        # bug 892569
        str(self.gettz("UTC"))

    def test_get_tz_equality(self):
        self.assertEqual(self.gettz("UTC"), self.gettz("UTC"))

    def test_time_only_gettz(self):
        # gettz returns None
        tz_get = self.gettz("Europe/Minsk")
        self.assertIs(time(13, 20, tzinfo=tz_get).utcoffset(), None)

    def test_time_only_gettz_dst(self):
        # gettz returns None
        tz_get = self.gettz("Europe/Minsk")
        self.assertIs(time(13, 20, tzinfo=tz_get).dst(), None)

    def test_time_only_gettz_tz_name(self):
        tz_get = self.gettz("Europe/Minsk")
        self.assertIs(time(13, 20, tzinfo=tz_get).tzname(), None)

    def test_time_only_format_z(self):
        tz_get = self.gettz("Europe/Minsk")
        t = time(13, 20, tzinfo=tz_get)

        self.assertEqual(t.strftime("%H%M%Z"), "1320")

    def test_portugal_dst(self):
        # In 1996, Portugal changed from CET to WET
        PORTUGAL = self.gettz("Portugal")

        t_cet = datetime(1996, 3, 31, 1, 59, tzinfo=PORTUGAL)

        self.assertEqual(t_cet.tzname(), "CET")
        self.assertEqual(t_cet.utcoffset(), timedelta(hours=1))
        self.assertEqual(t_cet.dst(), timedelta(0))

        t_west = datetime(1996, 3, 31, 2, 1, tzinfo=PORTUGAL)

        self.assertEqual(t_west.tzname(), "WEST")
        self.assertEqual(t_west.utcoffset(), timedelta(hours=1))
        self.assertEqual(t_west.dst(), timedelta(hours=1))

    def test_gettz_cache_tz_file(self):
        NYC1 = tz.gettz("America/New_York")
        NYC2 = tz.gettz("America/New_York")

        assert NYC1 is NYC2

    @pytest.mark.xfail(
        IS_WIN and ("/" in os.environ.get("TZ", "")), reason="On Windows IANA zones are currently always singletons"
    )
    def test_gettz_cache_tz_local(self):
        local1 = tz.gettz()
        local2 = tz.gettz()

        assert local1 is not local2


@pytest.mark.gettz
def test_gettz_same_result_for_none_and_empty_string():
    local_from_none = tz.gettz()
    local_from_empty_string = tz.gettz("")
    assert local_from_none is not None
    assert local_from_empty_string is not None
    assert local_from_none == local_from_empty_string


@pytest.mark.gettz
@pytest.mark.parametrize("badzone", ["Fake.Region/Abcdefghijklmnop"])  # Violates several tz project name rules
def test_gettz_badzone(badzone):
    # Make sure passing a bad TZ string to gettz returns None (GH #800)
    tzi = tz.gettz(badzone)
    assert tzi is None


@pytest.mark.gettz
def test_gettz_badzone_unicode():
    # Make sure a unicode string can be passed to TZ (GH #802)
    # When fixed, combine this with test_gettz_badzone
    tzi = tz.gettz("🐼")
    assert tzi is None


@pytest.mark.gettz
@pytest.mark.parametrize(
    "badzone,exc_reason",
    [
        pytest.param(b"America/New_York", ".*should be str, not bytes.*", id="bytes on Python 3"),
        pytest.param(
            object(),
            None,
            id="no startswith()",
            marks=[pytest.mark.xfail(reason="AttributeError instead of TypeError", raises=AttributeError)],
        ),
    ],
)
def test_gettz_zone_wrong_type(badzone, exc_reason):
    with pytest.raises(TypeError, match=exc_reason):
        tz.gettz(badzone)


@pytest.mark.gettz
@pytest.mark.xfail(IS_WIN, reason="zoneinfo separately cached")
def test_gettz_cache_clear():
    NYC1 = tz.gettz("America/New_York")
    tz.gettz.cache_clear()

    NYC2 = tz.gettz("America/New_York")

    assert NYC1 is not NYC2


@pytest.mark.gettz
@pytest.mark.xfail(IS_WIN, reason="zoneinfo separately cached")
def test_gettz_set_cache_size():
    tz.gettz.cache_clear()
    tz.gettz.set_cache_size(3)

    MONACO_ref = weakref.ref(tz.gettz("Europe/Monaco"))
    EASTER_ref = weakref.ref(tz.gettz("Pacific/Easter"))
    CURRIE_ref = weakref.ref(tz.gettz("Australia/Currie"))

    gc.collect()

    assert MONACO_ref() is not None
    assert EASTER_ref() is not None
    assert CURRIE_ref() is not None

    tz.gettz.set_cache_size(2)
    gc.collect()

    assert MONACO_ref() is None


@pytest.mark.xfail(IS_WIN, reason="Windows does not use system zoneinfo")
@pytest.mark.smoke
@pytest.mark.gettz
def test_gettz_weakref():
    tz.gettz.cache_clear()
    tz.gettz.set_cache_size(2)
    NYC1 = tz.gettz("America/New_York")
    NYC_ref = weakref.ref(tz.gettz("America/New_York"))

    assert NYC1 is NYC_ref()

    del NYC1
    gc.collect()

    assert NYC_ref() is not None  # Should still be in the strong cache
    assert tz.gettz("America/New_York") is NYC_ref()

    # Populate strong cache with other timezones
    tz.gettz("Europe/Monaco")
    tz.gettz("Pacific/Easter")
    tz.gettz("Australia/Currie")

    gc.collect()
    assert NYC_ref() is None  # Should have been pushed out
    assert tz.gettz("America/New_York") is not NYC_ref()


class ZoneInfoGettzTest(GettzTest):
    def gettz(self, tzname):
        zoneinfo_file = zoneinfo.get_zonefile_instance()
        return zoneinfo_file.get(tzname)

    def test_zone_info_file_start1(self):
        tz_ = self.gettz("EST5EDT")
        self.assertEqual(datetime(2003, 4, 6, 1, 59, tzinfo=tz_).tzname(), "EST", MISSING_TARBALL)
        self.assertEqual(datetime(2003, 4, 6, 2, 00, tzinfo=tz_).tzname(), "EDT")

    def test_zone_info_file_end1(self):
        tzc = self.gettz("EST5EDT")
        self.assertEqual(datetime(2003, 10, 26, 0, 59, tzinfo=tzc).tzname(), "EDT", MISSING_TARBALL)

        end_est = tz.enfold(datetime(2003, 10, 26, 1, 00, tzinfo=tzc), fold=1)
        self.assertEqual(end_est.tzname(), "EST")

    def test_zone_info_offset_signal(self):
        utc = self.gettz("UTC")
        nyc = self.gettz("America/New_York")
        self.assertNotEqual(utc, None, MISSING_TARBALL)
        self.assertNotEqual(nyc, None)
        t0 = datetime(2007, 11, 4, 0, 30, tzinfo=nyc)
        t1 = t0.astimezone(utc)
        t2 = t1.astimezone(nyc)
        self.assertEqual(t0, t2)
        self.assertEqual(nyc.dst(t0), timedelta(hours=1))

    def test_zone_info_copy(self):
        # copy.copy() called on a ZoneInfo file was returning the same instance
        CHI = self.gettz("America/Chicago")
        CHI_COPY = copy.copy(CHI)

        self.assertIsNot(CHI, CHI_COPY)
        self.assertEqual(CHI, CHI_COPY)

    def test_zone_info_deep_copy(self):
        CHI = self.gettz("America/Chicago")
        CHI_COPY = copy.deepcopy(CHI)

        self.assertIsNot(CHI, CHI_COPY)
        self.assertEqual(CHI, CHI_COPY)

    def test_zone_info_instance_caching(self):
        zif_0 = zoneinfo.get_zonefile_instance()
        zif_1 = zoneinfo.get_zonefile_instance()

        self.assertIs(zif_0, zif_1)

    def test_zone_info_new_instance(self):
        zif_0 = zoneinfo.get_zonefile_instance()
        zif_1 = zoneinfo.get_zonefile_instance(new_instance=True)
        zif_2 = zoneinfo.get_zonefile_instance()

        self.assertIsNot(zif_0, zif_1)
        self.assertIs(zif_1, zif_2)

    def test_zone_info_deprecated(self):
        with pytest.warns(DeprecationWarning):
            zoneinfo.gettz("US/Eastern")

    def test_zone_info_metadata_deprecated(self):
        with pytest.warns(DeprecationWarning):
            zoneinfo.gettz_db_metadata()


class TZRangeTest(unittest.TestCase, TzFoldMixin):
    TZ_EST = tz.tzrange(
        "EST",
        timedelta(hours=-5),
        "EDT",
        timedelta(hours=-4),
        start=relativedelta(month=3, day=1, hour=2, weekday=SU(+2)),
        end=relativedelta(month=11, day=1, hour=1, weekday=SU(+1)),
    )

    TZ_AEST = tz.tzrange(
        "AEST",
        timedelta(hours=10),
        "AEDT",
        timedelta(hours=11),
        start=relativedelta(month=10, day=1, hour=2, weekday=SU(+1)),
        end=relativedelta(month=4, day=1, hour=2, weekday=SU(+1)),
    )

    TZ_LON = tz.tzrange(
        "GMT",
        timedelta(hours=0),
        "BST",
        timedelta(hours=1),
        start=relativedelta(month=3, day=31, weekday=SU(-1), hours=2),
        end=relativedelta(month=10, day=31, weekday=SU(-1), hours=1),
    )
    # POSIX string for UTC
    UTC = "UTC"

    def gettz(self, tzname):
        tzname_map = {
            "Australia/Sydney": self.TZ_AEST,
            "America/Toronto": self.TZ_EST,
            "America/New_York": self.TZ_EST,
            "Europe/London": self.TZ_LON,
        }

        return tzname_map[tzname]

    def test_range_cmp1(self):
        self.assertEqual(
            tz.tzstr("EST5EDT"),
            tz.tzrange(
                "EST",
                -18000,
                "EDT",
                -14400,
                relativedelta(hours=+2, month=4, day=1, weekday=SU(+1)),
                relativedelta(hours=+1, month=10, day=31, weekday=SU(-1)),
            ),
        )

    def test_range_cmp2(self):
        self.assertEqual(tz.tzstr("EST5EDT"), tz.tzrange("EST", -18000, "EDT"))

    def test_range_offsets(self):
        TZR = tz.tzrange(
            "EST",
            -18000,
            "EDT",
            -14400,
            start=relativedelta(hours=2, month=4, day=1, weekday=SU(+2)),
            end=relativedelta(hours=1, month=10, day=31, weekday=SU(-1)),
        )

        dt_std = datetime(2014, 4, 11, 12, 0, tzinfo=TZR)  # STD
        dt_dst = datetime(2016, 4, 11, 12, 0, tzinfo=TZR)  # DST

        dst_zero = timedelta(0)
        dst_hour = timedelta(hours=1)

        std_offset = timedelta(hours=-5)
        dst_offset = timedelta(hours=-4)

        # Check dst()
        self.assertEqual(dt_std.dst(), dst_zero)
        self.assertEqual(dt_dst.dst(), dst_hour)

        # Check utcoffset()
        self.assertEqual(dt_std.utcoffset(), std_offset)
        self.assertEqual(dt_dst.utcoffset(), dst_offset)

        # Check tzname
        self.assertEqual(dt_std.tzname(), "EST")
        self.assertEqual(dt_dst.tzname(), "EDT")

    def test_time_only_range_fixed(self):
        # This is a fixed-offset zone, so tzrange allows this
        tz_range = tz.tzrange("dflt", stdoffset=timedelta(hours=-3))
        self.assertEqual(time(13, 20, tzinfo=tz_range).utcoffset(), timedelta(hours=-3))

    def test_time_only_range(self):
        # tzrange returns None because this zone has DST
        tz_range = tz.tzrange("EST", timedelta(hours=-5), "EDT", timedelta(hours=-4))
        self.assertIs(time(13, 20, tzinfo=tz_range).utcoffset(), None)

    def test_broken_is_dst_handling(self):
        # tzrange._isdst() was using a date() rather than a datetime().
        # Issue reported by Lennart Regebro.
        dt = datetime(2007, 8, 6, 4, 10, tzinfo=tz.UTC)
        self.assertEqual(dt.astimezone(tz=tz.gettz("GMT+2")), datetime(2007, 8, 6, 6, 10, tzinfo=tz.tzstr("GMT+2")))

    def test_range_time_delta(self):
        # Test that tzrange can be specified with a timedelta instead of an int.
        est5edt_td = tz.tzrange("EST", timedelta(hours=-5), "EDT", timedelta(hours=-4))

        est5edt_sec = tz.tzrange("EST", -18000, "EDT", -14400)

        self.assertEqual(est5edt_td, est5edt_sec)

    def test_range_equality(self):
        TZR1 = tz.tzrange("EST", -18000, "EDT", -14400)

        # Standard abbreviation different
        TZR2 = tz.tzrange("ET", -18000, "EDT", -14400)
        self.assertNotEqual(TZR1, TZR2)

        # DST abbreviation different
        TZR3 = tz.tzrange("EST", -18000, "EMT", -14400)
        self.assertNotEqual(TZR1, TZR3)

        # STD offset different
        TZR4 = tz.tzrange("EST", -14000, "EDT", -14400)
        self.assertNotEqual(TZR1, TZR4)

        # DST offset different
        TZR5 = tz.tzrange("EST", -18000, "EDT", -18000)
        self.assertNotEqual(TZR1, TZR5)

        # Start delta different
        TZR6 = tz.tzrange("EST", -18000, "EDT", -14400, start=relativedelta(hours=+1, month=3, day=1, weekday=SU(+2)))
        self.assertNotEqual(TZR1, TZR6)

        # End delta different
        TZR7 = tz.tzrange("EST", -18000, "EDT", -14400, end=relativedelta(hours=+1, month=11, day=1, weekday=SU(+2)))
        self.assertNotEqual(TZR1, TZR7)

    def test_range_inequality_unsupported(self):
        TZR = tz.tzrange("EST", -18000, "EDT", -14400)

        self.assertFalse(TZR == 4)
        self.assertTrue(TZR == COMPARES_EQUAL)
        self.assertFalse(TZR != COMPARES_EQUAL)


@pytest.mark.tzstr
class TZStrTest(unittest.TestCase, TzFoldMixin):
    # POSIX string indicating change to summer time on the 2nd Sunday in March
    # at 2AM, and ending the 1st Sunday in November at 2AM. (valid >= 2007)
    TZ_EST = "EST+5EDT,M3.2.0/2,M11.1.0/2"

    # POSIX string for AEST/AEDT (valid >= 2008)
    TZ_AEST = "AEST-10AEDT,M10.1.0/2,M4.1.0/3"

    # POSIX string for GMT/BST
    TZ_LON = "GMT0BST,M3.5.0,M10.5.0"

    def gettz(self, tzname):
        # Actual time zone changes are handled by the _gettz_context function
        tzname_map = {
            "Australia/Sydney": self.TZ_AEST,
            "America/Toronto": self.TZ_EST,
            "America/New_York": self.TZ_EST,
            "Europe/London": self.TZ_LON,
        }

        return tz.tzstr(tzname_map[tzname])

    def test_str_str(self):
        # Test that tz.tzstr() won't throw an error if given a str instead
        # of a unicode literal.
        self.assertEqual(datetime(2003, 4, 6, 1, 59, tzinfo=tz.tzstr("EST5EDT")).tzname(), "EST")
        self.assertEqual(datetime(2003, 4, 6, 2, 00, tzinfo=tz.tzstr("EST5EDT")).tzname(), "EDT")

    def test_str_inequality(self):
        TZS1 = tz.tzstr("EST5EDT4")

        # Standard abbreviation different
        TZS2 = tz.tzstr("ET5EDT4")
        self.assertNotEqual(TZS1, TZS2)

        # DST abbreviation different
        TZS3 = tz.tzstr("EST5EMT")
        self.assertNotEqual(TZS1, TZS3)

        # STD offset different
        TZS4 = tz.tzstr("EST4EDT4")
        self.assertNotEqual(TZS1, TZS4)

        # DST offset different
        TZS5 = tz.tzstr("EST5EDT3")
        self.assertNotEqual(TZS1, TZS5)

    def test_str_inequality_start_end(self):
        TZS1 = tz.tzstr("EST5EDT4")

        # Start delta different
        TZS2 = tz.tzstr("EST5EDT4,M4.2.0/02:00:00,M10-5-0/02:00")
        self.assertNotEqual(TZS1, TZS2)

        # End delta different
        TZS3 = tz.tzstr("EST5EDT4,M4.2.0/02:00:00,M11-5-0/02:00")
        self.assertNotEqual(TZS1, TZS3)

    def test_posix_offset(self):
        TZ1 = tz.tzstr("UTC-3")
        self.assertEqual(datetime(2015, 1, 1, tzinfo=TZ1).utcoffset(), timedelta(hours=-3))

        TZ2 = tz.tzstr("UTC-3", posix_offset=True)
        self.assertEqual(datetime(2015, 1, 1, tzinfo=TZ2).utcoffset(), timedelta(hours=+3))

    def test_str_inequality_unsupported(self):
        TZS = tz.tzstr("EST5EDT")

        self.assertFalse(TZS == 4)
        self.assertTrue(TZS == COMPARES_EQUAL)
        self.assertFalse(TZS != COMPARES_EQUAL)

    def test_tz_str_repr(self):
        TZS1 = tz.tzstr("EST5EDT4")
        TZS2 = tz.tzstr("EST")

        self.assertEqual(repr(TZS1), "TzStr(" + repr("EST5EDT4") + ")")
        self.assertEqual(repr(TZS2), "TzStr(" + repr("EST") + ")")

    def test_tz_str_failure(self):
        with self.assertRaises(ValueError):
            tz.tzstr("InvalidString;439999")

    def test_tz_str_singleton(self):
        tz1 = tz.tzstr("EST5EDT")
        tz2 = tz.tzstr("CST4CST")
        tz3 = tz.tzstr("EST5EDT")

        self.assertIsNot(tz1, tz2)
        self.assertIs(tz1, tz3)

    def test_tz_str_singleton_posix(self):
        tz_t1 = tz.tzstr("GMT+3", posix_offset=True)
        tz_f1 = tz.tzstr("GMT+3", posix_offset=False)

        tz_t2 = tz.tzstr("GMT+3", posix_offset=True)
        tz_f2 = tz.tzstr("GMT+3", posix_offset=False)

        self.assertIs(tz_t1, tz_t2)
        self.assertIsNot(tz_t1, tz_f1)

        self.assertIs(tz_f1, tz_f2)

    def test_tz_str_instance(self):
        tz1 = tz.tzstr("EST5EDT")
        tz2 = tz.tzstr.instance("EST5EDT")
        tz3 = tz.tzstr.instance("EST5EDT")

        assert tz1 is not tz2
        assert tz2 is not tz3

        # Ensure that these still are all the same zone
        assert tz1 == tz2 == tz3


@pytest.mark.smoke
@pytest.mark.tzstr
def test_tzstr_weakref():
    tz_t1 = tz.tzstr("EST5EDT")
    tz_t2_ref = weakref.ref(tz.tzstr("EST5EDT"))
    assert tz_t1 is tz_t2_ref()

    del tz_t1
    gc.collect()

    assert tz_t2_ref() is not None
    assert tz.tzstr("EST5EDT") is tz_t2_ref()

    for offset in range(5, 15):
        tz.tzstr(f"GMT+{offset}")
    gc.collect()

    assert tz_t2_ref() is None
    assert tz.tzstr("EST5EDT") is not tz_t2_ref()


@pytest.mark.tzstr
@pytest.mark.parametrize(
    "tz_str,expected",
    [
        # From https://www.gnu.org/software/libc/manual/html_node/TZ-Variable.html
        ("", tz.tzrange(None)),  # TODO: Should change this so tz.tzrange('') works
        (
            "EST+5EDT,M3.2.0/2,M11.1.0/12",
            tz.tzrange(
                "EST",
                -18000,
                "EDT",
                -14400,
                start=relativedelta(month=3, day=1, weekday=SU(2), hours=2),
                end=relativedelta(month=11, day=1, weekday=SU(1), hours=11),
            ),
        ),
        (
            "WART4WARST,J1/0,J365/25",  # This is DST all year, Western Argentina Summer Time
            tz.tzrange(
                "WART",
                timedelta(hours=-4),
                "WARST",
                start=relativedelta(month=1, day=1, hours=0),
                end=relativedelta(month=12, day=31, days=1),
            ),
        ),
        (
            "IST-2IDT,M3.4.4/26,M10.5.0",  # Israel Standard / Daylight Time
            tz.tzrange(
                "IST",
                timedelta(hours=2),
                "IDT",
                start=relativedelta(month=3, day=1, weekday=TH(4), days=1, hours=2),
                end=relativedelta(month=10, day=31, weekday=SU(-1), hours=1),
            ),
        ),
        (
            "WGT3WGST,M3.5.0/2,M10.5.0/1",
            tz.tzrange(
                "WGT",
                timedelta(hours=-3),
                "WGST",
                start=relativedelta(month=3, day=31, weekday=SU(-1), hours=2),
                end=relativedelta(month=10, day=31, weekday=SU(-1), hours=0),
            ),
        ),
        # Different offset specifications
        ("WGT0300WGST", tz.tzrange("WGT", timedelta(hours=-3), "WGST")),
        ("WGT03:00WGST", tz.tzrange("WGT", timedelta(hours=-3), "WGST")),
        ("AEST-1100AEDT", tz.tzrange("AEST", timedelta(hours=11), "AEDT")),
        ("AEST-11:00AEDT", tz.tzrange("AEST", timedelta(hours=11), "AEDT")),
        # Different time formats
        (
            "EST5EDT,M3.2.0/4:00,M11.1.0/3:00",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=relativedelta(month=3, day=1, weekday=SU(2), hours=4),
                end=relativedelta(month=11, day=1, weekday=SU(1), hours=2),
            ),
        ),
        (
            "EST5EDT,M3.2.0/04:00,M11.1.0/03:00",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=relativedelta(month=3, day=1, weekday=SU(2), hours=4),
                end=relativedelta(month=11, day=1, weekday=SU(1), hours=2),
            ),
        ),
        (
            "EST5EDT,M3.2.0/0400,M11.1.0/0300",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=relativedelta(month=3, day=1, weekday=SU(2), hours=4),
                end=relativedelta(month=11, day=1, weekday=SU(1), hours=2),
            ),
        ),
    ],
)
def test_valid_gnu_tzstr(tz_str, expected):
    tzi = tz.tzstr(tz_str)

    assert tzi == expected


@pytest.mark.tzstr
@pytest.mark.parametrize(
    "tz_str, expected",
    [
        (
            "EST5EDT,5,4,0,7200,11,3,0,7200",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=relativedelta(month=5, day=1, weekday=SU(+4), hours=+2),
                end=relativedelta(month=11, day=1, weekday=SU(+3), hours=+1),
            ),
        ),
        (
            "EST5EDT,5,-4,0,7200,11,3,0,7200",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=relativedelta(hours=+2, month=5, day=31, weekday=SU(-4)),
                end=relativedelta(hours=+1, month=11, day=1, weekday=SU(+3)),
            ),
        ),
        (
            "EST5EDT,5,4,0,7200,11,-3,0,7200",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=relativedelta(hours=+2, month=5, day=1, weekday=SU(+4)),
                end=relativedelta(hours=+1, month=11, day=31, weekday=SU(-3)),
            ),
        ),
        (
            "EST5EDT,5,4,0,7200,11,-3,0,7200,3600",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=relativedelta(hours=+2, month=5, day=1, weekday=SU(+4)),
                end=relativedelta(hours=+1, month=11, day=31, weekday=SU(-3)),
            ),
        ),
        (
            "EST5EDT,5,4,0,7200,11,-3,0,7200,3600",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=relativedelta(hours=+2, month=5, day=1, weekday=SU(+4)),
                end=relativedelta(hours=+1, month=11, day=31, weekday=SU(-3)),
            ),
        ),
        (
            "EST5EDT,5,4,0,7200,11,-3,0,7200,-3600",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                timedelta(hours=-6),
                start=relativedelta(hours=+2, month=5, day=1, weekday=SU(+4)),
                end=relativedelta(hours=+3, month=11, day=31, weekday=SU(-3)),
            ),
        ),
        (
            "EST5EDT,5,4,0,7200,11,-3,0,7200,+7200",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                timedelta(hours=-3),
                start=relativedelta(hours=+2, month=5, day=1, weekday=SU(+4)),
                end=relativedelta(hours=0, month=11, day=31, weekday=SU(-3)),
            ),
        ),
        (
            "EST5EDT,5,4,0,7200,11,-3,0,7200,+3600",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=relativedelta(hours=+2, month=5, day=1, weekday=SU(+4)),
                end=relativedelta(hours=+1, month=11, day=31, weekday=SU(-3)),
            ),
        ),
    ],
)
def test_valid_dateutil_format(tz_str, expected):
    # This tests the dateutil-specific format that is used widely in the tests
    # and examples. It is unclear where this format originated from.
    with pytest.warns(tz.DeprecatedTzFormatWarning):
        tzi = tz.tzstr.instance(tz_str)

    assert tzi == expected


@pytest.mark.tzstr
@pytest.mark.parametrize(
    "tz_str",
    [
        "hdfiughdfuig,dfughdfuigpu87ñ::",
        ",dfughdfuigpu87ñ::",
        "-1:WART4WARST,J1,J365/25",
        "WART4WARST,J1,J365/-25",
        "IST-2IDT,M3.4.-1/26,M10.5.0",
        "IST-2IDT,M3,2000,1/26,M10,5,0",
    ],
)
def test_invalid_gnu_tzstr(tz_str):
    with pytest.raises(ValueError):
        tz.tzstr(tz_str)


# Different representations of the same default rule set
DEFAULT_TZSTR_RULES_EQUIV_2003 = [
    "EST5EDT",
    "EST5EDT4,M4.1.0/02:00:00,M10-5-0/02:00",
    "EST5EDT4,95/02:00:00,298/02:00",
    "EST5EDT4,J96/02:00:00,J299/02:00",
    "EST5EDT4,J96/02:00:00,J299/02",
]


@pytest.mark.tzstr
@pytest.mark.parametrize("tz_str", DEFAULT_TZSTR_RULES_EQUIV_2003)
def test_tzstr_default_start(tz_str):
    tzi = tz.tzstr(tz_str)
    dt_std = datetime(2003, 4, 6, 1, 59, tzinfo=tzi)
    dt_dst = datetime(2003, 4, 6, 2, 00, tzinfo=tzi)

    assert get_timezone_tuple(dt_std) == EST_TUPLE
    assert get_timezone_tuple(dt_dst) == EDT_TUPLE


@pytest.mark.tzstr
@pytest.mark.parametrize("tz_str", DEFAULT_TZSTR_RULES_EQUIV_2003)
def test_tzstr_default_end(tz_str):
    tzi = tz.tzstr(tz_str)
    dt_dst = datetime(2003, 10, 26, 0, 59, tzinfo=tzi)
    dt_dst_ambig = datetime(2003, 10, 26, 1, 00, tzinfo=tzi)
    dt_std_ambig = tz.enfold(dt_dst_ambig, fold=1)
    dt_std = datetime(2003, 10, 26, 2, 00, tzinfo=tzi)

    assert get_timezone_tuple(dt_dst) == EDT_TUPLE
    assert get_timezone_tuple(dt_dst_ambig) == EDT_TUPLE
    assert get_timezone_tuple(dt_std_ambig) == EST_TUPLE
    assert get_timezone_tuple(dt_std) == EST_TUPLE


@pytest.mark.tzstr
@pytest.mark.parametrize("tzstr_1", ["EST5EDT", "EST5EDT4,M4.1.0/02:00:00,M10-5-0/02:00"])
@pytest.mark.parametrize("tzstr_2", ["EST5EDT", "EST5EDT4,M4.1.0/02:00:00,M10-5-0/02:00"])
def test_tzstr_default_cmp(tzstr_1, tzstr_2):
    tz1 = tz.tzstr(tzstr_1)
    tz2 = tz.tzstr(tzstr_2)

    assert tz1 == tz2


class TZICalTest(unittest.TestCase, TzFoldMixin):
    def _gettz_str_tuple(self, tzname):

        tzname_map = {
            "Australia/Sydney": TZ_AEST,
            "America/Toronto": TZ_EST,
            "America/New_York": TZ_EST,
            "America/Los_Angeles": TZ_PST,
            "Europe/London": TZ_LON,
        }

        return tzname_map[tzname]

    def _gettz_str(self, tzname):
        return "\n".join(self._gettz_str_tuple(tzname))

    def _tzstr_dtstart_with_params(self, tzname, param_str):
        # Adds parameters to the DTSTART values of a given tzstr
        tz_str_tuple = self._gettz_str_tuple(tzname)

        out_tz = []
        for line in tz_str_tuple:
            if line.startswith("DTSTART"):
                name, value = line.split(":", 1)
                line = name + ";" + param_str + ":" + value

            out_tz.append(line)

        return "\n".join(out_tz)

    def gettz(self, tzname):
        tz_str = self._gettz_str(tzname)

        tzc = tz.tzical(StringIO(tz_str)).get()

        return tzc

    def test_repr(self):
        instr = StringIO(TZICAL_PST8PDT)
        instr.name = "StringIO(PST8PDT)"
        tzc = tz.tzical(instr)

        self.assertEqual(repr(tzc), "TzIcal(" + repr(instr.name) + ")")

    # Test performance
    def _test_us_zone(self, tzc, func, values, start):
        if start:
            dt1 = datetime(2003, 3, 9, 1, 59)
            dt2 = datetime(2003, 3, 9, 2, 00)
            fold = [0, 0]
        else:
            dt1 = datetime(2003, 11, 2, 0, 59)
            dt2 = datetime(2003, 11, 2, 1, 00)
            fold = [0, 1]

        dts = (tz.enfold(dt.replace(tzinfo=tzc), fold=f) for dt, f in zip((dt1, dt2), fold))

        for value, dt_ in zip(values, dts):
            self.assertEqual(func(dt_), value)

    def _test_multi_zones(self, tzstrs, tzids, func, values, start):
        tzic = tz.tzical(StringIO("\n".join(tzstrs)))
        for tzid, vals in zip(tzids, values):
            tzc = tzic.get(tzid)

            self._test_us_zone(tzc, func, vals, start)

    def _prepare_est(self):
        tz_str = self._gettz_str("America/New_York")
        return tz.tzical(StringIO(tz_str)).get()

    def _test_est(self, start, test_type, tzc=None):
        if tzc is None:
            tzc = self._prepare_est()

        argdict = {
            "name": (datetime.tzname, ("EST", "EDT")),
            "offset": (datetime.utcoffset, (timedelta(hours=-5), timedelta(hours=-4))),
            "dst": (datetime.dst, (timedelta(hours=0), timedelta(hours=1))),
        }

        func, values = argdict[test_type]

        if not start:
            values = reversed(values)

        self._test_us_zone(tzc, func, values, start=start)

    def test_est_start_name(self):
        self._test_est(start=True, test_type="name")

    def test_est_end_name(self):
        self._test_est(start=False, test_type="name")

    def test_est_start_offset(self):
        self._test_est(start=True, test_type="offset")

    def test_est_end_offset(self):
        self._test_est(start=False, test_type="offset")

    def test_est_start_dst(self):
        self._test_est(start=True, test_type="dst")

    def test_est_end_dst(self):
        self._test_est(start=False, test_type="dst")

    def test_est_value_datetime(self):
        # Violating one-test-per-test rule because we're not set up to do
        # parameterized tests and the manual proliferation is getting a bit
        # out of hand.
        tz_str = self._tzstr_dtstart_with_params("America/New_York", "VALUE=DATE-TIME")

        tzc = tz.tzical(StringIO(tz_str)).get()

        for start in (True, False):
            for test_type in ("name", "offset", "dst"):
                self._test_est(start=start, test_type=test_type, tzc=tzc)

    def _test_multizone(self, start, test_type):
        tzstrs = (self._gettz_str("America/New_York"), self._gettz_str("America/Los_Angeles"))
        tzids = ("US-Eastern", "US-Pacific")

        argdict = {
            "name": (datetime.tzname, (("EST", "EDT"), ("PST", "PDT"))),
            "offset": (
                datetime.utcoffset,
                ((timedelta(hours=-5), timedelta(hours=-4)), (timedelta(hours=-8), timedelta(hours=-7))),
            ),
            "dst": (datetime.dst, ((timedelta(hours=0), timedelta(hours=1)), (timedelta(hours=0), timedelta(hours=1)))),
        }

        func, values = argdict[test_type]

        if not start:
            values = map(reversed, values)

        self._test_multi_zones(tzstrs, tzids, func, values, start)

    def test_multi_zone_start_name(self):
        self._test_multizone(start=True, test_type="name")

    def test_multi_zone_end_name(self):
        self._test_multizone(start=False, test_type="name")

    def test_multi_zone_start_offset(self):
        self._test_multizone(start=True, test_type="offset")

    def test_multi_zone_end_offset(self):
        self._test_multizone(start=False, test_type="offset")

    def test_multi_zone_start_dst(self):
        self._test_multizone(start=True, test_type="dst")

    def test_multi_zone_end_dst(self):
        self._test_multizone(start=False, test_type="dst")

    def test_multi_zone_keys(self):
        est_str = self._gettz_str("America/New_York")
        pst_str = self._gettz_str("America/Los_Angeles")
        tzic = tz.tzical(StringIO("\n".join((est_str, pst_str))))

        # Sort keys because they are in a random order, being dictionary keys
        keys = sorted(tzic.keys())

        self.assertEqual(keys, ["US-Eastern", "US-Pacific"])

    # Test error conditions
    def test_empty_string(self):
        with self.assertRaises(ValueError):
            tz.tzical(StringIO(""))

    def test_multi_zone_get(self):
        tzic = tz.tzical(StringIO(TZICAL_EST5EDT + TZICAL_PST8PDT))

        with self.assertRaises(ValueError):
            tzic.get()

    def test_dtstart_date(self):
        tz_str = self._tzstr_dtstart_with_params("America/New_York", "VALUE=DATE")
        with self.assertRaises(ValueError):
            tz.tzical(StringIO(tz_str))

    def test_dtstart_tzid(self):
        tz_str = self._tzstr_dtstart_with_params("America/New_York", "TZID=UTC")
        with self.assertRaises(ValueError):
            tz.tzical(StringIO(tz_str))

    def test_dtstart_bad_param(self):
        tz_str = self._tzstr_dtstart_with_params("America/New_York", "FOO=BAR")
        with self.assertRaises(ValueError):
            tz.tzical(StringIO(tz_str))

    # Test Parsing
    def test_gap(self):
        tzic = tz.tzical(StringIO("\n".join((TZICAL_EST5EDT, TZICAL_PST8PDT))))

        keys = sorted(tzic.keys())
        self.assertEqual(keys, ["US-Eastern", "US-Pacific"])


class TZTest(unittest.TestCase):
    def test_file_start1(self):
        tzc = tz.tzfile(BytesIO(base64.b64decode(TZFILE_EST5EDT)))
        self.assertEqual(datetime(2003, 4, 6, 1, 59, tzinfo=tzc).tzname(), "EST")
        self.assertEqual(datetime(2003, 4, 6, 2, 00, tzinfo=tzc).tzname(), "EDT")

    def test_file_end1(self):
        tzc = tz.tzfile(BytesIO(base64.b64decode(TZFILE_EST5EDT)))
        self.assertEqual(datetime(2003, 10, 26, 0, 59, tzinfo=tzc).tzname(), "EDT")
        end_est = tz.enfold(datetime(2003, 10, 26, 1, 00, tzinfo=tzc))
        self.assertEqual(end_est.tzname(), "EST")

    def test_file_last_transition(self):
        # After the last transition, it goes to standard time in perpetuity
        tzc = tz.tzfile(BytesIO(base64.b64decode(TZFILE_EST5EDT)))
        self.assertEqual(datetime(2037, 10, 25, 0, 59, tzinfo=tzc).tzname(), "EDT")

        last_date = tz.enfold(datetime(2037, 10, 25, 1, 00, tzinfo=tzc), fold=1)
        self.assertEqual(last_date.tzname(), "EST")

        self.assertEqual(datetime(2038, 5, 25, 12, 0, tzinfo=tzc).tzname(), "EST")

    def test_invalid_file(self):
        # Should throw a ValueError if an invalid file is passed
        with self.assertRaises(ValueError):
            tz.tzfile(BytesIO(b"BadFile"))

    def test_filestream_with_name_repr(self):
        # If fileobj is a filestream with a "name" attribute this name should
        # be reflected in the tz object's repr
        fileobj = BytesIO(base64.b64decode(TZFILE_EST5EDT))
        fileobj.name = "foo"
        tzc = tz.tzfile(fileobj)
        self.assertEqual(repr(tzc), "TzFile(" + repr("foo") + ")")

    def test_leap_count_decodes_properly(self):
        # This timezone has leapcnt, and failed to decode until
        # Eugene Oden notified about the issue.

        # As leap information is currently unused (and unstored) by tzfile() we
        # can only indirectly test this: Take advantage of tzfile() not closing
        # the input file if handed in as an opened file and assert that the
        # full file content has been read by tzfile(). Note: For this test to
        # work NEW_YORK must be in TZif version 1 format i.e. no more data
        # after TZif v1 header + data has been read
        fileobj = BytesIO(base64.b64decode(NEW_YORK))
        tz.tzfile(fileobj)
        # we expect no remaining file content now, i.e. zero-length; if there's
        # still data we haven't read the file format correctly
        remaining_tzfile_content = fileobj.read()
        self.assertEqual(len(remaining_tzfile_content), 0)

    def test_is_std(self):
        # NEW_YORK tzfile contains this isstd information:
        isstd_expected = (0, 0, 0, 1)
        tzc = tz.tzfile(BytesIO(base64.b64decode(NEW_YORK)))
        # gather the actual information as parsed by the tzfile class
        isstd = []
        for ttinfo in tzc._ttinfo_list:
            # ttinfo objects contain boolean values
            isstd.append(int(ttinfo.isstd))
        # ttinfo list may contain more entries than isstd file content
        isstd = tuple(isstd[: len(isstd_expected)])
        self.assertEqual(
            isstd_expected, isstd, f"isstd UTC/local indicators parsed: {isstd} != tzfile contents: {isstd_expected}"
        )

    def test_gmt_has_no_daylight(self):
        # tz.tzstr("GMT+2") improperly considered daylight saving time.
        # Issue reported by Lennart Regebro.
        dt = datetime(2007, 8, 6, 4, 10)
        self.assertEqual(tz.gettz("GMT+2").dst(dt), timedelta(0))

    def test_gmt_offset(self):
        # GMT and UTC offsets have inverted signal when compared to the
        # usual TZ variable handling.
        dt = datetime(2007, 8, 6, 4, 10, tzinfo=tz.UTC)
        self.assertEqual(dt.astimezone(tz=tz.tzstr("GMT+2")), datetime(2007, 8, 6, 6, 10, tzinfo=tz.tzstr("GMT+2")))
        self.assertEqual(dt.astimezone(tz=tz.gettz("UTC-2")), datetime(2007, 8, 6, 2, 10, tzinfo=tz.tzstr("UTC-2")))

    @pytest.mark.skipif(IS_WIN, reason="requires Unix")
    def test_tzset_doesnt_corrupt(self):
        # if we start in non-UTC then tzset UTC make sure parse doesn't get confused
        with TZEnvContext("UTC"):
            # this should parse to UTC timezone not the original timezone
            dt = parse("2014-07-20T12:34:56+00:00")
            self.assertEqual(str(dt), "2014-07-20 12:34:56+00:00")


@pytest.mark.tzfile
def test_tzfile_sub_minute_offset():
    # If user running python 3.6 or newer, exact offset is used
    tzc = tz.tzfile(BytesIO(base64.b64decode(EUROPE_HELSINKI)))
    offset = timedelta(hours=1, minutes=39, seconds=52)
    assert datetime(1900, 1, 1, 0, 0, tzinfo=tzc).utcoffset() == offset


@pytest.mark.tzfile
def test_samoa_transition():
    # utcoffset() was erroneously returning +14:00 an hour early (GH #812)
    apia = tz.gettz("Pacific/Apia")
    dt = datetime(2011, 12, 29, 23, 59, tzinfo=apia)
    assert dt.utcoffset() == timedelta(hours=-10)

    # Make sure the transition actually works, too
    dt_after = (dt.astimezone(tz.UTC) + timedelta(minutes=1)).astimezone(apia)
    assert dt_after == datetime(2011, 12, 31, tzinfo=apia)
    assert dt_after.utcoffset() == timedelta(hours=14)


class TzPickleTest(PicklableMixin, unittest.TestCase):
    _asfile = False

    def setUp(self):
        self.assert_picklable = partial(self.assert_picklable, asfile=self._asfile)

    def test_pickle_tz_utc(self):
        self.assert_picklable(tz.tzutc(), singleton=True)

    def test_pickle_tz_offset_zero(self):
        self.assert_picklable(tz.tzoffset("UTC", 0), singleton=True)

    def test_pickle_tz_offset_pos(self):
        self.assert_picklable(tz.tzoffset("UTC+1", 3600), singleton=True)

    def test_pickle_tz_offset_neg(self):
        self.assert_picklable(tz.tzoffset("UTC-1", -3600), singleton=True)

    @pytest.mark.tzlocal
    def test_pickle_tz_local(self):
        self.assert_picklable(tz.tzlocal())

    def test_pickle_tz_file_est5edt(self):
        tzc = tz.tzfile(BytesIO(base64.b64decode(TZFILE_EST5EDT)))
        self.assert_picklable(tzc)

    def test_pickle_tz_file_europe_helsinki(self):
        tzc = tz.tzfile(BytesIO(base64.b64decode(EUROPE_HELSINKI)))
        self.assert_picklable(tzc)

    def test_pickle_tz_file_new_york(self):
        tzc = tz.tzfile(BytesIO(base64.b64decode(NEW_YORK)))
        self.assert_picklable(tzc)

    @unittest.skip("Known failure")
    def test_pickle_tzical(self):
        tzc = tz.tzical(StringIO(TZICAL_EST5EDT)).get()
        self.assert_picklable(tzc)

    def test_pickle_tz_gettz(self):
        self.assert_picklable(tz.gettz("America/New_York"))

    def test_pickle_zone_file_gettz(self):
        zoneinfo_file = zoneinfo.get_zonefile_instance()
        tzi = zoneinfo_file.get("America/New_York")
        self.assertIsNot(tzi, None)
        self.assert_picklable(tzi)


class TzPickleFileTest(TzPickleTest):
    """Run all the TzPickleTest tests, using a temporary file"""

    _asfile = True


class DatetimeAmbiguousTest(unittest.TestCase):
    """Test the datetime_exists / datetime_ambiguous functions"""

    def test_no_tz_specified(self):
        with self.assertRaises(ValueError):
            tz.datetime_ambiguous(datetime(2016, 4, 1, 2, 9))

    def _get_no_support_tzinfo_class(self, dt_start, dt_end, dst_only=False):
        # Generates a class of tzinfo with no support for is_ambiguous
        # where dates between dt_start and dt_end are ambiguous.

        class FoldingTzInfo(tzinfo):
            def utcoffset(self, dt):
                if not dst_only:
                    dt_n = dt.replace(tzinfo=None)

                    if dt_start <= dt_n < dt_end and getattr(dt_n, "fold", 0):
                        return timedelta(hours=-1)

                return timedelta(hours=0)

            def dst(self, dt):
                dt_n = dt.replace(tzinfo=None)

                if dt_start <= dt_n < dt_end and getattr(dt_n, "fold", 0):
                    return timedelta(hours=1)
                return timedelta(0)

        return FoldingTzInfo

    def _get_no_support_tzinfo(self, dt_start, dt_end, dst_only=False):
        return self._get_no_support_tzinfo_class(dt_start, dt_end, dst_only)()

    def test_no_support_ambiguity_fold_naive(self):
        dt_start = datetime(2018, 9, 1, 1, 0)
        dt_end = datetime(2018, 9, 1, 2, 0)

        tzi = self._get_no_support_tzinfo(dt_start, dt_end)

        self.assertTrue(tz.datetime_ambiguous(datetime(2018, 9, 1, 1, 30), tz=tzi))

    def test_no_support_ambiguity_fold_aware(self):
        dt_start = datetime(2018, 9, 1, 1, 0)
        dt_end = datetime(2018, 9, 1, 2, 0)

        tzi = self._get_no_support_tzinfo(dt_start, dt_end)

        self.assertTrue(tz.datetime_ambiguous(datetime(2018, 9, 1, 1, 30, tzinfo=tzi)))

    def test_no_support_ambiguity_unambiguous_naive(self):
        dt_start = datetime(2018, 9, 1, 1, 0)
        dt_end = datetime(2018, 9, 1, 2, 0)

        tzi = self._get_no_support_tzinfo(dt_start, dt_end)

        self.assertFalse(tz.datetime_ambiguous(datetime(2018, 10, 1, 12, 30), tz=tzi))

    def test_no_support_ambiguity_unambiguous_aware(self):
        dt_start = datetime(2018, 9, 1, 1, 0)
        dt_end = datetime(2018, 9, 1, 2, 0)

        tzi = self._get_no_support_tzinfo(dt_start, dt_end)

        self.assertFalse(tz.datetime_ambiguous(datetime(2018, 10, 1, 12, 30, tzinfo=tzi)))

    def test_no_support_ambiguity_fold_dst_only(self):
        dt_start = datetime(2018, 9, 1, 1, 0)
        dt_end = datetime(2018, 9, 1, 2, 0)

        tzi = self._get_no_support_tzinfo(dt_start, dt_end, dst_only=True)

        self.assertTrue(tz.datetime_ambiguous(datetime(2018, 9, 1, 1, 30), tz=tzi))

    def test_no_support_ambiguity_unambiguous_dst_only(self):
        dt_start = datetime(2018, 9, 1, 1, 0)
        dt_end = datetime(2018, 9, 1, 2, 0)

        tzi = self._get_no_support_tzinfo(dt_start, dt_end, dst_only=True)

        self.assertFalse(tz.datetime_ambiguous(datetime(2018, 10, 1, 12, 30), tz=tzi))

    def test_support_ambiguity_fold_naive(self):
        tzi = tz.gettz("US/Eastern")

        dt = datetime(2011, 11, 6, 1, 30)

        self.assertTrue(tz.datetime_ambiguous(dt, tz=tzi))

    def test_support_ambiguity_fold_aware(self):
        tzi = tz.gettz("US/Eastern")

        dt = datetime(2011, 11, 6, 1, 30, tzinfo=tzi)

        self.assertTrue(tz.datetime_ambiguous(dt))

    def test_support_ambiguity_unambiguous_aware(self):
        tzi = tz.gettz("US/Eastern")

        dt = datetime(2011, 11, 6, 4, 30)

        self.assertFalse(tz.datetime_ambiguous(dt, tz=tzi))

    def test_support_ambiguity_unambiguous_naive(self):
        tzi = tz.gettz("US/Eastern")

        dt = datetime(2011, 11, 6, 4, 30, tzinfo=tzi)

        self.assertFalse(tz.datetime_ambiguous(dt))

    def _get_ambig_error_tzinfo(self, dt_start, dt_end, dst_only=False):
        cTzInfo = self._get_no_support_tzinfo_class(dt_start, dt_end, dst_only)

        # Takes the wrong number of arguments and raises an error anyway.
        class FoldTzInfoRaises(cTzInfo):
            def is_ambiguous(self, dt, other_arg):
                raise NotImplementedError("This is not implemented")

        return FoldTzInfoRaises()

    def test_incompatible_ambiguity_fold_naive(self):
        dt_start = datetime(2018, 9, 1, 1, 0)
        dt_end = datetime(2018, 9, 1, 2, 0)

        tzi = self._get_ambig_error_tzinfo(dt_start, dt_end)

        self.assertTrue(tz.datetime_ambiguous(datetime(2018, 9, 1, 1, 30), tz=tzi))

    def test_incompatible_ambiguity_fold_aware(self):
        dt_start = datetime(2018, 9, 1, 1, 0)
        dt_end = datetime(2018, 9, 1, 2, 0)

        tzi = self._get_ambig_error_tzinfo(dt_start, dt_end)

        self.assertTrue(tz.datetime_ambiguous(datetime(2018, 9, 1, 1, 30, tzinfo=tzi)))

    def test_incompatible_ambiguity_unambiguous_naive(self):
        dt_start = datetime(2018, 9, 1, 1, 0)
        dt_end = datetime(2018, 9, 1, 2, 0)

        tzi = self._get_ambig_error_tzinfo(dt_start, dt_end)

        self.assertFalse(tz.datetime_ambiguous(datetime(2018, 10, 1, 12, 30), tz=tzi))

    def test_incompatible_ambiguity_unambiguous_aware(self):
        dt_start = datetime(2018, 9, 1, 1, 0)
        dt_end = datetime(2018, 9, 1, 2, 0)

        tzi = self._get_ambig_error_tzinfo(dt_start, dt_end)

        self.assertFalse(tz.datetime_ambiguous(datetime(2018, 10, 1, 12, 30, tzinfo=tzi)))

    def test_incompatible_ambiguity_fold_dst_only(self):
        dt_start = datetime(2018, 9, 1, 1, 0)
        dt_end = datetime(2018, 9, 1, 2, 0)

        tzi = self._get_ambig_error_tzinfo(dt_start, dt_end, dst_only=True)

        self.assertTrue(tz.datetime_ambiguous(datetime(2018, 9, 1, 1, 30), tz=tzi))

    def test_incompatible_ambiguity_unambiguous_dst_only(self):
        dt_start = datetime(2018, 9, 1, 1, 0)
        dt_end = datetime(2018, 9, 1, 2, 0)

        tzi = self._get_ambig_error_tzinfo(dt_start, dt_end, dst_only=True)

        self.assertFalse(tz.datetime_ambiguous(datetime(2018, 10, 1, 12, 30), tz=tzi))

    def test_specified_tz_overrides_attached(self):
        # If a tz is specified, the datetime will be treated as naive.

        # This is not ambiguous in the local zone
        dt = datetime(2011, 11, 6, 1, 30, tzinfo=tz.gettz("Australia/Sydney"))

        self.assertFalse(tz.datetime_ambiguous(dt))

        tzi = tz.gettz("US/Eastern")
        self.assertTrue(tz.datetime_ambiguous(dt, tz=tzi))


class DatetimeExistsTest(unittest.TestCase):
    def test_no_tz_specified(self):
        with self.assertRaises(ValueError):
            tz.datetime_exists(datetime(2016, 4, 1, 2, 9))

    def test_in_gap_naive(self):
        tzi = tz.gettz("Australia/Sydney")

        dt = datetime(2012, 10, 7, 2, 30)

        self.assertFalse(tz.datetime_exists(dt, tz=tzi))

    def test_in_gap_aware(self):
        tzi = tz.gettz("Australia/Sydney")

        dt = datetime(2012, 10, 7, 2, 30, tzinfo=tzi)

        self.assertFalse(tz.datetime_exists(dt))

    def test_exists_naive(self):
        tzi = tz.gettz("Australia/Sydney")

        dt = datetime(2012, 10, 7, 10, 30)

        self.assertTrue(tz.datetime_exists(dt, tz=tzi))

    def test_exists_aware(self):
        tzi = tz.gettz("Australia/Sydney")

        dt = datetime(2012, 10, 7, 10, 30, tzinfo=tzi)

        self.assertTrue(tz.datetime_exists(dt))

    def test_specified_tz_overrides_attached(self):
        est = tz.gettz("US/Eastern")
        aest = tz.gettz("Australia/Sydney")

        dt = datetime(2012, 10, 7, 2, 30, tzinfo=est)  # This time exists

        self.assertFalse(tz.datetime_exists(dt, tz=aest))


class TestEnfold:
    def test_enter_fold_default(self):
        dt = tz.enfold(datetime(2020, 1, 19, 3, 32))

        assert dt.fold == 1

    def test_enter_fold(self):
        dt = tz.enfold(datetime(2020, 1, 19, 3, 32), fold=1)

        assert dt.fold == 1

    def test_exit_fold(self):
        dt = tz.enfold(datetime(2020, 1, 19, 3, 32), fold=0)

        # Before Python 3.6, dt.fold won't exist if fold is 0.
        assert getattr(dt, "fold", 0) == 0

    def test_defold(self):
        dt = tz.enfold(datetime(2020, 1, 19, 3, 32), fold=1)

        dt2 = tz.enfold(dt, fold=0)

        assert getattr(dt2, "fold", 0) == 0

    def test_fold_replace_args(self):
        # This test can be dropped when Python < 3.6 is dropped, since it
        # is mainly to cover the `replace` method on _DatetimeWithFold
        dt = tz.enfold(datetime(1950, 1, 2, 12, 30, 15, 8), fold=1)

        dt2 = dt.replace(1952, 2, 3, 13, 31, 16, 9)
        assert dt2 == tz.enfold(datetime(1952, 2, 3, 13, 31, 16, 9), fold=1)
        assert dt2.fold == 1

    def test_fold_replace_exception_duplicate_args(self):
        dt = tz.enfold(datetime(1999, 1, 3), fold=1)

        with pytest.raises(TypeError):
            dt.replace(1950, year=2000)  # pylint: disable=e1124


@pytest.mark.tz_resolve_imaginary
class ImaginaryDateTest(unittest.TestCase):
    def test_canberra_forward(self):
        tzi = tz.gettz("Australia/Canberra")
        dt = datetime(2018, 10, 7, 2, 30, tzinfo=tzi)
        dt_act = tz.resolve_imaginary(dt)
        dt_exp = datetime(2018, 10, 7, 3, 30, tzinfo=tzi)
        self.assertEqual(dt_act, dt_exp)

    def test_london_forward(self):
        tzi = tz.gettz("Europe/London")
        dt = datetime(2018, 3, 25, 1, 30, tzinfo=tzi)
        dt_act = tz.resolve_imaginary(dt)
        dt_exp = datetime(2018, 3, 25, 2, 30, tzinfo=tzi)
        self.assertEqual(dt_act, dt_exp)

    def test_keiv_forward(self):
        tzi = tz.gettz("Europe/Kiev")
        dt = datetime(2018, 3, 25, 3, 30, tzinfo=tzi)
        dt_act = tz.resolve_imaginary(dt)
        dt_exp = datetime(2018, 3, 25, 4, 30, tzinfo=tzi)
        self.assertEqual(dt_act, dt_exp)


@pytest.mark.tz_resolve_imaginary
@pytest.mark.parametrize(
    "dt",
    [
        datetime(2017, 11, 5, 1, 30, tzinfo=tz.gettz("America/New_York")),
        datetime(2018, 10, 28, 1, 30, tzinfo=tz.gettz("Europe/London")),
        datetime(2017, 4, 2, 2, 30, tzinfo=tz.gettz("Australia/Sydney")),
    ],
)
def test_resolve_imaginary_ambiguous(dt):
    assert tz.resolve_imaginary(dt) is dt

    dt_f = tz.enfold(dt)
    assert dt is not dt_f
    assert tz.resolve_imaginary(dt_f) is dt_f


@pytest.mark.tz_resolve_imaginary
@pytest.mark.parametrize(
    "dt",
    [
        datetime(2017, 6, 2, 12, 30, tzinfo=tz.gettz("America/New_York")),
        datetime(2018, 4, 2, 9, 30, tzinfo=tz.gettz("Europe/London")),
        datetime(2017, 2, 2, 16, 30, tzinfo=tz.gettz("Australia/Sydney")),
        datetime(2017, 12, 2, 12, 30, tzinfo=tz.gettz("America/New_York")),
        datetime(2018, 12, 2, 9, 30, tzinfo=tz.gettz("Europe/London")),
        datetime(2017, 6, 2, 16, 30, tzinfo=tz.gettz("Australia/Sydney")),
        datetime(2025, 9, 25, 1, 17, tzinfo=tz.UTC),
        datetime(2025, 9, 25, 1, 17, tzinfo=tz.tzoffset("EST", -18000)),
        datetime(2019, 3, 4, tzinfo=None),
    ],
)
def test_resolve_imaginary_existing(dt):
    assert tz.resolve_imaginary(dt) is dt


def __get_kiritimati_resolve_imaginary_test():
    # In the 2018d release of the IANA database, the Kiritimati "imaginary day"
    # data was corrected, so if the system zoneinfo is older than 2018d, the
    # Kiritimati test will fail.

    tzi = tz.gettz("Pacific/Kiritimati")
    new_version = False
    if not tz.datetime_exists(datetime(1995, 1, 1, 12, 30), tzi):
        zif = zoneinfo.get_zonefile_instance()
        if zif.metadata is not None:
            new_version = zif.metadata["tzversion"] >= "2018d"

        if new_version:
            tzi = zif.get("Pacific/Kiritimati")
    else:
        new_version = True

    if new_version:
        dates = (datetime(1994, 12, 31, 12, 30), datetime(1995, 1, 1, 12, 30))
    else:
        dates = (datetime(1995, 1, 1, 12, 30), datetime(1995, 1, 2, 12, 30))

    return (tzi,) + dates


resolve_imaginary_tests = [
    (tz.gettz("Europe/London"), datetime(2018, 3, 25, 1, 30), datetime(2018, 3, 25, 2, 30)),
    (tz.gettz("America/New_York"), datetime(2017, 3, 12, 2, 30), datetime(2017, 3, 12, 3, 30)),
    (tz.gettz("Australia/Sydney"), datetime(2014, 10, 5, 2, 0), datetime(2014, 10, 5, 3, 0)),
    __get_kiritimati_resolve_imaginary_test(),
    (tz.gettz("Africa/Monrovia"), datetime(1972, 1, 7, 0, 30), datetime(1972, 1, 7, 1, 14, 30)),
]


@pytest.mark.tz_resolve_imaginary
@pytest.mark.parametrize("tzi, dt, dt_exp", resolve_imaginary_tests)
def test_resolve_imaginary(tzi, dt, dt_exp):
    dt = dt.replace(tzinfo=tzi)
    dt_exp = dt_exp.replace(tzinfo=tzi)

    dt_r = tz.resolve_imaginary(dt)
    assert dt_r == dt_exp
    assert dt_r.tzname() == dt_exp.tzname()
    assert dt_r.utcoffset() == dt_exp.utcoffset()
