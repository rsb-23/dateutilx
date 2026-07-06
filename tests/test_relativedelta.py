import unittest
from datetime import date, datetime, timedelta

import pytest

from dateutil.helper import Day
from dateutil.relativedelta import FR, MO, SU, TU, WE, RelativeDelta

from ._common import NOT_A_VALUE

relativedelta = RelativeDelta


class RelativeDeltaTest(unittest.TestCase):
    now = datetime(2003, 9, 17, 20, 54, 47, 282310)
    today = date(2003, 9, 17)

    def test_inheritance(self):
        # Ensure that relativedelta is inheritance-friendly.
        class RDChildClass(relativedelta):
            pass

        cc_rd = RDChildClass(
            years=1, months=1, days=1, leapdays=1, weeks=1, hours=1, minutes=1, seconds=1, microseconds=1
        )

        rd = relativedelta(
            years=1, months=1, days=1, leapdays=1, weeks=1, hours=1, minutes=1, seconds=1, microseconds=1
        )

        self.assertEqual(type(cc_rd + rd), type(cc_rd), msg="Addition does not inherit type.")

        self.assertEqual(type(cc_rd - rd), type(cc_rd), msg="Subtraction does not inherit type.")

        self.assertEqual(type(-cc_rd), type(cc_rd), msg="Negation does not inherit type.")  # pylint: disable=e1130

        self.assertEqual(type(cc_rd * 5.0), type(cc_rd), msg="Multiplication does not inherit type.")

        self.assertEqual(type(cc_rd / 5.0), type(cc_rd), msg="Division does not inherit type.")

    def test_month_end_month_beginning(self):
        self.assertEqual(
            relativedelta(datetime(2003, 1, 31, 23, 59, 59), datetime(2003, 3, 1, 0, 0, 0)),
            relativedelta(months=-1, seconds=-1),
        )

        self.assertEqual(
            relativedelta(datetime(2003, 3, 1, 0, 0, 0), datetime(2003, 1, 31, 23, 59, 59)),
            relativedelta(months=1, seconds=1),
        )

    def test_month_end_month_beginning_leap_year(self):
        self.assertEqual(
            relativedelta(datetime(2012, 1, 31, 23, 59, 59), datetime(2012, 3, 1, 0, 0, 0)),
            relativedelta(months=-1, seconds=-1),
        )

        self.assertEqual(
            relativedelta(datetime(2003, 3, 1, 0, 0, 0), datetime(2003, 1, 31, 23, 59, 59)),
            relativedelta(months=1, seconds=1),
        )

    def test_next_month(self):
        self.assertEqual(self.now + relativedelta(months=+1), datetime(2003, 10, 17, 20, 54, 47, 282310))

    def test_next_month_plus_one_week(self):
        self.assertEqual(self.now + relativedelta(months=+1, weeks=+1), datetime(2003, 10, 24, 20, 54, 47, 282310))

    def test_next_month_plus_one_week10am(self):
        self.assertEqual(self.today + relativedelta(months=+1, weeks=+1, hour=10), datetime(2003, 10, 24, 10, 0))

    def test_next_month_plus_one_week_10am_diff(self):
        self.assertEqual(
            relativedelta(datetime(2003, 10, 24, 10, 0), self.today), relativedelta(months=+1, days=+7, hours=+10)
        )

    def test_one_month_before_one_year(self):
        self.assertEqual(self.now + relativedelta(years=+1, months=-1), datetime(2004, 8, 17, 20, 54, 47, 282310))

    def test_months_of_diff_num_of_days(self):
        self.assertEqual(date(2003, 1, 27) + relativedelta(months=+1), date(2003, 2, 27))
        self.assertEqual(date(2003, 1, 31) + relativedelta(months=+1), date(2003, 2, 28))
        self.assertEqual(date(2003, 1, 31) + relativedelta(months=+2), date(2003, 3, 31))

    def test_months_of_diff_num_of_days_with_years(self):
        self.assertEqual(date(2000, 2, 28) + relativedelta(years=+1), date(2001, 2, 28))
        self.assertEqual(date(2000, 2, 29) + relativedelta(years=+1), date(2001, 2, 28))

        self.assertEqual(date(1999, 2, 28) + relativedelta(years=+1), date(2000, 2, 28))
        self.assertEqual(date(1999, 3, 1) + relativedelta(years=+1), date(2000, 3, 1))
        self.assertEqual(date(1999, 3, 1) + relativedelta(years=+1), date(2000, 3, 1))

        self.assertEqual(date(2001, 2, 28) + relativedelta(years=-1), date(2000, 2, 28))
        self.assertEqual(date(2001, 3, 1) + relativedelta(years=-1), date(2000, 3, 1))

    def test_next_friday(self):
        self.assertEqual(self.today + relativedelta(weekday=FR), date(2003, 9, 19))

    def test_next_friday_int(self):
        self.assertEqual(self.today + relativedelta(weekday=Day.FRI), date(2003, 9, 19))

    def test_last_friday_in_this_month(self):
        self.assertEqual(self.today + relativedelta(day=31, weekday=FR(-1)), date(2003, 9, 26))

    def test_last_day_of_february(self):
        self.assertEqual(date(2021, 2, 1) + relativedelta(day=31), date(2021, 2, 28))

    def test_last_day_of_february_leap_year(self):
        self.assertEqual(date(2020, 2, 1) + relativedelta(day=31), date(2020, 2, 29))

    def test_next_wednesday_is_today(self):
        self.assertEqual(self.today + relativedelta(weekday=WE), date(2003, 9, 17))

    def test_next_wednesday_not_today(self):
        self.assertEqual(self.today + relativedelta(days=+1, weekday=WE), date(2003, 9, 24))

    def test_add_more_than_12months(self):
        self.assertEqual(date(2003, 12, 1) + relativedelta(months=+13), date(2005, 1, 1))

    def test_add_negative_months(self):
        self.assertEqual(date(2003, 1, 1) + relativedelta(months=-2), date(2002, 11, 1))

    def test_15th_iso_year_week(self):
        self.assertEqual(date(2003, 1, 1) + relativedelta(day=4, weeks=+14, weekday=MO(-1)), date(2003, 4, 7))

    def test_millennium_age(self):
        self.assertEqual(
            relativedelta(self.now, date(2001, 1, 1)),
            relativedelta(years=+2, months=+8, days=+16, hours=+20, minutes=+54, seconds=+47, microseconds=+282310),
        )

    def test_john_age(self):
        self.assertEqual(
            relativedelta(self.now, datetime(1978, 4, 5, 12, 0)),
            relativedelta(years=+25, months=+5, days=+12, hours=+8, minutes=+54, seconds=+47, microseconds=+282310),
        )

    def test_john_age_with_date(self):
        self.assertEqual(
            relativedelta(self.today, datetime(1978, 4, 5, 12, 0)),
            relativedelta(years=+25, months=+5, days=+11, hours=+12),
        )

    def test_year_day(self):
        self.assertEqual(date(2003, 1, 1) + relativedelta(yearday=260), date(2003, 9, 17))
        self.assertEqual(date(2002, 1, 1) + relativedelta(yearday=260), date(2002, 9, 17))
        self.assertEqual(date(2000, 1, 1) + relativedelta(yearday=260), date(2000, 9, 16))
        self.assertEqual(self.today + relativedelta(yearday=261), date(2003, 9, 18))

    def test_year_day_bug(self):
        # Tests a problem reported by Adam Ryan.
        self.assertEqual(date(2010, 1, 1) + relativedelta(yearday=15), date(2010, 1, 15))

    def test_non_leap_year_day(self):
        self.assertEqual(date(2003, 1, 1) + relativedelta(nlyearday=260), date(2003, 9, 17))
        self.assertEqual(date(2002, 1, 1) + relativedelta(nlyearday=260), date(2002, 9, 17))
        self.assertEqual(date(2000, 1, 1) + relativedelta(nlyearday=260), date(2000, 9, 17))
        self.assertEqual(self.today + relativedelta(yearday=261), date(2003, 9, 18))

    def test_boolean(self):
        self.assertFalse(relativedelta(days=0))
        self.assertTrue(relativedelta(days=1))

    def test_absolute_value_negative(self):
        rd_base = relativedelta(years=-1, months=-5, days=-2, hours=-3, minutes=-5, seconds=-2, microseconds=-12)
        rd_expected = relativedelta(years=1, months=5, days=2, hours=3, minutes=5, seconds=2, microseconds=12)
        self.assertEqual(abs(rd_base), rd_expected)

    def test_absolute_value_positive(self):
        rd_base = relativedelta(years=1, months=5, days=2, hours=3, minutes=5, seconds=2, microseconds=12)
        self.assertEqual(abs(rd_base), rd_base)

    def test_comparison(self):
        d1 = relativedelta(years=1, months=1, days=1, leapdays=0, hours=1, minutes=1, seconds=1, microseconds=1)
        d2 = relativedelta(years=1, months=1, days=1, leapdays=0, hours=1, minutes=1, seconds=1, microseconds=1)
        d3 = relativedelta(years=1, months=1, days=1, leapdays=0, hours=1, minutes=1, seconds=1, microseconds=2)

        self.assertEqual(d1, d2)
        self.assertNotEqual(d1, d3)

    def test_inequality_type_mismatch(self):
        # Different type
        self.assertFalse(relativedelta(year=1) == 19)

    def test_inequality_unsupported_type(self):
        self.assertIs(relativedelta(hours=3) == NOT_A_VALUE, NOT_A_VALUE)

    def test_inequality_weekdays(self):
        # Different weekdays
        no_wday = relativedelta(year=1997, month=4)
        wday_mo_1 = relativedelta(year=1997, month=4, weekday=MO(+1))
        wday_mo_2 = relativedelta(year=1997, month=4, weekday=MO(+2))
        wday_tu = relativedelta(year=1997, month=4, weekday=TU)

        self.assertTrue(wday_mo_1 == wday_mo_1)  # pylint: disable=r0124

        self.assertFalse(no_wday == wday_mo_1)
        self.assertFalse(wday_mo_1 == no_wday)

        self.assertFalse(wday_mo_1 == wday_mo_2)
        self.assertFalse(wday_mo_2 == wday_mo_1)

        self.assertFalse(wday_mo_1 == wday_tu)
        self.assertFalse(wday_tu == wday_mo_1)

    def test_month_overflow(self):
        self.assertEqual(relativedelta(months=273), relativedelta(years=22, months=9))

    def test_weeks(self):
        # Test that the weeks property is working properly.
        rd = relativedelta(years=4, months=2, weeks=8, days=6)
        self.assertEqual((rd.weeks, rd.days), (8, 8 * 7 + 6))

        rd.weeks = 3
        self.assertEqual((rd.weeks, rd.days), (3, 3 * 7 + 6))

    def test_relative_delta_repr(self):
        self.assertEqual(
            repr(relativedelta(years=1, months=-1, days=15)), "RelativeDelta(years=+1, months=-1, days=+15)"
        )

        self.assertEqual(repr(relativedelta(months=14, seconds=-25)), "RelativeDelta(years=+1, months=+2, seconds=-25)")

        self.assertEqual(
            repr(relativedelta(month=3, hour=3, weekday=SU(3))), "RelativeDelta(month=3, weekday=SU(+3), hour=3)"
        )

    def test_relative_delta_invalid_datetime_object(self):
        with self.assertRaises(TypeError):
            relativedelta(dt1="2018-01-01", dt2="2018-01-02")

        with self.assertRaises(TypeError):
            relativedelta(dt1=datetime(2018, 1, 1), dt2="2018-01-02")

        with self.assertRaises(TypeError):
            relativedelta(dt1="2018-01-01", dt2=datetime(2018, 1, 2))

    def test_invalid_year_day(self):
        with self.assertRaises(ValueError):
            relativedelta(yearday=367)

    def test_add_timedelta_to_unpopulated_relativedelta(self):
        td = timedelta(days=1, seconds=1, microseconds=1, milliseconds=1, minutes=1, hours=1, weeks=1)

        expected = relativedelta(weeks=1, days=1, hours=1, minutes=1, seconds=1, microseconds=1001)

        self.assertEqual(expected, relativedelta() + td)

    def test_add_timedelta_to_populated_relative_delta(self):
        td = timedelta(days=1, seconds=1, microseconds=1, milliseconds=1, minutes=1, hours=1, weeks=1)
        # fmt: off
        rd = relativedelta(
            year=1, month=1, day=1, hour=1, minute=1, second=1, microsecond=1,
            years=1, months=1, days=1, weeks=1, hours=1, minutes=1, seconds=1, microseconds=1,
        )
        expected = relativedelta(
            year=1, month=1, day=1, hour=1, minute=1, second=1, microsecond=1,
            years=1, months=1, weeks=2, days=2, hours=2, minutes=2, seconds=2, microseconds=1002,
        )
        # fmt: on

        self.assertEqual(expected, rd + td)

    def test_hashable(self):
        try:
            {relativedelta(minute=1): "test"}
        except TypeError:
            self.fail("RelativeDelta() failed to hash!")

    def test_day_of_month_plus(self):
        assert [
            date(2021, 1, 28) + relativedelta(months=1),
            date(2021, 2, 27) + relativedelta(months=1),
            date(2021, 4, 29) + relativedelta(months=1),
            date(2021, 5, 30) + relativedelta(months=1),
        ] == [date(2021, 2, 28), date(2021, 3, 27), date(2021, 5, 29), date(2021, 6, 30)]

    def test_last_day_of_month_plus(self):
        assert [
            date(2021, 1, 31) + relativedelta(months=1),
            date(2021, 1, 30) + relativedelta(months=1),
            date(2021, 1, 29) + relativedelta(months=1),
            date(2021, 1, 28) + relativedelta(months=1),
            date(2021, 2, 28) + relativedelta(months=1),
            date(2021, 4, 30) + relativedelta(months=1),
            date(2021, 5, 31) + relativedelta(months=1),
        ] == [
            date(2021, 2, 28),
            date(2021, 2, 28),
            date(2021, 2, 28),
            date(2021, 2, 28),
            date(2021, 3, 28),
            date(2021, 5, 30),
            date(2021, 6, 30),
        ]

    def test_day_of_month_minus(self):
        assert [
            date(2021, 2, 27) - relativedelta(months=1),
            date(2021, 3, 30) - relativedelta(months=1),
            date(2021, 3, 29) - relativedelta(months=1),
            date(2021, 3, 28) - relativedelta(months=1),
            date(2021, 5, 30) - relativedelta(months=1),
            date(2021, 6, 29) - relativedelta(months=1),
        ] == [
            date(2021, 1, 27),
            date(2021, 2, 28),
            date(2021, 2, 28),
            date(2021, 2, 28),
            date(2021, 4, 30),
            date(2021, 5, 29),
        ]

    def test_last_day_of_month_minus(self):
        assert [
            date(2021, 2, 28) - relativedelta(months=1),
            date(2021, 3, 31) - relativedelta(months=1),
            date(2021, 5, 31) - relativedelta(months=1),
            date(2021, 6, 30) - relativedelta(months=1),
        ] == [date(2021, 1, 28), date(2021, 2, 28), date(2021, 4, 30), date(2021, 5, 30)]


