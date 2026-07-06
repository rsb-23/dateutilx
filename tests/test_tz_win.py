import contextlib
import datetime as dt
import unittest
from datetime import datetime, timedelta

from dateutil import tz
from dateutil.helper import is_windows_os
from dateutil.parser import parse

from ._common import COMPARES_EQUAL, TZWinContext

IS_WIN = is_windows_os()
try:
    from dateutil import tzwin
except ImportError as e:
    if IS_WIN:
        raise e
    tzwin = None

UTC = tz.UTC

ESTs = "Eastern Standard Time"
EDTs = "Eastern Daylight Time"


class TzWinFoldMixin:
    context = contextlib.nullcontext

    def get_args(self, tzname):
        return (tzname,)

    @staticmethod
    def get_utc_transitions(tzi, year, gap):
        dston, dstoff = tzi.transitions(year)
        if gap:
            t_n = dston - timedelta(minutes=30)

            t0_u = t_n.replace(tzinfo=tzi).astimezone(tz.UTC)
        else:
            # Get 1 hour before the first ambiguous date
            t_n = dstoff - timedelta(minutes=30)

            t0_u = t_n.replace(tzinfo=tzi).astimezone(tz.UTC)
            t_n += timedelta(hours=1)  # Naive ambiguous date
            t0_u = t0_u + timedelta(hours=1)  # First ambiguous date

        t1_u = t0_u + timedelta(hours=1)
        return t_n, t0_u, t1_u

    def test_fold_positive_utc_offset(self):
        # Test that we can resolve ambiguous times
        tzname = "AUS Eastern Standard Time"
        args = self.get_args(tzname)

        with self.context(tzname):
            # Calling fromutc() alters the tzfile object
            SYD = self.tzclass(*args)

            # Get the transition time in UTC from the object, because
            # Windows doesn't store historical info
            t_n, t0_u, t1_u = self.get_utc_transitions(SYD, 2012, False)

            # Using fresh tzfiles
            t0_syd = t0_u.astimezone(SYD)
            t1_syd = t1_u.astimezone(SYD)

            self.assertEqual(t0_syd.replace(tzinfo=None), t_n)

            self.assertEqual(t1_syd.replace(tzinfo=None), t_n)

            self.assertEqual(t0_syd.utcoffset(), timedelta(hours=11))
            self.assertEqual(t1_syd.utcoffset(), timedelta(hours=10))
            self.assertNotEqual(t0_syd.tzname(), t1_syd.tzname())

    def test_gap_positive_utc_offset(self):
        # Test that we don't have a problem around gaps.
        tzname = "AUS Eastern Standard Time"
        args = self.get_args(tzname)

        with self.context(tzname):
            SYD = self.tzclass(*args)

            t_n, t0_u, t1_u = self.get_utc_transitions(SYD, 2012, True)

            t0 = t0_u.astimezone(SYD)
            t1 = t1_u.astimezone(SYD)

            self.assertEqual(t0.replace(tzinfo=None), t_n)

            self.assertEqual(t1.replace(tzinfo=None), t_n + timedelta(hours=2))

            self.assertEqual(t0.utcoffset(), timedelta(hours=10))
            self.assertEqual(t1.utcoffset(), timedelta(hours=11))

    def test_fold_negative_utc_offset(self):
        # Test that we can resolve ambiguous times
        tzname = "Eastern Standard Time"
        args = self.get_args(tzname)

        with self.context(tzname):
            TOR = self.tzclass(*args)

            t_n, t0_u, t1_u = self.get_utc_transitions(TOR, 2011, False)

            t0_tor = t0_u.astimezone(TOR)
            t1_tor = t1_u.astimezone(TOR)

            self.assertEqual(t0_tor.replace(tzinfo=None), t_n)
            self.assertEqual(t1_tor.replace(tzinfo=None), t_n)

            self.assertNotEqual(t0_tor.tzname(), t1_tor.tzname())
            self.assertEqual(t0_tor.utcoffset(), timedelta(hours=-4.0))
            self.assertEqual(t1_tor.utcoffset(), timedelta(hours=-5.0))

    def test_gap_negative_utc_offset(self):
        # Test that we don't have a problem around gaps.
        tzname = "Eastern Standard Time"
        args = self.get_args(tzname)

        with self.context(tzname):
            TOR = self.tzclass(*args)

            t_n, t0_u, t1_u = self.get_utc_transitions(TOR, 2011, True)

            t0 = t0_u.astimezone(TOR)
            t1 = t1_u.astimezone(TOR)

            self.assertEqual(t0.replace(tzinfo=None), t_n)

            self.assertEqual(t1.replace(tzinfo=None), t_n + timedelta(hours=2))

            self.assertNotEqual(t0.tzname(), t1.tzname())
            self.assertEqual(t0.utcoffset(), timedelta(hours=-5.0))
            self.assertEqual(t1.utcoffset(), timedelta(hours=-4.0))

    def test_fold_independence(self):
        tzname = "Eastern Standard Time"
        args = self.get_args(tzname)

        with self.context(tzname):
            NYC = self.tzclass(*args)
            hour = timedelta(hours=1)

            # Firmly 2015-11-01 0:30 EDT-4
            t_n = self.get_utc_transitions(NYC, 2015, False)[0]

            pre_dst = (t_n - hour).replace(tzinfo=NYC)

            # Currently, there's no way around the fact that this resolves to an
            # ambiguous date, which defaults to EST. I'm not hard-coding in the
            # answer, though, because the preferred behavior would be that this
            # results in a time on the EDT side.

            # Ambiguous between 2015-11-01 1:30 EDT-4 and 2015-11-01 1:30 EST-5
            in_dst = pre_dst + hour
            in_dst_tzname_0 = in_dst.tzname()  # Stash the tzname - EDT

            # Doing the arithmetic in UTC creates a date that is unambiguously
            # 2015-11-01 1:30 EDT-5
            in_dst_via_utc = (pre_dst.astimezone(UTC) + 2 * hour).astimezone(NYC)

            # Make sure we got the right folding behavior
            self.assertNotEqual(in_dst_via_utc.tzname(), in_dst_tzname_0)

            # Now check to make sure in_dst's tzname hasn't changed
            self.assertEqual(in_dst_tzname_0, in_dst.tzname())

    def test_in_zone_fold_equality(self):
        # Two datetimes in the same zone are considered to be equal if their
        # wall times are equal, even if they have different absolute times.
        tzname = "Eastern Standard Time"
        args = self.get_args(tzname)

        with self.context(tzname):
            NYC = self.tzclass(*args)

            t_n = self.get_utc_transitions(NYC, 2011, False)[0]

            dt0 = t_n.replace(tzinfo=NYC)
            dt1 = tz.enfold(dt0, fold=1)

            # Make sure these actually represent different times
            self.assertNotEqual(dt0.astimezone(UTC), dt1.astimezone(UTC))

            # Test that they compare equal
            self.assertEqual(dt0, dt1)


