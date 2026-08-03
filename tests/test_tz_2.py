import gc
import unittest
import weakref
from datetime import datetime, timedelta

import pytest

from dateutilx import tz
from dateutilx.relativedelta import RelativeDelta
from dateutilx.weekday import SU, TH

from ._common import COMPARES_EQUAL
from .test_tz import TzFoldMixin

EST_TUPLE = ("EST", timedelta(hours=-5), timedelta(hours=0))
EDT_TUPLE = ("EDT", timedelta(hours=-4), timedelta(hours=1))


def get_timezone_tuple(dt):
    """Retrieve a (tzname, utcoffset, dst) tuple for a given DST"""
    return dt.tzname(), dt.utcoffset(), dt.dst()


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
        with pytest.raises(ValueError):
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
                start=RelativeDelta(month=3, day=1, weekday=SU(2), hours=2),
                end=RelativeDelta(month=11, day=1, weekday=SU(1), hours=11),
            ),
        ),
        (
            "WART4WARST,J1/0,J365/25",  # This is DST all year, Western Argentina Summer Time
            tz.tzrange(
                "WART",
                timedelta(hours=-4),
                "WARST",
                start=RelativeDelta(month=1, day=1, hours=0),
                end=RelativeDelta(month=12, day=31, days=1),
            ),
        ),
        (
            "IST-2IDT,M3.4.4/26,M10.5.0",  # Israel Standard / Daylight Time
            tz.tzrange(
                "IST",
                timedelta(hours=2),
                "IDT",
                start=RelativeDelta(month=3, day=1, weekday=TH(4), days=1, hours=2),
                end=RelativeDelta(month=10, day=31, weekday=SU(-1), hours=1),
            ),
        ),
        (
            "WGT3WGST,M3.5.0/2,M10.5.0/1",
            tz.tzrange(
                "WGT",
                timedelta(hours=-3),
                "WGST",
                start=RelativeDelta(month=3, day=31, weekday=SU(-1), hours=2),
                end=RelativeDelta(month=10, day=31, weekday=SU(-1), hours=0),
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
                start=RelativeDelta(month=3, day=1, weekday=SU(2), hours=4),
                end=RelativeDelta(month=11, day=1, weekday=SU(1), hours=2),
            ),
        ),
        (
            "EST5EDT,M3.2.0/04:00,M11.1.0/03:00",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=RelativeDelta(month=3, day=1, weekday=SU(2), hours=4),
                end=RelativeDelta(month=11, day=1, weekday=SU(1), hours=2),
            ),
        ),
        (
            "EST5EDT,M3.2.0/0400,M11.1.0/0300",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=RelativeDelta(month=3, day=1, weekday=SU(2), hours=4),
                end=RelativeDelta(month=11, day=1, weekday=SU(1), hours=2),
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
                start=RelativeDelta(month=5, day=1, weekday=SU(+4), hours=+2),
                end=RelativeDelta(month=11, day=1, weekday=SU(+3), hours=+1),
            ),
        ),
        (
            "EST5EDT,5,-4,0,7200,11,3,0,7200",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=RelativeDelta(hours=+2, month=5, day=31, weekday=SU(-4)),
                end=RelativeDelta(hours=+1, month=11, day=1, weekday=SU(+3)),
            ),
        ),
        (
            "EST5EDT,5,4,0,7200,11,-3,0,7200",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=RelativeDelta(hours=+2, month=5, day=1, weekday=SU(+4)),
                end=RelativeDelta(hours=+1, month=11, day=31, weekday=SU(-3)),
            ),
        ),
        (
            "EST5EDT,5,4,0,7200,11,-3,0,7200,3600",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=RelativeDelta(hours=+2, month=5, day=1, weekday=SU(+4)),
                end=RelativeDelta(hours=+1, month=11, day=31, weekday=SU(-3)),
            ),
        ),
        (
            "EST5EDT,5,4,0,7200,11,-3,0,7200,3600",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=RelativeDelta(hours=+2, month=5, day=1, weekday=SU(+4)),
                end=RelativeDelta(hours=+1, month=11, day=31, weekday=SU(-3)),
            ),
        ),
        (
            "EST5EDT,5,4,0,7200,11,-3,0,7200,-3600",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                timedelta(hours=-6),
                start=RelativeDelta(hours=+2, month=5, day=1, weekday=SU(+4)),
                end=RelativeDelta(hours=+3, month=11, day=31, weekday=SU(-3)),
            ),
        ),
        (
            "EST5EDT,5,4,0,7200,11,-3,0,7200,+7200",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                timedelta(hours=-3),
                start=RelativeDelta(hours=+2, month=5, day=1, weekday=SU(+4)),
                end=RelativeDelta(hours=0, month=11, day=31, weekday=SU(-3)),
            ),
        ),
        (
            "EST5EDT,5,4,0,7200,11,-3,0,7200,+3600",
            tz.tzrange(
                "EST",
                timedelta(hours=-5),
                "EDT",
                start=RelativeDelta(hours=+2, month=5, day=1, weekday=SU(+4)),
                end=RelativeDelta(hours=+1, month=11, day=31, weekday=SU(-3)),
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
    dt_std_ambig = dt_dst_ambig.replace(fold=1)
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

    dt_f = dt.replace(fold=1)
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


resolve_imaginary_tests = [
    (tz.gettz("Europe/London"), datetime(2018, 3, 25, 1, 30), datetime(2018, 3, 25, 2, 30)),
    (tz.gettz("America/New_York"), datetime(2017, 3, 12, 2, 30), datetime(2017, 3, 12, 3, 30)),
    (tz.gettz("Australia/Sydney"), datetime(2014, 10, 5, 2, 0), datetime(2014, 10, 5, 3, 0)),
    (tz.gettz("Pacific/Kiritimati"), datetime(1994, 12, 31, 12, 30), datetime(1995, 1, 1, 12, 30)),
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