class RelativeDeltaOperationTest(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(
            relativedelta(days=10) + relativedelta(years=1, months=2, days=3, hours=4, minutes=5, microseconds=6),
            relativedelta(years=1, months=2, days=13, hours=4, minutes=5, microseconds=6),
        )

    def test_absolute_addition(self):
        self.assertEqual(relativedelta() + relativedelta(day=0, hour=0), relativedelta(day=0, hour=0))
        self.assertEqual(relativedelta(day=0, hour=0) + relativedelta(), relativedelta(day=0, hour=0))

    def test_addition_to_datetime(self):
        self.assertEqual(datetime(2000, 1, 1) + relativedelta(days=1), datetime(2000, 1, 2))

    def test_right_addition_to_datetime(self):
        self.assertEqual(relativedelta(days=1) + datetime(2000, 1, 1), datetime(2000, 1, 2))

    def test_addition_invalid_type(self):
        with self.assertRaises(TypeError):
            _ = relativedelta(days=3) + 9

    def test_addition_unsupported_type(self):
        # For unsupported types that define their own comparators, etc.
        self.assertIs(relativedelta(days=1) + NOT_A_VALUE, NOT_A_VALUE)

    def test_addition_float_value(self):
        self.assertEqual(datetime(2000, 1, 1) + relativedelta(days=1.0), datetime(2000, 1, 2))
        self.assertEqual(datetime(2000, 1, 1) + relativedelta(months=1.0), datetime(2000, 2, 1))
        self.assertEqual(datetime(2000, 1, 1) + relativedelta(years=1.0), datetime(2001, 1, 1))

    def test_addition_float_fractionals(self):
        self.assertEqual(datetime(2000, 1, 1, 0) + relativedelta(days=0.5), datetime(2000, 1, 1, 12))
        self.assertEqual(datetime(2000, 1, 1, 0, 0) + relativedelta(hours=0.5), datetime(2000, 1, 1, 0, 30))
        self.assertEqual(datetime(2000, 1, 1, 0, 0, 0) + relativedelta(minutes=0.5), datetime(2000, 1, 1, 0, 0, 30))
        self.assertEqual(
            datetime(2000, 1, 1, 0, 0, 0, 0) + relativedelta(seconds=0.5), datetime(2000, 1, 1, 0, 0, 0, 500000)
        )
        self.assertEqual(
            datetime(2000, 1, 1, 0, 0, 0, 0) + relativedelta(microseconds=500000.25),
            datetime(2000, 1, 1, 0, 0, 0, 500000),
        )

    def test_subtraction(self):
        self.assertEqual(
            relativedelta(days=10) - relativedelta(years=1, months=2, days=3, hours=4, minutes=5, microseconds=6),
            relativedelta(years=-1, months=-2, days=7, hours=-4, minutes=-5, microseconds=-6),
        )

    def test_right_subtraction_from_datetime(self):
        self.assertEqual(datetime(2000, 1, 2) - relativedelta(days=1), datetime(2000, 1, 1))

    def test_subraction_with_datetime(self):
        self.assertRaises(TypeError, lambda x, y: x - y, (relativedelta(days=1), datetime(2000, 1, 1)))

    def test_subtraction_invalid_type(self):
        with self.assertRaises(TypeError):
            _ = relativedelta(hours=12) - 14

    def test_subtraction_unsupported_type(self):
        self.assertIs(relativedelta(days=1) + NOT_A_VALUE, NOT_A_VALUE)

    def test_multiplication(self):
        self.assertEqual(datetime(2000, 1, 1) + relativedelta(days=1) * 28, datetime(2000, 1, 29))
        self.assertEqual(datetime(2000, 1, 1) + 28 * relativedelta(days=1), datetime(2000, 1, 29))

    def test_multiplication_unsupported_type(self):
        self.assertIs(relativedelta(days=1) * NOT_A_VALUE, NOT_A_VALUE)

    def test_division(self):
        self.assertEqual(datetime(2000, 1, 1) + relativedelta(days=28) / 28, datetime(2000, 1, 2))

    def test_division_unsupported_type(self):
        self.assertIs(relativedelta(days=1) / NOT_A_VALUE, NOT_A_VALUE)


class RelativeDeltaFractionTest(unittest.TestCase):
    def test_relative_delta_fractional_year(self):
        with self.assertRaises(ValueError):
            relativedelta(years=1.5)

    def test_relative_delta_fractional_month(self):
        with self.assertRaises(ValueError):
            relativedelta(months=1.5)

    def test_relative_delta_fractional_absolutes(self):
        # Fractional absolute values will soon be unsupported,
        # check for the deprecation warning.
        with pytest.warns(DeprecationWarning):
            relativedelta(year=2.86)

        with pytest.warns(DeprecationWarning):
            relativedelta(month=1.29)

        with pytest.warns(DeprecationWarning):
            relativedelta(day=0.44)

        with pytest.warns(DeprecationWarning):
            relativedelta(hour=23.98)

        with pytest.warns(DeprecationWarning):
            relativedelta(minute=45.21)

        with pytest.warns(DeprecationWarning):
            relativedelta(second=13.2)

        with pytest.warns(DeprecationWarning):
            relativedelta(microsecond=157221.93)

    def test_relative_delta_fractional_repr(self):
        rd = relativedelta(years=3, months=-2, days=1.25)

        self.assertEqual(repr(rd), "RelativeDelta(years=+3, months=-2, days=+1.25)")

        rd = relativedelta(hours=0.5, seconds=9.22)
        self.assertEqual(repr(rd), "RelativeDelta(hours=+0.5, seconds=+9.22)")

    def test_relative_delta_fractional_weeks(self):
        # Equivalent to days=8, hours=18
        rd = relativedelta(weeks=1.25)
        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd, datetime(2009, 9, 11, 18))

    def test_relative_delta_fractional_days(self):
        rd1 = relativedelta(days=1.48)

        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd1, datetime(2009, 9, 4, 11, 31, 12))

        rd2 = relativedelta(days=1.5)
        self.assertEqual(d1 + rd2, datetime(2009, 9, 4, 12, 0, 0))

    def test_relative_delta_fractional_hours(self):
        rd = relativedelta(days=1, hours=12.5)
        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd, datetime(2009, 9, 4, 12, 30, 0))

    def test_relative_delta_fractional_minutes(self):
        rd = relativedelta(hours=1, minutes=30.5)
        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd, datetime(2009, 9, 3, 1, 30, 30))

    def test_relative_delta_fractional_seconds(self):
        rd = relativedelta(hours=5, minutes=30, seconds=30.5)
        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd, datetime(2009, 9, 3, 5, 30, 30, 500000))

    def test_relative_delta_fractional_positive_overflow(self):
        # Equivalent to (days=1, hours=14)
        rd1 = relativedelta(days=1.5, hours=2)
        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd1, datetime(2009, 9, 4, 14, 0, 0))

        # Equivalent to (days=1, hours=14, minutes=45)
        rd2 = relativedelta(days=1.5, hours=2.5, minutes=15)
        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd2, datetime(2009, 9, 4, 14, 45))

        # Carry back up - equivalent to (days=2, hours=2, minutes=0, seconds=1)
        rd3 = relativedelta(days=1.5, hours=13, minutes=59.5, seconds=31)
        self.assertEqual(d1 + rd3, datetime(2009, 9, 5, 2, 0, 1))

    def test_relative_delta_fractional_negative_days(self):
        # Equivalent to (days=-1, hours=-1)
        rd1 = relativedelta(days=-1.5, hours=11)
        d1 = datetime(2009, 9, 3, 12, 0)
        self.assertEqual(d1 + rd1, datetime(2009, 9, 2, 11, 0, 0))

        # Equivalent to (days=-1, hours=-9)
        rd2 = relativedelta(days=-1.25, hours=-3)
        self.assertEqual(d1 + rd2, datetime(2009, 9, 2, 3))

    def test_relative_delta_normalize_fractional_days(self):
        # Equivalent to (days=2, hours=18)
        rd1 = relativedelta(days=2.75)

        self.assertEqual(rd1.normalized(), relativedelta(days=2, hours=18))

        # Equivalent to (days=1, hours=11, minutes=31, seconds=12)
        rd2 = relativedelta(days=1.48)

        self.assertEqual(rd2.normalized(), relativedelta(days=1, hours=11, minutes=31, seconds=12))

    def test_relative_delta_normalize_fractional_days2(self):
        # Equivalent to (hours=1, minutes=30)
        rd1 = relativedelta(hours=1.5)

        self.assertEqual(rd1.normalized(), relativedelta(hours=1, minutes=30))

        # Equivalent to (hours=3, minutes=17, seconds=5, microseconds=100)
        rd2 = relativedelta(hours=3.28472225)

        self.assertEqual(rd2.normalized(), relativedelta(hours=3, minutes=17, seconds=5, microseconds=100))

    def test_relative_delta_normalize_fractional_minutes(self):
        # Equivalent to (minutes=15, seconds=36)
        rd1 = relativedelta(minutes=15.6)

        self.assertEqual(rd1.normalized(), relativedelta(minutes=15, seconds=36))

        # Equivalent to (minutes=25, seconds=20, microseconds=25000)
        rd2 = relativedelta(minutes=25.33375)

        self.assertEqual(rd2.normalized(), relativedelta(minutes=25, seconds=20, microseconds=25000))

    def test_relative_delta_normalize_fractional_seconds(self):
        # Equivalent to (seconds=45, microseconds=25000)
        rd1 = relativedelta(seconds=45.025)
        self.assertEqual(rd1.normalized(), relativedelta(seconds=45, microseconds=25000))

    def test_relative_delta_fractional_positive_overflow2(self):
        # Equivalent to (days=1, hours=14)
        rd1 = relativedelta(days=1.5, hours=2)
        self.assertEqual(rd1.normalized(), relativedelta(days=1, hours=14))

        # Equivalent to (days=1, hours=14, minutes=45)
        rd2 = relativedelta(days=1.5, hours=2.5, minutes=15)
        self.assertEqual(rd2.normalized(), relativedelta(days=1, hours=14, minutes=45))

        # Carry back up - equivalent to:
        # (days=2, hours=2, minutes=0, seconds=2, microseconds=3)
        rd3 = relativedelta(days=1.5, hours=13, minutes=59.50045, seconds=31.473, microseconds=500003)
        self.assertEqual(rd3.normalized(), relativedelta(days=2, hours=2, minutes=0, seconds=2, microseconds=3))

    def test_relative_delta_fractional_negative_overflow(self):
        # Equivalent to (days=-1)
        rd1 = relativedelta(days=-0.5, hours=-12)
        self.assertEqual(rd1.normalized(), relativedelta(days=-1))

        # Equivalent to (days=-1)
        rd2 = relativedelta(days=-1.5, hours=12)
        self.assertEqual(rd2.normalized(), relativedelta(days=-1))

        # Equivalent to (days=-1, hours=-14, minutes=-45)
        rd3 = relativedelta(days=-1.5, hours=-2.5, minutes=-15)
        self.assertEqual(rd3.normalized(), relativedelta(days=-1, hours=-14, minutes=-45))

        # Equivalent to (days=-1, hours=-14, minutes=+15)
        rd4 = relativedelta(days=-1.5, hours=-2.5, minutes=45)
        self.assertEqual(rd4.normalized(), relativedelta(days=-1, hours=-14, minutes=+15))

        # Carry back up - equivalent to:
        # (days=-2, hours=-2, minutes=0, seconds=-2, microseconds=-3)
        rd3 = relativedelta(days=-1.5, hours=-13, minutes=-59.50045, seconds=-31.473, microseconds=-500003)
        self.assertEqual(rd3.normalized(), relativedelta(days=-2, hours=-2, minutes=0, seconds=-2, microseconds=-3))


class TestRelativeDeltaWeeksProperty:
    # fmt: off
    @pytest.mark.parametrize(
        "days,expected_days,expected_weeks",
        [
            (1, 1, 0), (-1, -1, 0),
            (8, 8, 1), (-8, -8, -1)
        ],
    )
    # fmt: on
    def test_weeks_property_getter(self, days, expected_days, expected_weeks):
        rd = relativedelta(days=days)

        assert rd.days == expected_days
        assert rd.weeks == expected_weeks

    @pytest.mark.parametrize(
        "initial_days,set_weeks,expected_days,expected_weeks",
        [
            (1, 1, 8, 1),  # add 7 days
            (-1, 1, 6, 0),  # add 7 days
            (8, -1, -6, 0),  # change from 1 week, 1 day to -1 week, 1 day
            (-8, -1, -8, -1),  # does not change anything
        ],
    )
    def test_weeks_property_setter(self, initial_days, set_weeks, expected_days, expected_weeks):
        """Test the weeks setter which makes a "smart" update of the days attribute"""
        rd = relativedelta(days=initial_days)
        rd.weeks = set_weeks

        assert rd.days == expected_days
        assert rd.weeks == expected_weeks