@unittest.skipUnless(IS_WIN, "Requires Windows")
class TzWinTest(unittest.TestCase, TzWinFoldMixin):
    def setUp(self):
        self.tzclass = tzwin.TzWin

    def test_tz_res_load_name(self):
        # This may not work right on non-US locales.
        tzr = tzwin.TzRes()
        self.assertEqual(tzr.load_name(112), "Eastern Standard Time")

    def test_tz_res_name_from_string(self):
        tzr = tzwin.TzRes()
        self.assertEqual(tzr.name_from_string("@tzres.dll,-221"), "Alaskan Daylight Time")

        self.assertEqual(tzr.name_from_string("Samoa Daylight Time"), "Samoa Daylight Time")

        with self.assertRaises(ValueError):
            tzr.name_from_string("@tzres.dll,100")

    def test_isdst_zone_with_no_daylight_saving(self):
        tz_ = self.tzclass("UTC")
        dt_ = parse("2013-03-06 19:08:15")
        self.assertFalse(tz_._isdst(dt_))

    def test_offset(self):
        tz_ = self.tzclass("Cape Verde Standard Time")
        self.assertEqual(tz_.utcoffset(datetime(1995, 5, 21, 12, 9, 13)), timedelta(-1, 82800))

    def test_tzwin_name(self):
        # https://github.com/dateutil/dateutil/issues/143
        tw = tz.tzwin("Eastern Standard Time")

        # Cover the transitions for at least two years.
        transition_dates = [
            (datetime(2015, 3, 8, 0, 59), ESTs),
            (datetime(2015, 3, 8, 3, 1), EDTs),
            (datetime(2015, 11, 1, 0, 59), EDTs),
            (datetime(2015, 11, 1, 3, 1), ESTs),
            (datetime(2016, 3, 13, 0, 59), ESTs),
            (datetime(2016, 3, 13, 3, 1), EDTs),
            (datetime(2016, 11, 6, 0, 59), EDTs),
            (datetime(2016, 11, 6, 3, 1), ESTs),
        ]

        for t_date, expected in transition_dates:
            self.assertEqual(t_date.replace(tzinfo=tw).tzname(), expected)

    def test_tzwin_repr(self):
        tw = tz.tzwin("Yakutsk Standard Time")
        self.assertEqual(repr(tw), "tzwin(" + repr("Yakutsk Standard Time") + ")")

    def test_tz_win_equality(self):
        # https://github.com/dateutil/dateutil/issues/151
        tzwin_names = (
            "Eastern Standard Time",
            "West Pacific Standard Time",
            "Yakutsk Standard Time",
            "Iran Standard Time",
            "UTC",
        )

        for tzwin_name in tzwin_names:
            # Get two different instances to compare
            tw1 = tz.tzwin(tzwin_name)
            tw2 = tz.tzwin(tzwin_name)

            self.assertEqual(tw1, tw2)

    def test_tz_win_inequality(self):
        # https://github.com/dateutil/dateutil/issues/151
        # Note these last two currently differ only in their name.
        tzwin_names = (
            ("Eastern Standard Time", "Yakutsk Standard Time"),
            ("Greenwich Standard Time", "GMT Standard Time"),
            ("GMT Standard Time", "UTC"),
            ("E. South America Standard Time", "Argentina Standard Time"),
        )

        for tzwn1, tzwn2 in tzwin_names:
            # Get two different instances to compare
            tw1 = tz.tzwin(tzwn1)
            tw2 = tz.tzwin(tzwn2)

            self.assertNotEqual(tw1, tw2)

    def test_tz_win_equality_invalid(self):
        # Compare to objects that do not implement comparison with this
        # (should default to False)
        EST = tz.tzwin("Eastern Standard Time")
        self.assertFalse(EST == UTC)
        self.assertFalse(EST == 1)
        self.assertFalse(UTC == EST)

        self.assertTrue(EST != UTC)
        self.assertTrue(EST != 1)

    def test_tz_win_inequality_unsupported(self):
        # Compare it to an object that is promiscuous about equality, but for
        # which tzwin does not implement an equality operator.
        EST = tz.tzwin("Eastern Standard Time")
        self.assertTrue(EST == COMPARES_EQUAL)
        self.assertFalse(EST != COMPARES_EQUAL)

    def test_tzwin_time_only_dst(self):
        # For zones with DST, .dst() should return None
        tw_est = tz.tzwin("Eastern Standard Time")
        self.assertIs(dt.time(14, 10, tzinfo=tw_est).dst(), None)

        # This zone has no DST, so .dst() can return 0
        tw_sast = tz.tzwin("South Africa Standard Time")
        self.assertEqual(dt.time(14, 10, tzinfo=tw_sast).dst(), timedelta(0))

    def test_tzwin_time_only_utc_offset(self):
        # For zones with DST, .utcoffset() should return None
        tw_est = tz.tzwin("Eastern Standard Time")
        self.assertIs(dt.time(14, 10, tzinfo=tw_est).utcoffset(), None)

        # This zone has no DST, so .utcoffset() returns standard offset
        tw_sast = tz.tzwin("South Africa Standard Time")
        self.assertEqual(dt.time(14, 10, tzinfo=tw_sast).utcoffset(), timedelta(hours=2))

    def test_tzwin_time_only_tzname(self):
        # For zones with DST, the name defaults to standard time
        tw_est = tz.tzwin("Eastern Standard Time")
        self.assertEqual(dt.time(14, 10, tzinfo=tw_est).tzname(), "Eastern Standard Time")

        # For zones with no DST, this should work normally.
        tw_sast = tz.tzwin("South Africa Standard Time")
        self.assertEqual(dt.time(14, 10, tzinfo=tw_sast).tzname(), "South Africa Standard Time")


@unittest.skipUnless(IS_WIN, "Requires Windows")
class TzWinLocalTest(unittest.TestCase, TzWinFoldMixin):
    def setUp(self):
        self.tzclass = tzwin.TzWinLocal
        self.context = TZWinContext

    def get_args(self, tzname):
        return ()

    def test_local(self):
        # Not sure how to pin a local time zone, so for now we're just going
        # to run this and make sure it doesn't raise an error
        # See GitHub Issue #135: https://github.com/dateutil/dateutil/issues/135
        datetime.now(self.tzclass())

    def test_tzwin_local_utc_offset(self):
        with TZWinContext("Eastern Standard Time"):
            tzwl = self.tzclass()
            self.assertEqual(datetime(2014, 3, 11, tzinfo=tzwl).utcoffset(), timedelta(hours=-4))

    def test_tzwin_local_name(self):
        # https://github.com/dateutil/dateutil/issues/143

        transition_dates = [
            (datetime(2015, 3, 8, 0, 59), ESTs),
            (datetime(2015, 3, 8, 3, 1), EDTs),
            (datetime(2015, 11, 1, 0, 59), EDTs),
            (datetime(2015, 11, 1, 3, 1), ESTs),
            (datetime(2016, 3, 13, 0, 59), ESTs),
            (datetime(2016, 3, 13, 3, 1), EDTs),
            (datetime(2016, 11, 6, 0, 59), EDTs),
            (datetime(2016, 11, 6, 3, 1), ESTs),
        ]

        with TZWinContext("Eastern Standard Time"):
            tw = self.tzclass()

            for t_date, expected in transition_dates:
                self.assertEqual(t_date.replace(tzinfo=tw).tzname(), expected)

    def test_tz_win_local_repr(self):
        tw = self.tzclass()
        self.assertEqual(repr(tw), "tzwinlocal()")

    def test_tzwin_local_repr(self):
        # https://github.com/dateutil/dateutil/issues/143
        with TZWinContext("Eastern Standard Time"):
            tw = self.tzclass()

            self.assertEqual(str(tw), "tzwinlocal(" + repr("Eastern Standard Time") + ")")

        with TZWinContext("Pacific Standard Time"):
            tw = self.tzclass()

            self.assertEqual(str(tw), "tzwinlocal(" + repr("Pacific Standard Time") + ")")

    def test_tzwin_local_equality(self):
        tw_est = tz.tzwin("Eastern Standard Time")
        tw_pst = tz.tzwin("Pacific Standard Time")

        with TZWinContext("Eastern Standard Time"):
            twl1 = self.tzclass()
            twl2 = self.tzclass()

            self.assertEqual(twl1, twl2)
            self.assertEqual(twl1, tw_est)
            self.assertNotEqual(twl1, tw_pst)

        with TZWinContext("Pacific Standard Time"):
            twl1 = self.tzclass()
            twl2 = self.tzclass()
            tw = tz.tzwin("Pacific Standard Time")

            self.assertEqual(twl1, twl2)
            self.assertEqual(twl1, tw)
            self.assertEqual(twl1, tw_pst)
            self.assertNotEqual(twl1, tw_est)

    def test_tzwin_local_time_only_dst(self):
        # For zones with DST, .dst() should return None
        with TZWinContext("Eastern Standard Time"):
            twl = self.tzclass()
            self.assertIs(dt.time(14, 10, tzinfo=twl).dst(), None)

        # This zone has no DST, so .dst() can return 0
        with TZWinContext("South Africa Standard Time"):
            twl = self.tzclass()
            self.assertEqual(dt.time(14, 10, tzinfo=twl).dst(), timedelta(0))

    def test_tzwin_local_time_only_utc_offset(self):
        # For zones with DST, .utcoffset() should return None
        with TZWinContext("Eastern Standard Time"):
            twl = self.tzclass()
            self.assertIs(dt.time(14, 10, tzinfo=twl).utcoffset(), None)

        # This zone has no DST, so .utcoffset() returns standard offset
        with TZWinContext("South Africa Standard Time"):
            twl = self.tzclass()
            self.assertEqual(dt.time(14, 10, tzinfo=twl).utcoffset(), timedelta(hours=2))

    def test_tzwin_local_time_only_tz_name(self):
        # For zones with DST, the name defaults to standard time
        with TZWinContext("Eastern Standard Time"):
            twl = self.tzclass()
            self.assertEqual(dt.time(14, 10, tzinfo=twl).tzname(), "Eastern Standard Time")

        # For zones with no DST, this should work normally.
        with TZWinContext("South Africa Standard Time"):
            twl = self.tzclass()
            self.assertEqual(dt.time(14, 10, tzinfo=twl).tzname(), "South Africa Standard Time")
