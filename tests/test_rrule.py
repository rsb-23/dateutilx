import unittest
from datetime import date, datetime

import pytest

from dateutilx import tz
from dateutilx.helper import Frequency
from dateutilx.rrule import FR, MO, SU, TH, TU, rrule, rruleset, rrulestr

from .freezegun import freeze_time

MODULE = "dateutilx.rrule"
YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY, MINUTELY, SECONDLY = Frequency

NYC = tz.gettz("America/New_York")
BXL = tz.gettz("Europe/Brussels")


# pylint: disable=r0904
@pytest.mark.rrule
class RRuleTest(unittest.TestCase):
    def _rrulestr_reverse_test(self, rule):
        """
        Call with an `rrule` and it will test that `str(rrule)` generates a
        string which generates the same `rrule` as the input when passed to
        `rrulestr()`
        """
        rr_str = str(rule)
        rrulestr_rrule = rrulestr(rr_str)

        self.assertEqual(list(rule), list(rrulestr_rrule))

    def test_str_append_rrule_token(self):
        # `_rrulestr_reverse_test` does not check if the "RRULE:" prefix
        # property is appended properly, so give it a dedicated test
        self.assertEqual(
            str(rrule(YEARLY, count=5, dtstart=datetime(1997, 9, 2, 9, 0))),
            "DTSTART:19970902T090000\nRRULE:FREQ=YEARLY;COUNT=5",
        )

        rr_str = "DTSTART:19970105T083000\nRRULE:FREQ=YEARLY;INTERVAL=2"
        self.assertEqual(str(rrulestr(rr_str)), rr_str)

    def test_yearly(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1998, 9, 2, 9, 0), datetime(1999, 9, 2, 9, 0)],
        )

    def test_yearly_interval(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1999, 9, 2, 9, 0), datetime(2001, 9, 2, 9, 0)],
        )

    def test_yearly_interval_large(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, interval=100, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(2097, 9, 2, 9, 0), datetime(2197, 9, 2, 9, 0)],
        )

    def test_yearly_by_month(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 2, 9, 0), datetime(1998, 3, 2, 9, 0), datetime(1999, 1, 2, 9, 0)],
        )

    def test_yearly_by_month_day(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 3, 9, 0), datetime(1997, 10, 1, 9, 0), datetime(1997, 10, 3, 9, 0)],
        )

    def test_yearly_by_month_and_month_day(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 5, 9, 0), datetime(1998, 1, 7, 9, 0), datetime(1998, 3, 5, 9, 0)],
        )

    def test_yearly_byweekday(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)],
        )

    def test_yearly_bynweekday(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 25, 9, 0), datetime(1998, 1, 6, 9, 0), datetime(1998, 12, 31, 9, 0)],
        )

    def test_yearly_bynweekday_large(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byweekday=(TU(3), TH(-3)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 11, 9, 0), datetime(1998, 1, 20, 9, 0), datetime(1998, 12, 17, 9, 0)],
        )

    def test_yearly_by_month_and_week_day(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 1, 6, 9, 0), datetime(1998, 1, 8, 9, 0)],
        )

    def test_yearly_by_month_and_nweekday(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 6, 9, 0), datetime(1998, 1, 29, 9, 0), datetime(1998, 3, 3, 9, 0)],
        )

    def test_yearly_by_month_and_nweekday_large(self):
        # This is interesting because the TH(-3) ends up before
        # the TU(3).
        self.assertEqual(
            list(rrule(YEARLY, count=3, bymonth=(1, 3), byweekday=(TU(3), TH(-3)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 15, 9, 0), datetime(1998, 1, 20, 9, 0), datetime(1998, 3, 12, 9, 0)],
        )

    def test_yearly_bymonthday_and_weekday(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 2, 3, 9, 0), datetime(1998, 3, 3, 9, 0)],
        )

    def test_yearly_by_month_and_month_day_and_week_day(self):
        self.assertEqual(
            list(
                rrule(
                    YEARLY,
                    count=3,
                    bymonth=(1, 3),
                    bymonthday=(1, 3),
                    byweekday=(TU, TH),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 3, 3, 9, 0), datetime(2001, 3, 1, 9, 0)],
        )

    def test_yearly_by_year_day(self):
        self.assertEqual(
            list(rrule(YEARLY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 9, 0),
                datetime(1998, 1, 1, 9, 0),
                datetime(1998, 4, 10, 9, 0),
                datetime(1998, 7, 19, 9, 0),
            ],
        )

    def test_yearly_by_year_day_neg(self):
        self.assertEqual(
            list(rrule(YEARLY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 9, 0),
                datetime(1998, 1, 1, 9, 0),
                datetime(1998, 4, 10, 9, 0),
                datetime(1998, 7, 19, 9, 0),
            ],
        )

    def test_yearly_by_month_and_year_day(self):
        self.assertEqual(
            list(
                rrule(YEARLY, count=4, bymonth=(4, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
            ),
            [
                datetime(1998, 4, 10, 9, 0),
                datetime(1998, 7, 19, 9, 0),
                datetime(1999, 4, 10, 9, 0),
                datetime(1999, 7, 19, 9, 0),
            ],
        )

    def test_yearly_by_month_and_year_day_neg(self):
        self.assertEqual(
            list(
                rrule(
                    YEARLY,
                    count=4,
                    bymonth=(4, 7),
                    byyearday=(-365, -266, -166, -1),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [
                datetime(1998, 4, 10, 9, 0),
                datetime(1998, 7, 19, 9, 0),
                datetime(1999, 4, 10, 9, 0),
                datetime(1999, 7, 19, 9, 0),
            ],
        )

    def test_yearly_by_week_no(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 5, 11, 9, 0), datetime(1998, 5, 12, 9, 0), datetime(1998, 5, 13, 9, 0)],
        )

    def test_yearly_by_week_no_and_week_day(self):
        # That's a nice one. The first days of week number one
        # may be in the last year.
        self.assertEqual(
            list(rrule(YEARLY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 29, 9, 0), datetime(1999, 1, 4, 9, 0), datetime(2000, 1, 3, 9, 0)],
        )

    def test_yearly_by_week_no_and_week_day_large(self):
        # Another nice test. The last days of week number 52/53
        # may be in the next year.
        self.assertEqual(
            list(rrule(YEARLY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 9, 0), datetime(1998, 12, 27, 9, 0), datetime(2000, 1, 2, 9, 0)],
        )

    def test_yearly_by_week_no_and_week_day_last(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 9, 0), datetime(1999, 1, 3, 9, 0), datetime(2000, 1, 2, 9, 0)],
        )

    def test_yearly_by_easter(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 12, 9, 0), datetime(1999, 4, 4, 9, 0), datetime(2000, 4, 23, 9, 0)],
        )

    def test_yearly_by_easter_pos(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 13, 9, 0), datetime(1999, 4, 5, 9, 0), datetime(2000, 4, 24, 9, 0)],
        )

    def test_yearly_by_easter_neg(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 11, 9, 0), datetime(1999, 4, 3, 9, 0), datetime(2000, 4, 22, 9, 0)],
        )

    def test_yearly_by_week_no_and_week_day53(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 12, 28, 9, 0), datetime(2004, 12, 27, 9, 0), datetime(2009, 12, 28, 9, 0)],
        )

    def test_yearly_by_hour(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0), datetime(1998, 9, 2, 6, 0), datetime(1998, 9, 2, 18, 0)],
        )

    def test_yearly_by_minute(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6), datetime(1997, 9, 2, 9, 18), datetime(1998, 9, 2, 9, 6)],
        )

    def test_yearly_by_second(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 6), datetime(1997, 9, 2, 9, 0, 18), datetime(1998, 9, 2, 9, 0, 6)],
        )

    def test_yearly_by_hour_and_minute(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 6), datetime(1997, 9, 2, 18, 18), datetime(1998, 9, 2, 6, 6)],
        )

    def test_yearly_by_hour_and_second(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0, 6), datetime(1997, 9, 2, 18, 0, 18), datetime(1998, 9, 2, 6, 0, 6)],
        )

    def test_yearly_by_minute_and_second(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6, 6), datetime(1997, 9, 2, 9, 6, 18), datetime(1997, 9, 2, 9, 18, 6)],
        )

    def test_yearly_by_hour_and_minute_and_second(self):
        self.assertEqual(
            list(
                rrule(
                    YEARLY,
                    count=3,
                    byhour=(6, 18),
                    byminute=(6, 18),
                    bysecond=(6, 18),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1997, 9, 2, 18, 6, 6), datetime(1997, 9, 2, 18, 6, 18), datetime(1997, 9, 2, 18, 18, 6)],
        )

    def test_yearly_by_set_pos(self):
        self.assertEqual(
            list(
                rrule(
                    YEARLY, count=3, bymonthday=15, byhour=(6, 18), bysetpos=(3, -3), dtstart=datetime(1997, 9, 2, 9, 0)
                )
            ),
            [datetime(1997, 11, 15, 18, 0), datetime(1998, 2, 15, 6, 0), datetime(1998, 11, 15, 18, 0)],
        )

    def test_monthly(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 10, 2, 9, 0), datetime(1997, 11, 2, 9, 0)],
        )

    def test_monthly_interval(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 11, 2, 9, 0), datetime(1998, 1, 2, 9, 0)],
        )

    def test_monthly_interval_large(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, interval=18, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1999, 3, 2, 9, 0), datetime(2000, 9, 2, 9, 0)],
        )

    def test_monthly_by_month(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 2, 9, 0), datetime(1998, 3, 2, 9, 0), datetime(1999, 1, 2, 9, 0)],
        )

    def test_monthly_by_month_day(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 3, 9, 0), datetime(1997, 10, 1, 9, 0), datetime(1997, 10, 3, 9, 0)],
        )

    def test_monthly_by_month_and_month_day(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 5, 9, 0), datetime(1998, 1, 7, 9, 0), datetime(1998, 3, 5, 9, 0)],
        )

    def test_monthly_byweekday(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)],
        )

        # Third Monday of the month
        self.assertEqual(
            rrule(MONTHLY, byweekday=(MO(+3)), dtstart=datetime(1997, 9, 1)).between(
                datetime(1997, 9, 1), datetime(1997, 12, 1)
            ),
            [datetime(1997, 9, 15, 0, 0), datetime(1997, 10, 20, 0, 0), datetime(1997, 11, 17, 0, 0)],
        )

    def test_monthly_bynweekday(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 25, 9, 0), datetime(1997, 10, 7, 9, 0)],
        )

    def test_monthly_bynweekday_large(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byweekday=(TU(3), TH(-3)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 11, 9, 0), datetime(1997, 9, 16, 9, 0), datetime(1997, 10, 16, 9, 0)],
        )

    def test_monthly_by_month_and_week_day(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 1, 6, 9, 0), datetime(1998, 1, 8, 9, 0)],
        )

    def test_monthly_by_month_and_nweekday(self):
        self.assertEqual(
            list(
                rrule(MONTHLY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
            ),
            [datetime(1998, 1, 6, 9, 0), datetime(1998, 1, 29, 9, 0), datetime(1998, 3, 3, 9, 0)],
        )

    def test_monthly_by_month_and_nweekday_large(self):
        self.assertEqual(
            list(
                rrule(MONTHLY, count=3, bymonth=(1, 3), byweekday=(TU(3), TH(-3)), dtstart=datetime(1997, 9, 2, 9, 0))
            ),
            [datetime(1998, 1, 15, 9, 0), datetime(1998, 1, 20, 9, 0), datetime(1998, 3, 12, 9, 0)],
        )

    def test_monthly_bymonthday_and_weekday(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 2, 3, 9, 0), datetime(1998, 3, 3, 9, 0)],
        )

    def test_monthly_by_month_and_month_day_and_week_day(self):
        self.assertEqual(
            list(
                rrule(
                    MONTHLY,
                    count=3,
                    bymonth=(1, 3),
                    bymonthday=(1, 3),
                    byweekday=(TU, TH),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 3, 3, 9, 0), datetime(2001, 3, 1, 9, 0)],
        )

    def test_monthly_by_year_day(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 9, 0),
                datetime(1998, 1, 1, 9, 0),
                datetime(1998, 4, 10, 9, 0),
                datetime(1998, 7, 19, 9, 0),
            ],
        )

    def test_monthly_by_year_day_neg(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 9, 0),
                datetime(1998, 1, 1, 9, 0),
                datetime(1998, 4, 10, 9, 0),
                datetime(1998, 7, 19, 9, 0),
            ],
        )

    def test_monthly_by_month_and_year_day(self):
        self.assertEqual(
            list(
                rrule(
                    MONTHLY, count=4, bymonth=(4, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0)
                )
            ),
            [
                datetime(1998, 4, 10, 9, 0),
                datetime(1998, 7, 19, 9, 0),
                datetime(1999, 4, 10, 9, 0),
                datetime(1999, 7, 19, 9, 0),
            ],
        )

    def test_monthly_by_month_and_year_day_neg(self):
        self.assertEqual(
            list(
                rrule(
                    MONTHLY,
                    count=4,
                    bymonth=(4, 7),
                    byyearday=(-365, -266, -166, -1),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [
                datetime(1998, 4, 10, 9, 0),
                datetime(1998, 7, 19, 9, 0),
                datetime(1999, 4, 10, 9, 0),
                datetime(1999, 7, 19, 9, 0),
            ],
        )

    def test_monthly_by_week_no(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 5, 11, 9, 0), datetime(1998, 5, 12, 9, 0), datetime(1998, 5, 13, 9, 0)],
        )

    def test_monthly_by_week_no_and_week_day(self):
        # That's a nice one. The first days of week number one
        # may be in the last year.
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 29, 9, 0), datetime(1999, 1, 4, 9, 0), datetime(2000, 1, 3, 9, 0)],
        )

    def test_monthly_by_week_no_and_week_day_large(self):
        # Another nice test. The last days of week number 52/53
        # may be in the next year.
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 9, 0), datetime(1998, 12, 27, 9, 0), datetime(2000, 1, 2, 9, 0)],
        )

    def test_monthly_by_week_no_and_week_day_last(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 9, 0), datetime(1999, 1, 3, 9, 0), datetime(2000, 1, 2, 9, 0)],
        )

    def test_monthly_by_week_no_and_week_day53(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 12, 28, 9, 0), datetime(2004, 12, 27, 9, 0), datetime(2009, 12, 28, 9, 0)],
        )

    def test_monthly_by_easter(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 12, 9, 0), datetime(1999, 4, 4, 9, 0), datetime(2000, 4, 23, 9, 0)],
        )

    def test_monthly_by_easter_pos(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 13, 9, 0), datetime(1999, 4, 5, 9, 0), datetime(2000, 4, 24, 9, 0)],
        )

    def test_monthly_by_easter_neg(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 11, 9, 0), datetime(1999, 4, 3, 9, 0), datetime(2000, 4, 22, 9, 0)],
        )

    def test_monthly_by_hour(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0), datetime(1997, 10, 2, 6, 0), datetime(1997, 10, 2, 18, 0)],
        )

    def test_monthly_by_minute(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6), datetime(1997, 9, 2, 9, 18), datetime(1997, 10, 2, 9, 6)],
        )

    def test_monthly_by_second(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 6), datetime(1997, 9, 2, 9, 0, 18), datetime(1997, 10, 2, 9, 0, 6)],
        )

    def test_monthly_by_hour_and_minute(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 6), datetime(1997, 9, 2, 18, 18), datetime(1997, 10, 2, 6, 6)],
        )

    def test_monthly_by_hour_and_second(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0, 6), datetime(1997, 9, 2, 18, 0, 18), datetime(1997, 10, 2, 6, 0, 6)],
        )

    def test_monthly_by_minute_and_second(self):
        self.assertEqual(
            list(rrule(MONTHLY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6, 6), datetime(1997, 9, 2, 9, 6, 18), datetime(1997, 9, 2, 9, 18, 6)],
        )

    def test_monthly_by_hour_and_minute_and_second(self):
        self.assertEqual(
            list(
                rrule(
                    MONTHLY,
                    count=3,
                    byhour=(6, 18),
                    byminute=(6, 18),
                    bysecond=(6, 18),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1997, 9, 2, 18, 6, 6), datetime(1997, 9, 2, 18, 6, 18), datetime(1997, 9, 2, 18, 18, 6)],
        )

    def test_monthly_by_set_pos(self):
        self.assertEqual(
            list(
                rrule(
                    MONTHLY,
                    count=3,
                    bymonthday=(13, 17),
                    byhour=(6, 18),
                    bysetpos=(3, -3),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1997, 9, 13, 18, 0), datetime(1997, 9, 17, 6, 0), datetime(1997, 10, 13, 18, 0)],
        )

    def test_weekly(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 9, 9, 0), datetime(1997, 9, 16, 9, 0)],
        )

    def test_weekly_interval(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 16, 9, 0), datetime(1997, 9, 30, 9, 0)],
        )

    def test_weekly_interval_large(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, interval=20, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1998, 1, 20, 9, 0), datetime(1998, 6, 9, 9, 0)],
        )

    def test_weekly_by_month(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 6, 9, 0), datetime(1998, 1, 13, 9, 0), datetime(1998, 1, 20, 9, 0)],
        )

    def test_weekly_by_month_day(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 3, 9, 0), datetime(1997, 10, 1, 9, 0), datetime(1997, 10, 3, 9, 0)],
        )

    def test_weekly_by_month_and_month_day(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 5, 9, 0), datetime(1998, 1, 7, 9, 0), datetime(1998, 3, 5, 9, 0)],
        )

    def test_weekly_byweekday(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)],
        )

    def test_weekly_bynweekday(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)],
        )

    def test_weekly_by_month_and_week_day(self):
        # This test is interesting, because it crosses the year
        # boundary in a weekly period to find day '1' as a
        # valid recurrence.
        self.assertEqual(
            list(rrule(WEEKLY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 1, 6, 9, 0), datetime(1998, 1, 8, 9, 0)],
        )

    def test_weekly_by_month_and_nweekday(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 1, 6, 9, 0), datetime(1998, 1, 8, 9, 0)],
        )

    def test_weekly_bymonthday_and_weekday(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 2, 3, 9, 0), datetime(1998, 3, 3, 9, 0)],
        )

    def test_weekly_by_month_and_month_day_and_week_day(self):
        self.assertEqual(
            list(
                rrule(
                    WEEKLY,
                    count=3,
                    bymonth=(1, 3),
                    bymonthday=(1, 3),
                    byweekday=(TU, TH),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 3, 3, 9, 0), datetime(2001, 3, 1, 9, 0)],
        )

    def test_weekly_by_year_day(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 9, 0),
                datetime(1998, 1, 1, 9, 0),
                datetime(1998, 4, 10, 9, 0),
                datetime(1998, 7, 19, 9, 0),
            ],
        )

    def test_weekly_by_year_day_neg(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 9, 0),
                datetime(1998, 1, 1, 9, 0),
                datetime(1998, 4, 10, 9, 0),
                datetime(1998, 7, 19, 9, 0),
            ],
        )

    def test_weekly_by_month_and_year_day(self):
        self.assertEqual(
            list(
                rrule(WEEKLY, count=4, bymonth=(1, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
            ),
            [
                datetime(1998, 1, 1, 9, 0),
                datetime(1998, 7, 19, 9, 0),
                datetime(1999, 1, 1, 9, 0),
                datetime(1999, 7, 19, 9, 0),
            ],
        )

    def test_weekly_by_month_and_year_day_neg(self):
        self.assertEqual(
            list(
                rrule(
                    WEEKLY,
                    count=4,
                    bymonth=(1, 7),
                    byyearday=(-365, -266, -166, -1),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [
                datetime(1998, 1, 1, 9, 0),
                datetime(1998, 7, 19, 9, 0),
                datetime(1999, 1, 1, 9, 0),
                datetime(1999, 7, 19, 9, 0),
            ],
        )

    def test_weekly_by_week_no(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 5, 11, 9, 0), datetime(1998, 5, 12, 9, 0), datetime(1998, 5, 13, 9, 0)],
        )

    def test_weekly_by_week_no_and_week_day(self):
        # That's a nice one. The first days of week number one
        # may be in the last year.
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 29, 9, 0), datetime(1999, 1, 4, 9, 0), datetime(2000, 1, 3, 9, 0)],
        )

    def test_weekly_by_week_no_and_week_day_large(self):
        # Another nice test. The last days of week number 52/53
        # may be in the next year.
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 9, 0), datetime(1998, 12, 27, 9, 0), datetime(2000, 1, 2, 9, 0)],
        )

    def test_weekly_by_week_no_and_week_day_last(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 9, 0), datetime(1999, 1, 3, 9, 0), datetime(2000, 1, 2, 9, 0)],
        )

    def test_weekly_by_week_no_and_week_day53(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 12, 28, 9, 0), datetime(2004, 12, 27, 9, 0), datetime(2009, 12, 28, 9, 0)],
        )

    def test_weekly_by_easter(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 12, 9, 0), datetime(1999, 4, 4, 9, 0), datetime(2000, 4, 23, 9, 0)],
        )

    def test_weekly_by_easter_pos(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 13, 9, 0), datetime(1999, 4, 5, 9, 0), datetime(2000, 4, 24, 9, 0)],
        )

    def test_weekly_by_easter_neg(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 11, 9, 0), datetime(1999, 4, 3, 9, 0), datetime(2000, 4, 22, 9, 0)],
        )

    def test_weekly_by_hour(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0), datetime(1997, 9, 9, 6, 0), datetime(1997, 9, 9, 18, 0)],
        )

    def test_weekly_by_minute(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6), datetime(1997, 9, 2, 9, 18), datetime(1997, 9, 9, 9, 6)],
        )

    def test_weekly_by_second(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 6), datetime(1997, 9, 2, 9, 0, 18), datetime(1997, 9, 9, 9, 0, 6)],
        )

    def test_weekly_by_hour_and_minute(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 6), datetime(1997, 9, 2, 18, 18), datetime(1997, 9, 9, 6, 6)],
        )

    def test_weekly_by_hour_and_second(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0, 6), datetime(1997, 9, 2, 18, 0, 18), datetime(1997, 9, 9, 6, 0, 6)],
        )

    def test_weekly_by_minute_and_second(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6, 6), datetime(1997, 9, 2, 9, 6, 18), datetime(1997, 9, 2, 9, 18, 6)],
        )

    def test_weekly_by_hour_and_minute_and_second(self):
        self.assertEqual(
            list(
                rrule(
                    WEEKLY,
                    count=3,
                    byhour=(6, 18),
                    byminute=(6, 18),
                    bysecond=(6, 18),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1997, 9, 2, 18, 6, 6), datetime(1997, 9, 2, 18, 6, 18), datetime(1997, 9, 2, 18, 18, 6)],
        )

    def test_weekly_by_set_pos(self):
        self.assertEqual(
            list(
                rrule(
                    WEEKLY,
                    count=3,
                    byweekday=(TU, TH),
                    byhour=(6, 18),
                    bysetpos=(3, -3),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1997, 9, 2, 18, 0), datetime(1997, 9, 4, 6, 0), datetime(1997, 9, 9, 18, 0)],
        )

    def test_daily(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 3, 9, 0), datetime(1997, 9, 4, 9, 0)],
        )

    def test_daily_interval(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 6, 9, 0)],
        )

    def test_daily_interval_large(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, interval=92, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 12, 3, 9, 0), datetime(1998, 3, 5, 9, 0)],
        )

    def test_daily_by_month(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 1, 2, 9, 0), datetime(1998, 1, 3, 9, 0)],
        )

    def test_daily_by_month_day(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 3, 9, 0), datetime(1997, 10, 1, 9, 0), datetime(1997, 10, 3, 9, 0)],
        )

    def test_daily_by_month_and_month_day(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 5, 9, 0), datetime(1998, 1, 7, 9, 0), datetime(1998, 3, 5, 9, 0)],
        )

    def test_daily_byweekday(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)],
        )

    def test_daily_bynweekday(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)],
        )

    def test_daily_by_month_and_week_day(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 1, 6, 9, 0), datetime(1998, 1, 8, 9, 0)],
        )

    def test_daily_by_month_and_nweekday(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 1, 6, 9, 0), datetime(1998, 1, 8, 9, 0)],
        )

    def test_daily_bymonthday_and_weekday(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 2, 3, 9, 0), datetime(1998, 3, 3, 9, 0)],
        )

    def test_daily_by_month_and_month_day_and_week_day(self):
        self.assertEqual(
            list(
                rrule(
                    DAILY,
                    count=3,
                    bymonth=(1, 3),
                    bymonthday=(1, 3),
                    byweekday=(TU, TH),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1998, 1, 1, 9, 0), datetime(1998, 3, 3, 9, 0), datetime(2001, 3, 1, 9, 0)],
        )

    def test_daily_by_year_day(self):
        self.assertEqual(
            list(rrule(DAILY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 9, 0),
                datetime(1998, 1, 1, 9, 0),
                datetime(1998, 4, 10, 9, 0),
                datetime(1998, 7, 19, 9, 0),
            ],
        )

    def test_daily_by_year_day_neg(self):
        self.assertEqual(
            list(rrule(DAILY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 9, 0),
                datetime(1998, 1, 1, 9, 0),
                datetime(1998, 4, 10, 9, 0),
                datetime(1998, 7, 19, 9, 0),
            ],
        )

    def test_daily_by_month_and_year_day(self):
        self.assertEqual(
            list(
                rrule(DAILY, count=4, bymonth=(1, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
            ),
            [
                datetime(1998, 1, 1, 9, 0),
                datetime(1998, 7, 19, 9, 0),
                datetime(1999, 1, 1, 9, 0),
                datetime(1999, 7, 19, 9, 0),
            ],
        )

    def test_daily_by_month_and_year_day_neg(self):
        self.assertEqual(
            list(
                rrule(
                    DAILY, count=4, bymonth=(1, 7), byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0)
                )
            ),
            [
                datetime(1998, 1, 1, 9, 0),
                datetime(1998, 7, 19, 9, 0),
                datetime(1999, 1, 1, 9, 0),
                datetime(1999, 7, 19, 9, 0),
            ],
        )

    def test_daily_by_week_no(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 5, 11, 9, 0), datetime(1998, 5, 12, 9, 0), datetime(1998, 5, 13, 9, 0)],
        )

    def test_daily_by_week_no_and_week_day(self):
        # That's a nice one. The first days of week number one
        # may be in the last year.
        self.assertEqual(
            list(rrule(DAILY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 29, 9, 0), datetime(1999, 1, 4, 9, 0), datetime(2000, 1, 3, 9, 0)],
        )

    def test_daily_by_week_no_and_week_day_large(self):
        # Another nice test. The last days of week number 52/53
        # may be in the next year.
        self.assertEqual(
            list(rrule(DAILY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 9, 0), datetime(1998, 12, 27, 9, 0), datetime(2000, 1, 2, 9, 0)],
        )

    def test_daily_by_week_no_and_week_day_last(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 9, 0), datetime(1999, 1, 3, 9, 0), datetime(2000, 1, 2, 9, 0)],
        )

    def test_daily_by_week_no_and_week_day53(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 12, 28, 9, 0), datetime(2004, 12, 27, 9, 0), datetime(2009, 12, 28, 9, 0)],
        )

    def test_daily_by_easter(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 12, 9, 0), datetime(1999, 4, 4, 9, 0), datetime(2000, 4, 23, 9, 0)],
        )

    def test_daily_by_easter_pos(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 13, 9, 0), datetime(1999, 4, 5, 9, 0), datetime(2000, 4, 24, 9, 0)],
        )

    def test_daily_by_easter_neg(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 11, 9, 0), datetime(1999, 4, 3, 9, 0), datetime(2000, 4, 22, 9, 0)],
        )

    def test_daily_by_hour(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0), datetime(1997, 9, 3, 6, 0), datetime(1997, 9, 3, 18, 0)],
        )

    def test_daily_by_minute(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6), datetime(1997, 9, 2, 9, 18), datetime(1997, 9, 3, 9, 6)],
        )

    def test_daily_by_second(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 6), datetime(1997, 9, 2, 9, 0, 18), datetime(1997, 9, 3, 9, 0, 6)],
        )

    def test_daily_by_hour_and_minute(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 6), datetime(1997, 9, 2, 18, 18), datetime(1997, 9, 3, 6, 6)],
        )

    def test_daily_by_hour_and_second(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0, 6), datetime(1997, 9, 2, 18, 0, 18), datetime(1997, 9, 3, 6, 0, 6)],
        )

    def test_daily_by_minute_and_second(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6, 6), datetime(1997, 9, 2, 9, 6, 18), datetime(1997, 9, 2, 9, 18, 6)],
        )

    def test_daily_by_hour_and_minute_and_second(self):
        self.assertEqual(
            list(
                rrule(
                    DAILY,
                    count=3,
                    byhour=(6, 18),
                    byminute=(6, 18),
                    bysecond=(6, 18),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1997, 9, 2, 18, 6, 6), datetime(1997, 9, 2, 18, 6, 18), datetime(1997, 9, 2, 18, 18, 6)],
        )

    def test_daily_by_set_pos(self):
        self.assertEqual(
            list(
                rrule(
                    DAILY,
                    count=3,
                    byhour=(6, 18),
                    byminute=(15, 45),
                    bysetpos=(3, -3),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1997, 9, 2, 18, 15), datetime(1997, 9, 3, 6, 45), datetime(1997, 9, 3, 18, 15)],
        )

    def test_hourly(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 2, 10, 0), datetime(1997, 9, 2, 11, 0)],
        )

    def test_hourly_interval(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 2, 11, 0), datetime(1997, 9, 2, 13, 0)],
        )

    def test_hourly_interval_large(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, interval=769, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 10, 4, 10, 0), datetime(1997, 11, 5, 11, 0)],
        )

    def test_hourly_by_month(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 0, 0), datetime(1998, 1, 1, 1, 0), datetime(1998, 1, 1, 2, 0)],
        )

    def test_hourly_by_month_day(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 3, 0, 0), datetime(1997, 9, 3, 1, 0), datetime(1997, 9, 3, 2, 0)],
        )

    def test_hourly_by_month_and_month_day(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 5, 0, 0), datetime(1998, 1, 5, 1, 0), datetime(1998, 1, 5, 2, 0)],
        )

    def test_hourly_byweekday(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 2, 10, 0), datetime(1997, 9, 2, 11, 0)],
        )

    def test_hourly_bynweekday(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 2, 10, 0), datetime(1997, 9, 2, 11, 0)],
        )

    def test_hourly_by_month_and_week_day(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 0, 0), datetime(1998, 1, 1, 1, 0), datetime(1998, 1, 1, 2, 0)],
        )

    def test_hourly_by_month_and_nweekday(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 0, 0), datetime(1998, 1, 1, 1, 0), datetime(1998, 1, 1, 2, 0)],
        )

    def test_hourly_bymonthday_and_weekday(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 0, 0), datetime(1998, 1, 1, 1, 0), datetime(1998, 1, 1, 2, 0)],
        )

    def test_hourly_by_month_and_month_day_and_week_day(self):
        self.assertEqual(
            list(
                rrule(
                    HOURLY,
                    count=3,
                    bymonth=(1, 3),
                    bymonthday=(1, 3),
                    byweekday=(TU, TH),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1998, 1, 1, 0, 0), datetime(1998, 1, 1, 1, 0), datetime(1998, 1, 1, 2, 0)],
        )

    def test_hourly_by_year_day(self):
        self.assertEqual(
            list(rrule(HOURLY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 0, 0),
                datetime(1997, 12, 31, 1, 0),
                datetime(1997, 12, 31, 2, 0),
                datetime(1997, 12, 31, 3, 0),
            ],
        )

    def test_hourly_by_year_day_neg(self):
        self.assertEqual(
            list(rrule(HOURLY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 0, 0),
                datetime(1997, 12, 31, 1, 0),
                datetime(1997, 12, 31, 2, 0),
                datetime(1997, 12, 31, 3, 0),
            ],
        )

    def test_hourly_by_month_and_year_day(self):
        self.assertEqual(
            list(
                rrule(HOURLY, count=4, bymonth=(4, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
            ),
            [
                datetime(1998, 4, 10, 0, 0),
                datetime(1998, 4, 10, 1, 0),
                datetime(1998, 4, 10, 2, 0),
                datetime(1998, 4, 10, 3, 0),
            ],
        )

    def test_hourly_by_month_and_year_day_neg(self):
        self.assertEqual(
            list(
                rrule(
                    HOURLY,
                    count=4,
                    bymonth=(4, 7),
                    byyearday=(-365, -266, -166, -1),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [
                datetime(1998, 4, 10, 0, 0),
                datetime(1998, 4, 10, 1, 0),
                datetime(1998, 4, 10, 2, 0),
                datetime(1998, 4, 10, 3, 0),
            ],
        )

    def test_hourly_by_week_no(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 5, 11, 0, 0), datetime(1998, 5, 11, 1, 0), datetime(1998, 5, 11, 2, 0)],
        )

    def test_hourly_by_week_no_and_week_day(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 29, 0, 0), datetime(1997, 12, 29, 1, 0), datetime(1997, 12, 29, 2, 0)],
        )

    def test_hourly_by_week_no_and_week_day_large(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 0, 0), datetime(1997, 12, 28, 1, 0), datetime(1997, 12, 28, 2, 0)],
        )

    def test_hourly_by_week_no_and_week_day_last(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 0, 0), datetime(1997, 12, 28, 1, 0), datetime(1997, 12, 28, 2, 0)],
        )

    def test_hourly_by_week_no_and_week_day53(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 12, 28, 0, 0), datetime(1998, 12, 28, 1, 0), datetime(1998, 12, 28, 2, 0)],
        )

    def test_hourly_by_easter(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 12, 0, 0), datetime(1998, 4, 12, 1, 0), datetime(1998, 4, 12, 2, 0)],
        )

    def test_hourly_by_easter_pos(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 13, 0, 0), datetime(1998, 4, 13, 1, 0), datetime(1998, 4, 13, 2, 0)],
        )

    def test_hourly_by_easter_neg(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 11, 0, 0), datetime(1998, 4, 11, 1, 0), datetime(1998, 4, 11, 2, 0)],
        )

    def test_hourly_by_hour(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0), datetime(1997, 9, 3, 6, 0), datetime(1997, 9, 3, 18, 0)],
        )

    def test_hourly_by_minute(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6), datetime(1997, 9, 2, 9, 18), datetime(1997, 9, 2, 10, 6)],
        )

    def test_hourly_by_second(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 6), datetime(1997, 9, 2, 9, 0, 18), datetime(1997, 9, 2, 10, 0, 6)],
        )

    def test_hourly_by_hour_and_minute(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 6), datetime(1997, 9, 2, 18, 18), datetime(1997, 9, 3, 6, 6)],
        )

    def test_hourly_by_hour_and_second(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0, 6), datetime(1997, 9, 2, 18, 0, 18), datetime(1997, 9, 3, 6, 0, 6)],
        )

    def test_hourly_by_minute_and_second(self):
        self.assertEqual(
            list(rrule(HOURLY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6, 6), datetime(1997, 9, 2, 9, 6, 18), datetime(1997, 9, 2, 9, 18, 6)],
        )

    def test_hourly_by_hour_and_minute_and_second(self):
        self.assertEqual(
            list(
                rrule(
                    HOURLY,
                    count=3,
                    byhour=(6, 18),
                    byminute=(6, 18),
                    bysecond=(6, 18),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1997, 9, 2, 18, 6, 6), datetime(1997, 9, 2, 18, 6, 18), datetime(1997, 9, 2, 18, 18, 6)],
        )

    def test_hourly_by_set_pos(self):
        self.assertEqual(
            list(
                rrule(
                    HOURLY,
                    count=3,
                    byminute=(15, 45),
                    bysecond=(15, 45),
                    bysetpos=(3, -3),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1997, 9, 2, 9, 15, 45), datetime(1997, 9, 2, 9, 45, 15), datetime(1997, 9, 2, 10, 15, 45)],
        )

    def test_minutely(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 2, 9, 1), datetime(1997, 9, 2, 9, 2)],
        )

    def test_minutely_interval(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 2, 9, 2), datetime(1997, 9, 2, 9, 4)],
        )

    def test_minutely_interval_large(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, interval=1501, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 3, 10, 1), datetime(1997, 9, 4, 11, 2)],
        )

    def test_minutely_by_month(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 0, 0), datetime(1998, 1, 1, 0, 1), datetime(1998, 1, 1, 0, 2)],
        )

    def test_minutely_by_month_day(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 3, 0, 0), datetime(1997, 9, 3, 0, 1), datetime(1997, 9, 3, 0, 2)],
        )

    def test_minutely_by_month_and_month_day(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 5, 0, 0), datetime(1998, 1, 5, 0, 1), datetime(1998, 1, 5, 0, 2)],
        )

    def test_minutely_byweekday(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 2, 9, 1), datetime(1997, 9, 2, 9, 2)],
        )

    def test_minutely_bynweekday(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 2, 9, 1), datetime(1997, 9, 2, 9, 2)],
        )

    def test_minutely_by_month_and_week_day(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 0, 0), datetime(1998, 1, 1, 0, 1), datetime(1998, 1, 1, 0, 2)],
        )

    def test_minutely_by_month_and_nweekday(self):
        self.assertEqual(
            list(
                rrule(MINUTELY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
            ),
            [datetime(1998, 1, 1, 0, 0), datetime(1998, 1, 1, 0, 1), datetime(1998, 1, 1, 0, 2)],
        )

    def test_minutely_bymonthday_and_weekday(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 0, 0), datetime(1998, 1, 1, 0, 1), datetime(1998, 1, 1, 0, 2)],
        )

    def test_minutely_by_month_and_month_day_and_week_day(self):
        self.assertEqual(
            list(
                rrule(
                    MINUTELY,
                    count=3,
                    bymonth=(1, 3),
                    bymonthday=(1, 3),
                    byweekday=(TU, TH),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1998, 1, 1, 0, 0), datetime(1998, 1, 1, 0, 1), datetime(1998, 1, 1, 0, 2)],
        )

    def test_minutely_by_year_day(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 0, 0),
                datetime(1997, 12, 31, 0, 1),
                datetime(1997, 12, 31, 0, 2),
                datetime(1997, 12, 31, 0, 3),
            ],
        )

    def test_minutely_by_year_day_neg(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 0, 0),
                datetime(1997, 12, 31, 0, 1),
                datetime(1997, 12, 31, 0, 2),
                datetime(1997, 12, 31, 0, 3),
            ],
        )

    def test_minutely_by_month_and_year_day(self):
        self.assertEqual(
            list(
                rrule(
                    MINUTELY, count=4, bymonth=(4, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0)
                )
            ),
            [
                datetime(1998, 4, 10, 0, 0),
                datetime(1998, 4, 10, 0, 1),
                datetime(1998, 4, 10, 0, 2),
                datetime(1998, 4, 10, 0, 3),
            ],
        )

    def test_minutely_by_month_and_year_day_neg(self):
        self.assertEqual(
            list(
                rrule(
                    MINUTELY,
                    count=4,
                    bymonth=(4, 7),
                    byyearday=(-365, -266, -166, -1),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [
                datetime(1998, 4, 10, 0, 0),
                datetime(1998, 4, 10, 0, 1),
                datetime(1998, 4, 10, 0, 2),
                datetime(1998, 4, 10, 0, 3),
            ],
        )

    def test_minutely_by_week_no(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 5, 11, 0, 0), datetime(1998, 5, 11, 0, 1), datetime(1998, 5, 11, 0, 2)],
        )

    def test_minutely_by_week_no_and_week_day(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 29, 0, 0), datetime(1997, 12, 29, 0, 1), datetime(1997, 12, 29, 0, 2)],
        )

    def test_minutely_by_week_no_and_week_day_large(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 0, 0), datetime(1997, 12, 28, 0, 1), datetime(1997, 12, 28, 0, 2)],
        )

    def test_minutely_by_week_no_and_week_day_last(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 0, 0), datetime(1997, 12, 28, 0, 1), datetime(1997, 12, 28, 0, 2)],
        )

    def test_minutely_by_week_no_and_week_day53(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 12, 28, 0, 0), datetime(1998, 12, 28, 0, 1), datetime(1998, 12, 28, 0, 2)],
        )

    def test_minutely_by_easter(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 12, 0, 0), datetime(1998, 4, 12, 0, 1), datetime(1998, 4, 12, 0, 2)],
        )

    def test_minutely_by_easter_pos(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 13, 0, 0), datetime(1998, 4, 13, 0, 1), datetime(1998, 4, 13, 0, 2)],
        )

    def test_minutely_by_easter_neg(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 11, 0, 0), datetime(1998, 4, 11, 0, 1), datetime(1998, 4, 11, 0, 2)],
        )

    def test_minutely_by_hour(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0), datetime(1997, 9, 2, 18, 1), datetime(1997, 9, 2, 18, 2)],
        )

    def test_minutely_by_minute(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6), datetime(1997, 9, 2, 9, 18), datetime(1997, 9, 2, 10, 6)],
        )

    def test_minutely_by_second(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 6), datetime(1997, 9, 2, 9, 0, 18), datetime(1997, 9, 2, 9, 1, 6)],
        )

    def test_minutely_by_hour_and_minute(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 6), datetime(1997, 9, 2, 18, 18), datetime(1997, 9, 3, 6, 6)],
        )

    def test_minutely_by_hour_and_second(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0, 6), datetime(1997, 9, 2, 18, 0, 18), datetime(1997, 9, 2, 18, 1, 6)],
        )

    def test_minutely_by_minute_and_second(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6, 6), datetime(1997, 9, 2, 9, 6, 18), datetime(1997, 9, 2, 9, 18, 6)],
        )

    def test_minutely_by_hour_and_minute_and_second(self):
        self.assertEqual(
            list(
                rrule(
                    MINUTELY,
                    count=3,
                    byhour=(6, 18),
                    byminute=(6, 18),
                    bysecond=(6, 18),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1997, 9, 2, 18, 6, 6), datetime(1997, 9, 2, 18, 6, 18), datetime(1997, 9, 2, 18, 18, 6)],
        )

    def test_minutely_by_set_pos(self):
        self.assertEqual(
            list(rrule(MINUTELY, count=3, bysecond=(15, 30, 45), bysetpos=(3, -3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 15), datetime(1997, 9, 2, 9, 0, 45), datetime(1997, 9, 2, 9, 1, 15)],
        )

    def test_secondly(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 0), datetime(1997, 9, 2, 9, 0, 1), datetime(1997, 9, 2, 9, 0, 2)],
        )

    def test_secondly_interval(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 0), datetime(1997, 9, 2, 9, 0, 2), datetime(1997, 9, 2, 9, 0, 4)],
        )

    def test_secondly_interval_large(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, interval=90061, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 0), datetime(1997, 9, 3, 10, 1, 1), datetime(1997, 9, 4, 11, 2, 2)],
        )

    def test_secondly_by_month(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 0, 0, 0), datetime(1998, 1, 1, 0, 0, 1), datetime(1998, 1, 1, 0, 0, 2)],
        )

    def test_secondly_by_month_day(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 3, 0, 0, 0), datetime(1997, 9, 3, 0, 0, 1), datetime(1997, 9, 3, 0, 0, 2)],
        )

    def test_secondly_by_month_and_month_day(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 5, 0, 0, 0), datetime(1998, 1, 5, 0, 0, 1), datetime(1998, 1, 5, 0, 0, 2)],
        )

    def test_secondly_byweekday(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 0), datetime(1997, 9, 2, 9, 0, 1), datetime(1997, 9, 2, 9, 0, 2)],
        )

    def test_secondly_bynweekday(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 0), datetime(1997, 9, 2, 9, 0, 1), datetime(1997, 9, 2, 9, 0, 2)],
        )

    def test_secondly_by_month_and_week_day(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 0, 0, 0), datetime(1998, 1, 1, 0, 0, 1), datetime(1998, 1, 1, 0, 0, 2)],
        )

    def test_secondly_by_month_and_nweekday(self):
        self.assertEqual(
            list(
                rrule(SECONDLY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
            ),
            [datetime(1998, 1, 1, 0, 0, 0), datetime(1998, 1, 1, 0, 0, 1), datetime(1998, 1, 1, 0, 0, 2)],
        )

    def test_secondly_bymonthday_and_weekday(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 1, 1, 0, 0, 0), datetime(1998, 1, 1, 0, 0, 1), datetime(1998, 1, 1, 0, 0, 2)],
        )

    def test_secondly_by_month_and_month_day_and_week_day(self):
        self.assertEqual(
            list(
                rrule(
                    SECONDLY,
                    count=3,
                    bymonth=(1, 3),
                    bymonthday=(1, 3),
                    byweekday=(TU, TH),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1998, 1, 1, 0, 0, 0), datetime(1998, 1, 1, 0, 0, 1), datetime(1998, 1, 1, 0, 0, 2)],
        )

    def test_secondly_by_year_day(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 0, 0, 0),
                datetime(1997, 12, 31, 0, 0, 1),
                datetime(1997, 12, 31, 0, 0, 2),
                datetime(1997, 12, 31, 0, 0, 3),
            ],
        )

    def test_secondly_by_year_day_neg(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))),
            [
                datetime(1997, 12, 31, 0, 0, 0),
                datetime(1997, 12, 31, 0, 0, 1),
                datetime(1997, 12, 31, 0, 0, 2),
                datetime(1997, 12, 31, 0, 0, 3),
            ],
        )

    def test_secondly_by_month_and_year_day(self):
        self.assertEqual(
            list(
                rrule(
                    SECONDLY, count=4, bymonth=(4, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0)
                )
            ),
            [
                datetime(1998, 4, 10, 0, 0, 0),
                datetime(1998, 4, 10, 0, 0, 1),
                datetime(1998, 4, 10, 0, 0, 2),
                datetime(1998, 4, 10, 0, 0, 3),
            ],
        )

    def test_secondly_by_month_and_year_day_neg(self):
        self.assertEqual(
            list(
                rrule(
                    SECONDLY,
                    count=4,
                    bymonth=(4, 7),
                    byyearday=(-365, -266, -166, -1),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [
                datetime(1998, 4, 10, 0, 0, 0),
                datetime(1998, 4, 10, 0, 0, 1),
                datetime(1998, 4, 10, 0, 0, 2),
                datetime(1998, 4, 10, 0, 0, 3),
            ],
        )

    def test_secondly_by_week_no(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 5, 11, 0, 0, 0), datetime(1998, 5, 11, 0, 0, 1), datetime(1998, 5, 11, 0, 0, 2)],
        )

    def test_secondly_by_week_no_and_week_day(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 29, 0, 0, 0), datetime(1997, 12, 29, 0, 0, 1), datetime(1997, 12, 29, 0, 0, 2)],
        )

    def test_secondly_by_week_no_and_week_day_large(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 0, 0, 0), datetime(1997, 12, 28, 0, 0, 1), datetime(1997, 12, 28, 0, 0, 2)],
        )

    def test_secondly_by_week_no_and_week_day_last(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 12, 28, 0, 0, 0), datetime(1997, 12, 28, 0, 0, 1), datetime(1997, 12, 28, 0, 0, 2)],
        )

    def test_secondly_by_week_no_and_week_day53(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 12, 28, 0, 0, 0), datetime(1998, 12, 28, 0, 0, 1), datetime(1998, 12, 28, 0, 0, 2)],
        )

    def test_secondly_by_easter(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 12, 0, 0, 0), datetime(1998, 4, 12, 0, 0, 1), datetime(1998, 4, 12, 0, 0, 2)],
        )

    def test_secondly_by_easter_pos(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 13, 0, 0, 0), datetime(1998, 4, 13, 0, 0, 1), datetime(1998, 4, 13, 0, 0, 2)],
        )

    def test_secondly_by_easter_neg(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1998, 4, 11, 0, 0, 0), datetime(1998, 4, 11, 0, 0, 1), datetime(1998, 4, 11, 0, 0, 2)],
        )

    def test_secondly_by_hour(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0, 0), datetime(1997, 9, 2, 18, 0, 1), datetime(1997, 9, 2, 18, 0, 2)],
        )

    def test_secondly_by_minute(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6, 0), datetime(1997, 9, 2, 9, 6, 1), datetime(1997, 9, 2, 9, 6, 2)],
        )

    def test_secondly_by_second(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0, 6), datetime(1997, 9, 2, 9, 0, 18), datetime(1997, 9, 2, 9, 1, 6)],
        )

    def test_secondly_by_hour_and_minute(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 6, 0), datetime(1997, 9, 2, 18, 6, 1), datetime(1997, 9, 2, 18, 6, 2)],
        )

    def test_secondly_by_hour_and_second(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 18, 0, 6), datetime(1997, 9, 2, 18, 0, 18), datetime(1997, 9, 2, 18, 1, 6)],
        )

    def test_secondly_by_minute_and_second(self):
        self.assertEqual(
            list(rrule(SECONDLY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 6, 6), datetime(1997, 9, 2, 9, 6, 18), datetime(1997, 9, 2, 9, 18, 6)],
        )

    def test_secondly_by_hour_and_minute_and_second(self):
        self.assertEqual(
            list(
                rrule(
                    SECONDLY,
                    count=3,
                    byhour=(6, 18),
                    byminute=(6, 18),
                    bysecond=(6, 18),
                    dtstart=datetime(1997, 9, 2, 9, 0),
                )
            ),
            [datetime(1997, 9, 2, 18, 6, 6), datetime(1997, 9, 2, 18, 6, 18), datetime(1997, 9, 2, 18, 18, 6)],
        )

    def test_secondly_by_hour_and_minute_and_second_bug(self):
        # This explores a bug found by Mathieu Bridon.
        self.assertEqual(
            list(rrule(SECONDLY, count=3, bysecond=(0,), byminute=(1,), dtstart=datetime(2010, 3, 22, 12, 1))),
            [datetime(2010, 3, 22, 12, 1), datetime(2010, 3, 22, 13, 1), datetime(2010, 3, 22, 14, 1)],
        )

    def test_hourly_bad_rrule(self):
        """
        When `byhour` is specified with `freq=HOURLY`, there are certain
        combinations of `dtstart` and `byhour` which result in an rrule with no
        valid values.

        See https://github.com/dateutil/dateutil/issues/4
        """

        self.assertRaises(
            ValueError, rrule, HOURLY, interval=4, byhour=(7, 11, 15, 19), dtstart=datetime(1997, 9, 2, 9, 0)
        )

    def test_minutely_bad_rrule(self):
        """
        See :func:`testHourlyBadRRule` for details.
        """

        self.assertRaises(
            ValueError, rrule, MINUTELY, interval=12, byminute=(10, 11, 25, 39, 50), dtstart=datetime(1997, 9, 2, 9, 0)
        )

    def test_secondly_bad_rrule(self):
        """
        See :func:`testHourlyBadRRule` for details.
        """

        self.assertRaises(
            ValueError, rrule, SECONDLY, interval=10, bysecond=(2, 15, 37, 42, 59), dtstart=datetime(1997, 9, 2, 9, 0)
        )

    def test_minutely_bad_combo_rrule(self):
        """
        Certain values of :param:`interval` in :class:`rrule`, when combined
        with certain values of :param:`byhour` create rules which apply to no
        valid dates. The library should detect this case in the iterator and
        raise a :exception:`ValueError`.
        """

        with pytest.raises(ValueError):
            list(rrule(MINUTELY, interval=120, byhour=(10, 12, 14, 16), count=2, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_secondly_bad_combo_rrule(self):
        """
        See :func:`testMinutelyBadComboRRule' for details.
        """

        with pytest.raises(ValueError):
            list(rrule(SECONDLY, interval=360, byminute=(10, 28, 49), count=4, dtstart=datetime(1997, 9, 2, 9, 0)))

        with pytest.raises(ValueError):
            list(rrule(SECONDLY, interval=43200, byhour=(2, 10, 18, 23), count=4, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_bad_until_count_rrule(self):
        """
        See rfc-5545 3.3.10 - This checks for the deprecation warning, and will
        eventually check for an error.
        """
        with pytest.warns(DeprecationWarning):
            rrule(DAILY, dtstart=datetime(1997, 9, 2, 9, 0), count=3, until=datetime(1997, 9, 4, 9, 0))

    def test_until_not_matching(self):
        self.assertEqual(
            list(rrule(DAILY, dtstart=datetime(1997, 9, 2, 9, 0), until=datetime(1997, 9, 5, 8, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 3, 9, 0), datetime(1997, 9, 4, 9, 0)],
        )

    def test_until_matching(self):
        self.assertEqual(
            list(rrule(DAILY, dtstart=datetime(1997, 9, 2, 9, 0), until=datetime(1997, 9, 4, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 3, 9, 0), datetime(1997, 9, 4, 9, 0)],
        )

    def test_until_single(self):
        self.assertEqual(
            list(rrule(DAILY, dtstart=datetime(1997, 9, 2, 9, 0), until=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0)],
        )

    def test_until_empty(self):
        self.assertEqual(list(rrule(DAILY, dtstart=datetime(1997, 9, 2, 9, 0), until=datetime(1997, 9, 1, 9, 0))), [])

    def test_until_with_date(self):
        self.assertEqual(
            list(rrule(DAILY, dtstart=datetime(1997, 9, 2, 9, 0), until=date(1997, 9, 5))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 3, 9, 0), datetime(1997, 9, 4, 9, 0)],
        )

    def test_wkst_interval_mo(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, interval=2, byweekday=(TU, SU), wkst=MO, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 7, 9, 0), datetime(1997, 9, 16, 9, 0)],
        )

    def test_wkst_interval_su(self):
        self.assertEqual(
            list(rrule(WEEKLY, count=3, interval=2, byweekday=(TU, SU), wkst=SU, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 14, 9, 0), datetime(1997, 9, 16, 9, 0)],
        )

    def test_dtstart_is_date(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, dtstart=date(1997, 9, 2))),
            [datetime(1997, 9, 2, 0, 0), datetime(1997, 9, 3, 0, 0), datetime(1997, 9, 4, 0, 0)],
        )

    def test_dtstart_with_microseconds(self):
        self.assertEqual(
            list(rrule(DAILY, count=3, dtstart=datetime(1997, 9, 2, 9, 0, 0, 500000))),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 3, 9, 0), datetime(1997, 9, 4, 9, 0)],
        )

    def test_max_year(self):
        self.assertEqual(
            list(rrule(YEARLY, count=3, bymonth=2, bymonthday=31, dtstart=datetime(9997, 9, 2, 9, 0, 0))), []
        )

    def test_get_item(self):
        self.assertEqual(rrule(DAILY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))[0], datetime(1997, 9, 2, 9, 0))

    def test_get_item_neg(self):
        self.assertEqual(rrule(DAILY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))[-1], datetime(1997, 9, 4, 9, 0))

    def test_get_item_slice(self):
        self.assertEqual(
            rrule(
                DAILY,
                # count=3,
                dtstart=datetime(1997, 9, 2, 9, 0),
            )[1:2],
            [datetime(1997, 9, 3, 9, 0)],
        )

    def test_get_item_slice_empty(self):
        self.assertEqual(
            rrule(DAILY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))[:],
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 3, 9, 0), datetime(1997, 9, 4, 9, 0)],
        )

    def test_get_item_slice_step(self):
        self.assertEqual(
            rrule(DAILY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))[::-2],
            [datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 2, 9, 0)],
        )

    def test_count(self):
        self.assertEqual(rrule(DAILY, count=3, dtstart=datetime(1997, 9, 2, 9, 0)).count(), 3)

    def test_count_zero(self):
        self.assertEqual(rrule(YEARLY, count=0, dtstart=datetime(1997, 9, 2, 9, 0)).count(), 0)

    def test_contains(self):
        rr = rrule(DAILY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))
        self.assertEqual(datetime(1997, 9, 3, 9, 0) in rr, True)

    def test_contains_not(self):
        rr = rrule(DAILY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))
        self.assertEqual(datetime(1997, 9, 3, 9, 0) not in rr, False)

    def test_before(self):
        self.assertEqual(
            rrule(DAILY, dtstart=datetime(1997, 9, 2, 9, 0)).before(datetime(1997, 9, 5, 9, 0)),  # count=5
            datetime(1997, 9, 4, 9, 0),
        )

    def test_before_inc(self):
        self.assertEqual(
            rrule(
                DAILY,
                # count=5,
                dtstart=datetime(1997, 9, 2, 9, 0),
            ).before(datetime(1997, 9, 5, 9, 0), inc=True),
            datetime(1997, 9, 5, 9, 0),
        )

    def test_after(self):
        self.assertEqual(
            rrule(
                DAILY,
                # count=5,
                dtstart=datetime(1997, 9, 2, 9, 0),
            ).after(datetime(1997, 9, 4, 9, 0)),
            datetime(1997, 9, 5, 9, 0),
        )

    def test_after_inc(self):
        self.assertEqual(
            rrule(
                DAILY,
                # count=5,
                dtstart=datetime(1997, 9, 2, 9, 0),
            ).after(datetime(1997, 9, 4, 9, 0), inc=True),
            datetime(1997, 9, 4, 9, 0),
        )

    def test_xafter(self):
        self.assertEqual(
            list(rrule(DAILY, dtstart=datetime(1997, 9, 2, 9, 0)).xafter(datetime(1997, 9, 8, 9, 0), count=12)),
            [
                datetime(1997, 9, 9, 9, 0),
                datetime(1997, 9, 10, 9, 0),
                datetime(1997, 9, 11, 9, 0),
                datetime(1997, 9, 12, 9, 0),
                datetime(1997, 9, 13, 9, 0),
                datetime(1997, 9, 14, 9, 0),
                datetime(1997, 9, 15, 9, 0),
                datetime(1997, 9, 16, 9, 0),
                datetime(1997, 9, 17, 9, 0),
                datetime(1997, 9, 18, 9, 0),
                datetime(1997, 9, 19, 9, 0),
                datetime(1997, 9, 20, 9, 0),
            ],
        )

    def test_xafter_inc(self):
        self.assertEqual(
            list(
                rrule(DAILY, dtstart=datetime(1997, 9, 2, 9, 0)).xafter(datetime(1997, 9, 8, 9, 0), count=12, inc=True)
            ),
            [
                datetime(1997, 9, 8, 9, 0),
                datetime(1997, 9, 9, 9, 0),
                datetime(1997, 9, 10, 9, 0),
                datetime(1997, 9, 11, 9, 0),
                datetime(1997, 9, 12, 9, 0),
                datetime(1997, 9, 13, 9, 0),
                datetime(1997, 9, 14, 9, 0),
                datetime(1997, 9, 15, 9, 0),
                datetime(1997, 9, 16, 9, 0),
                datetime(1997, 9, 17, 9, 0),
                datetime(1997, 9, 18, 9, 0),
                datetime(1997, 9, 19, 9, 0),
            ],
        )

    def test_between(self):
        self.assertEqual(
            rrule(
                DAILY,
                # count=5,
                dtstart=datetime(1997, 9, 2, 9, 0),
            ).between(datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 6, 9, 0)),
            [datetime(1997, 9, 3, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 5, 9, 0)],
        )

    def test_between_inc(self):
        self.assertEqual(
            rrule(
                DAILY,
                # count=5,
                dtstart=datetime(1997, 9, 2, 9, 0),
            ).between(datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 6, 9, 0), inc=True),
            [
                datetime(1997, 9, 2, 9, 0),
                datetime(1997, 9, 3, 9, 0),
                datetime(1997, 9, 4, 9, 0),
                datetime(1997, 9, 5, 9, 0),
                datetime(1997, 9, 6, 9, 0),
            ],
        )

    def test_cache_pre(self):
        rr = rrule(DAILY, count=15, cache=True, dtstart=datetime(1997, 9, 2, 9, 0))
        self.assertEqual(
            list(rr),
            [
                datetime(1997, 9, 2, 9, 0),
                datetime(1997, 9, 3, 9, 0),
                datetime(1997, 9, 4, 9, 0),
                datetime(1997, 9, 5, 9, 0),
                datetime(1997, 9, 6, 9, 0),
                datetime(1997, 9, 7, 9, 0),
                datetime(1997, 9, 8, 9, 0),
                datetime(1997, 9, 9, 9, 0),
                datetime(1997, 9, 10, 9, 0),
                datetime(1997, 9, 11, 9, 0),
                datetime(1997, 9, 12, 9, 0),
                datetime(1997, 9, 13, 9, 0),
                datetime(1997, 9, 14, 9, 0),
                datetime(1997, 9, 15, 9, 0),
                datetime(1997, 9, 16, 9, 0),
            ],
        )

    def test_cache_post(self):
        rr = rrule(DAILY, count=15, cache=True, dtstart=datetime(1997, 9, 2, 9, 0))
        for _ in rr:
            pass
        self.assertEqual(
            list(rr),
            [
                datetime(1997, 9, 2, 9, 0),
                datetime(1997, 9, 3, 9, 0),
                datetime(1997, 9, 4, 9, 0),
                datetime(1997, 9, 5, 9, 0),
                datetime(1997, 9, 6, 9, 0),
                datetime(1997, 9, 7, 9, 0),
                datetime(1997, 9, 8, 9, 0),
                datetime(1997, 9, 9, 9, 0),
                datetime(1997, 9, 10, 9, 0),
                datetime(1997, 9, 11, 9, 0),
                datetime(1997, 9, 12, 9, 0),
                datetime(1997, 9, 13, 9, 0),
                datetime(1997, 9, 14, 9, 0),
                datetime(1997, 9, 15, 9, 0),
                datetime(1997, 9, 16, 9, 0),
            ],
        )

    def test_cache_post_internal(self):
        rr = rrule(DAILY, count=15, cache=True, dtstart=datetime(1997, 9, 2, 9, 0))
        for _ in rr:
            pass
        self.assertEqual(
            rr._cache,
            [
                datetime(1997, 9, 2, 9, 0),
                datetime(1997, 9, 3, 9, 0),
                datetime(1997, 9, 4, 9, 0),
                datetime(1997, 9, 5, 9, 0),
                datetime(1997, 9, 6, 9, 0),
                datetime(1997, 9, 7, 9, 0),
                datetime(1997, 9, 8, 9, 0),
                datetime(1997, 9, 9, 9, 0),
                datetime(1997, 9, 10, 9, 0),
                datetime(1997, 9, 11, 9, 0),
                datetime(1997, 9, 12, 9, 0),
                datetime(1997, 9, 13, 9, 0),
                datetime(1997, 9, 14, 9, 0),
                datetime(1997, 9, 15, 9, 0),
                datetime(1997, 9, 16, 9, 0),
            ],
        )

    def test_cache_pre_contains(self):
        rr = rrule(DAILY, count=3, cache=True, dtstart=datetime(1997, 9, 2, 9, 0))
        self.assertEqual(datetime(1997, 9, 3, 9, 0) in rr, True)

    def test_cache_post_contains(self):
        rr = rrule(DAILY, count=3, cache=True, dtstart=datetime(1997, 9, 2, 9, 0))
        for _ in rr:
            pass
        self.assertEqual(datetime(1997, 9, 3, 9, 0) in rr, True)

    def test_str(self):
        self.assertEqual(
            list(rrulestr("DTSTART:19970902T090000\nRRULE:FREQ=YEARLY;COUNT=3\n")),
            [datetime(1997, 9, 2, 9, 0), datetime(1998, 9, 2, 9, 0), datetime(1999, 9, 2, 9, 0)],
        )

    def test_str_with_tzid(self):
        self.assertEqual(
            list(rrulestr("DTSTART;TZID=America/New_York:19970902T090000\nRRULE:FREQ=YEARLY;COUNT=3\n")),
            [
                datetime(1997, 9, 2, 9, 0, tzinfo=NYC),
                datetime(1998, 9, 2, 9, 0, tzinfo=NYC),
                datetime(1999, 9, 2, 9, 0, tzinfo=NYC),
            ],
        )

    def test_str_with_tzid_mapping(self):
        rrstr = "DTSTART;TZID=Eastern:19970902T090000\n" + "RRULE:FREQ=YEARLY;COUNT=3"

        rr = rrulestr(rrstr, tzids={"Eastern": NYC})
        exp = [
            datetime(1997, 9, 2, 9, 0, tzinfo=NYC),
            datetime(1998, 9, 2, 9, 0, tzinfo=NYC),
            datetime(1999, 9, 2, 9, 0, tzinfo=NYC),
        ]

        self.assertEqual(list(rr), exp)

    def test_str_with_tzid_callable(self):
        rrstr = "DTSTART;TZID=UTC+04:19970902T090000\n" + "RRULE:FREQ=YEARLY;COUNT=3"

        tz_ = tz.tzstr("UTC+04")

        def parse_tzstr(tzstr):
            if tzstr is None:
                raise ValueError("Invalid tzstr")

            return tz.tzstr(tzstr)

        rr = rrulestr(rrstr, tzids=parse_tzstr)

        exp = [
            datetime(1997, 9, 2, 9, 0, tzinfo=tz_),
            datetime(1998, 9, 2, 9, 0, tzinfo=tz_),
            datetime(1999, 9, 2, 9, 0, tzinfo=tz_),
        ]

        self.assertEqual(list(rr), exp)

    def test_str_with_tzid_callable_failure(self):
        rrstr = "DTSTART;TZID=America/New_York:19970902T090000\n" + "RRULE:FREQ=YEARLY;COUNT=3"

        class TzInfoError(Exception):
            pass

        def tzinfos(tzstr):
            if tzstr == "America/New_York":
                raise TzInfoError("Invalid!")

        with self.assertRaises(TzInfoError):
            rrulestr(rrstr, tzids=tzinfos)

    def test_str_with_conflicting_tzid(self):
        # RFC 5545 Section 3.3.5, FORM #2: DATE WITH UTC TIME
        # https://tools.ietf.org/html/rfc5545#section-3.3.5
        # The "TZID" property parameter MUST NOT be applied to DATE-TIME
        with self.assertRaises(ValueError):
            rrulestr("DTSTART;TZID=America/New_York:19970902T090000Z\n" + "RRULE:FREQ=YEARLY;COUNT=3\n")

    def test_str_type(self):
        self.assertEqual(isinstance(rrulestr("DTSTART:19970902T090000\nRRULE:FREQ=YEARLY;COUNT=3\n"), rrule), True)

    def test_str_force_set_type(self):
        self.assertEqual(
            isinstance(rrulestr("DTSTART:19970902T090000\nRRULE:FREQ=YEARLY;COUNT=3\n", forceset=True), rruleset), True
        )

    def test_str_set_type(self):
        self.assertEqual(
            isinstance(
                rrulestr(
                    "DTSTART:19970902T090000\nRRULE:FREQ=YEARLY;COUNT=2;BYDAY=TU\nRRULE:FREQ=YEARLY;COUNT=1;BYDAY=TH\n"
                ),
                rruleset,
            ),
            True,
        )

    def test_str_case(self):
        self.assertEqual(
            list(rrulestr("dtstart:19970902T090000\nrrule:freq=yearly;count=3\n")),
            [datetime(1997, 9, 2, 9, 0), datetime(1998, 9, 2, 9, 0), datetime(1999, 9, 2, 9, 0)],
        )

    def test_str_spaces(self):
        self.assertEqual(
            list(rrulestr(" DTSTART:19970902T090000  RRULE:FREQ=YEARLY;COUNT=3 ")),
            [datetime(1997, 9, 2, 9, 0), datetime(1998, 9, 2, 9, 0), datetime(1999, 9, 2, 9, 0)],
        )

    def test_str_spaces_and_lines(self):
        self.assertEqual(
            list(rrulestr(" DTSTART:19970902T090000 \n \n RRULE:FREQ=YEARLY;COUNT=3 \n")),
            [datetime(1997, 9, 2, 9, 0), datetime(1998, 9, 2, 9, 0), datetime(1999, 9, 2, 9, 0)],
        )

    def test_str_no_dtstart(self):
        self.assertEqual(
            list(rrulestr("RRULE:FREQ=YEARLY;COUNT=3\n", dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1998, 9, 2, 9, 0), datetime(1999, 9, 2, 9, 0)],
        )

    def test_str_value_only(self):
        self.assertEqual(
            list(rrulestr("FREQ=YEARLY;COUNT=3\n", dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1998, 9, 2, 9, 0), datetime(1999, 9, 2, 9, 0)],
        )

    def test_str_unfold(self):
        self.assertEqual(
            list(rrulestr("FREQ=YEA\n RLY;COUNT=3\n", unfold=True, dtstart=datetime(1997, 9, 2, 9, 0))),
            [datetime(1997, 9, 2, 9, 0), datetime(1998, 9, 2, 9, 0), datetime(1999, 9, 2, 9, 0)],
        )

    def test_str_set(self):
        self.assertEqual(
            list(
                rrulestr(
                    "DTSTART:19970902T090000\nRRULE:FREQ=YEARLY;COUNT=2;BYDAY=TU\nRRULE:FREQ=YEARLY;COUNT=1;BYDAY=TH\n"
                )
            ),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)],
        )

    def test_str_set_date(self):
        self.assertEqual(
            list(
                rrulestr(
                    "DTSTART:19970902T090000\n"
                    "RRULE:FREQ=YEARLY;COUNT=1;BYDAY=TU\n"
                    "RDATE:19970904T090000\n"
                    "RDATE:19970909T090000\n"
                )
            ),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)],
        )

    def test_str_set_exrule(self):
        self.assertEqual(
            list(
                rrulestr(
                    "DTSTART:19970902T090000\n"
                    "RRULE:FREQ=YEARLY;COUNT=6;BYDAY=TU,TH\n"
                    "EXRULE:FREQ=YEARLY;COUNT=3;BYDAY=TH\n"
                )
            ),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 9, 9, 0), datetime(1997, 9, 16, 9, 0)],
        )

    def test_str_set_exdate(self):
        self.assertEqual(
            list(
                rrulestr(
                    "DTSTART:19970902T090000\n"
                    "RRULE:FREQ=YEARLY;COUNT=6;BYDAY=TU,TH\n"
                    "EXDATE:19970904T090000\n"
                    "EXDATE:19970911T090000\n"
                    "EXDATE:19970918T090000\n"
                )
            ),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 9, 9, 0), datetime(1997, 9, 16, 9, 0)],
        )

    def test_str_set_exdate_multiple(self):
        rrstr = (
            "DTSTART:19970902T090000\n"
            "RRULE:FREQ=YEARLY;COUNT=6;BYDAY=TU,TH\n"
            "EXDATE:19970904T090000,19970911T090000,19970918T090000\n"
        )

        rr = rrulestr(rrstr)
        assert list(rr) == [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 9, 9, 0), datetime(1997, 9, 16, 9, 0)]

    def test_str_set_exdate_with_tzid(self):
        rr = rrulestr(
            "DTSTART;TZID=Europe/Brussels:19970902T090000\n"
            "RRULE:FREQ=YEARLY;COUNT=6;BYDAY=TU,TH\n"
            "EXDATE;TZID=Europe/Brussels:19970904T090000\n"
            "EXDATE;TZID=Europe/Brussels:19970911T090000\n"
            "EXDATE;TZID=Europe/Brussels:19970918T090000\n"
        )

        assert list(rr) == [
            datetime(1997, 9, 2, 9, 0, tzinfo=BXL),
            datetime(1997, 9, 9, 9, 0, tzinfo=BXL),
            datetime(1997, 9, 16, 9, 0, tzinfo=BXL),
        ]

    def test_str_set_exdate_value_datetime_no_tzid(self):
        rrstr = "\n".join(
            [
                "DTSTART:19970902T090000",
                "RRULE:FREQ=YEARLY;COUNT=4;BYDAY=TU,TH",
                "EXDATE;VALUE=DATE-TIME:19970902T090000",
                "EXDATE;VALUE=DATE-TIME:19970909T090000",
            ]
        )

        rr = rrulestr(rrstr)
        assert list(rr) == [datetime(1997, 9, 4, 9), datetime(1997, 9, 11, 9)]

    def test_str_set_exdate_value_mix_datetime_no_tzid(self):
        rrstr = "\n".join(
            [
                "DTSTART:19970902T090000",
                "RRULE:FREQ=YEARLY;COUNT=4;BYDAY=TU,TH",
                "EXDATE;VALUE=DATE-TIME:19970902T090000",
                "EXDATE:19970909T090000",
            ]
        )

        rr = rrulestr(rrstr)
        assert list(rr) == [datetime(1997, 9, 4, 9), datetime(1997, 9, 11, 9)]

    def test_str_set_exdate_value_datetime_with_tzid(self):
        rrstr = "\n".join(
            [
                "DTSTART;VALUE=DATE-TIME;TZID=Europe/Brussels:19970902T090000",
                "RRULE:FREQ=YEARLY;COUNT=4;BYDAY=TU,TH",
                "EXDATE;VALUE=DATE-TIME;TZID=Europe/Brussels:19970902T090000",
                "EXDATE;VALUE=DATE-TIME;TZID=Europe/Brussels:19970909T090000",
            ]
        )

        rr = rrulestr(rrstr)
        assert list(rr) == [datetime(1997, 9, 4, 9, tzinfo=BXL), datetime(1997, 9, 11, 9, tzinfo=BXL)]

    def test_str_set_exdate_value_date(self):
        rrstr = "\n".join(
            [
                "DTSTART;VALUE=DATE:19970902",
                "RRULE:FREQ=YEARLY;COUNT=4;BYDAY=TU,TH",
                "EXDATE;VALUE=DATE:19970902",
                "EXDATE;VALUE=DATE:19970909",
            ]
        )

        rr = rrulestr(rrstr)
        assert list(rr) == [datetime(1997, 9, 4), datetime(1997, 9, 11)]

    def test_str_set_date_and_ex_date(self):
        self.assertEqual(
            list(
                rrulestr(
                    "DTSTART:19970902T090000\n"
                    "RDATE:19970902T090000\n"
                    "RDATE:19970904T090000\n"
                    "RDATE:19970909T090000\n"
                    "RDATE:19970911T090000\n"
                    "RDATE:19970916T090000\n"
                    "RDATE:19970918T090000\n"
                    "EXDATE:19970904T090000\n"
                    "EXDATE:19970911T090000\n"
                    "EXDATE:19970918T090000\n"
                )
            ),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 9, 9, 0), datetime(1997, 9, 16, 9, 0)],
        )

    def test_str_set_date_and_ex_rule(self):
        self.assertEqual(
            list(
                rrulestr(
                    "DTSTART:19970902T090000\n"
                    "RDATE:19970902T090000\n"
                    "RDATE:19970904T090000\n"
                    "RDATE:19970909T090000\n"
                    "RDATE:19970911T090000\n"
                    "RDATE:19970916T090000\n"
                    "RDATE:19970918T090000\n"
                    "EXRULE:FREQ=YEARLY;COUNT=3;BYDAY=TH\n"
                )
            ),
            [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 9, 9, 0), datetime(1997, 9, 16, 9, 0)],
        )

    def test_str_keywords(self):
        self.assertEqual(
            list(
                rrulestr(
                    "DTSTART:19970902T090000\n"
                    "RRULE:FREQ=YEARLY;COUNT=3;INTERVAL=3;"
                    "BYMONTH=3;BYWEEKDAY=TH;BYMONTHDAY=3;"
                    "BYHOUR=3;BYMINUTE=3;BYSECOND=3\n"
                )
            ),
            [datetime(2033, 3, 3, 3, 3, 3), datetime(2039, 3, 3, 3, 3, 3), datetime(2072, 3, 3, 3, 3, 3)],
        )

    def test_str_nweekday(self):
        self.assertEqual(
            list(rrulestr("DTSTART:19970902T090000\nRRULE:FREQ=YEARLY;COUNT=3;BYDAY=1TU,-1TH\n")),
            [datetime(1997, 12, 25, 9, 0), datetime(1998, 1, 6, 9, 0), datetime(1998, 12, 31, 9, 0)],
        )

    def test_str_until(self):
        self.assertEqual(
            list(rrulestr("DTSTART:19970902T090000\nRRULE:FREQ=YEARLY;UNTIL=19990101T000000;BYDAY=1TU,-1TH\n")),
            [datetime(1997, 12, 25, 9, 0), datetime(1998, 1, 6, 9, 0), datetime(1998, 12, 31, 9, 0)],
        )

    def test_str_value_datetime(self):
        rr = rrulestr("DTSTART;VALUE=DATE-TIME:19970902T090000\nRRULE:FREQ=YEARLY;COUNT=2")

        self.assertEqual(list(rr), [datetime(1997, 9, 2, 9, 0, 0), datetime(1998, 9, 2, 9, 0, 0)])

    def test_str_value_date(self):
        rr = rrulestr("DTSTART;VALUE=DATE:19970902\nRRULE:FREQ=YEARLY;COUNT=2")

        self.assertEqual(list(rr), [datetime(1997, 9, 2, 0, 0, 0), datetime(1998, 9, 2, 0, 0, 0)])

    def test_str_multiple_dtstart_comma(self):
        with pytest.raises(ValueError):
            _ = rrulestr("DTSTART:19970101T000000,19970202T000000\nRRULE:FREQ=YEARLY;COUNT=1")

    def test_str_invalid_until(self):
        with self.assertRaises(ValueError):
            list(rrulestr("DTSTART:19970902T090000\nRRULE:FREQ=YEARLY;UNTIL=TheCowsComeHome;BYDAY=1TU,-1TH\n"))

    def test_str_until_must_be_utc(self):
        with self.assertRaises(ValueError):
            list(
                rrulestr(
                    "DTSTART;TZID=America/New_York:19970902T090000\n"
                    "RRULE:FREQ=YEARLY;"
                    "UNTIL=19990101T000000;BYDAY=1TU,-1TH\n"
                )
            )

    def test_str_until_with_tz(self):
        rr = list(rrulestr("DTSTART;TZID=America/New_York:19970101T000000\nRRULE:FREQ=YEARLY;UNTIL=19990101T000000Z\n"))
        self.assertEqual(
            list(rr), [datetime(1997, 1, 1, 0, 0, 0, tzinfo=NYC), datetime(1998, 1, 1, 0, 0, 0, tzinfo=NYC)]
        )

    def test_str_empty_by_day(self):
        with self.assertRaises(ValueError):
            list(
                rrulestr(
                    "DTSTART:19970902T090000\n"
                    "FREQ=WEEKLY;"
                    "BYDAY=;"  # This part is invalid
                    "WKST=SU"
                )
            )

    def test_str_invalid_by_day(self):
        with self.assertRaises(ValueError):
            list(
                rrulestr(
                    "DTSTART:19970902T090000\n"
                    "FREQ=WEEKLY;"
                    "BYDAY=-1OK;"  # This part is invalid
                    "WKST=SU"
                )
            )

    def test_bad_by_set_pos(self):
        self.assertRaises(ValueError, rrule, MONTHLY, count=1, bysetpos=0, dtstart=datetime(1997, 9, 2, 9, 0))

    def test_bad_by_set_pos_many(self):
        self.assertRaises(ValueError, rrule, MONTHLY, count=1, bysetpos=(-1, 0, 1), dtstart=datetime(1997, 9, 2, 9, 0))

    # Tests to ensure that str(rrule) works
    def test_to_str_yearly(self):
        rule = rrule(YEARLY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))
        self._rrulestr_reverse_test(rule)

    def test_to_str_yearly_interval(self):
        rule = rrule(YEARLY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0))
        self._rrulestr_reverse_test(rule)

    def test_to_str_yearly_by_month(self):
        self._rrulestr_reverse_test(rrule(YEARLY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_yearly_by_month_day(self):
        self._rrulestr_reverse_test(rrule(YEARLY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_yearly_bymonth_and_monthday(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_byweekday(self):
        self._rrulestr_reverse_test(rrule(YEARLY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_yearly_bynweekday(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_bynweekday_large(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, byweekday=(TU(3), TH(-3)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_month_and_week_day(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_month_and_nweekday(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_month_and_nweekday_large(self):
        # This is interesting because the TH(-3) ends up before
        # the TU(3).
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, bymonth=(1, 3), byweekday=(TU(3), TH(-3)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_bymonthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_bymonth_and_monthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(
                YEARLY,
                count=3,
                bymonth=(1, 3),
                bymonthday=(1, 3),
                byweekday=(TU, TH),
                dtstart=datetime(1997, 9, 2, 9, 0),
            )
        )

    def test_to_str_yearly_by_year_day(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_month_and_year_day(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=4, bymonth=(4, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_month_and_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=4, bymonth=(4, 7), byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_week_no(self):
        self._rrulestr_reverse_test(rrule(YEARLY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_yearly_by_week_no_and_week_day(self):
        # That's a nice one. The first days of week number one
        # may be in the last year.
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_week_no_and_week_day_large(self):
        # Another nice test. The last days of week number 52/53
        # may be in the next year.
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_week_no_and_week_day_last(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_easter(self):
        self._rrulestr_reverse_test(rrule(YEARLY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_yearly_by_easter_pos(self):
        self._rrulestr_reverse_test(rrule(YEARLY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_yearly_by_easter_neg(self):
        self._rrulestr_reverse_test(rrule(YEARLY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_yearly_by_week_no_and_week_day53(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_hour(self):
        self._rrulestr_reverse_test(rrule(YEARLY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_yearly_by_minute(self):
        self._rrulestr_reverse_test(rrule(YEARLY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_yearly_by_second(self):
        self._rrulestr_reverse_test(rrule(YEARLY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_yearly_by_hour_and_minute(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_hour_and_second(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_yearly_by_hour_and_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(
                YEARLY, count=3, byhour=(6, 18), byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)
            )
        )

    def test_to_str_yearly_by_set_pos(self):
        self._rrulestr_reverse_test(
            rrule(YEARLY, count=3, bymonthday=15, byhour=(6, 18), bysetpos=(3, -3), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_monthly_interval(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_monthly_interval_large(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, interval=18, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_monthly_by_month(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_monthly_by_month_day(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_monthly_by_month_and_month_day(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_byweekday(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0)))

        # Third Monday of the month
        self.assertEqual(
            rrule(MONTHLY, byweekday=(MO(+3)), dtstart=datetime(1997, 9, 1)).between(
                datetime(1997, 9, 1), datetime(1997, 12, 1)
            ),
            [datetime(1997, 9, 15, 0, 0), datetime(1997, 10, 20, 0, 0), datetime(1997, 11, 17, 0, 0)],
        )

    def test_to_str_monthly_bynweekday(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_bynweekday_large(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, byweekday=(TU(3), TH(-3)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_month_and_week_day(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_month_and_nweekday(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_month_and_nweekday_large(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, bymonth=(1, 3), byweekday=(TU(3), TH(-3)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_bymonthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_bymonth_and_monthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(
                MONTHLY,
                count=3,
                bymonth=(1, 3),
                bymonthday=(1, 3),
                byweekday=(TU, TH),
                dtstart=datetime(1997, 9, 2, 9, 0),
            )
        )

    def test_to_str_monthly_by_year_day(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_month_and_year_day(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=4, bymonth=(4, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_month_and_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(
                MONTHLY, count=4, bymonth=(4, 7), byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0)
            )
        )

    def test_to_str_monthly_by_week_no(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_monthly_by_week_no_and_week_day(self):
        # That's a nice one. The first days of week number one
        # may be in the last year.
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_week_no_and_week_day_large(self):
        # Another nice test. The last days of week number 52/53
        # may be in the next year.
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_week_no_and_week_day_last(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_week_no_and_week_day53(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_easter(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_monthly_by_easter_pos(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_monthly_by_easter_neg(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_monthly_by_hour(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_monthly_by_minute(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_monthly_by_second(self):
        self._rrulestr_reverse_test(rrule(MONTHLY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_monthly_by_hour_and_minute(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_hour_and_second(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(MONTHLY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_monthly_by_hour_and_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(
                MONTHLY, count=3, byhour=(6, 18), byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)
            )
        )

    def test_to_str_monthly_by_set_pos(self):
        self._rrulestr_reverse_test(
            rrule(
                MONTHLY,
                count=3,
                bymonthday=(13, 17),
                byhour=(6, 18),
                bysetpos=(3, -3),
                dtstart=datetime(1997, 9, 2, 9, 0),
            )
        )

    def test_to_str_weekly(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_interval(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_interval_large(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, interval=20, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_by_month(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_by_month_day(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_by_month_and_month_day(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_byweekday(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_bynweekday(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_month_and_week_day(self):
        # This test is interesting, because it crosses the year
        # boundary in a weekly period to find day '1' as a
        # valid recurrence.
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_month_and_nweekday(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_bymonthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_bymonth_and_monthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(
                WEEKLY,
                count=3,
                bymonth=(1, 3),
                bymonthday=(1, 3),
                byweekday=(TU, TH),
                dtstart=datetime(1997, 9, 2, 9, 0),
            )
        )

    def test_to_str_weekly_by_year_day(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_month_and_year_day(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=4, bymonth=(1, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_month_and_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=4, bymonth=(1, 7), byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_week_no(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_by_week_no_and_week_day(self):
        # That's a nice one. The first days of week number one
        # may be in the last year.
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_week_no_and_week_day_large(self):
        # Another nice test. The last days of week number 52/53
        # may be in the next year.
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_week_no_and_week_day_last(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_week_no_and_week_day53(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_easter(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_by_easter_pos(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_by_easter_neg(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_by_hour(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_by_minute(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_by_second(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_weekly_by_hour_and_minute(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_hour_and_second(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(WEEKLY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_weekly_by_hour_and_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(
                WEEKLY, count=3, byhour=(6, 18), byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)
            )
        )

    def test_to_str_weekly_by_set_pos(self):
        self._rrulestr_reverse_test(
            rrule(
                WEEKLY,
                count=3,
                byweekday=(TU, TH),
                byhour=(6, 18),
                bysetpos=(3, -3),
                dtstart=datetime(1997, 9, 2, 9, 0),
            )
        )

    def test_to_str_daily(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_interval(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_interval_large(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, interval=92, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_by_month(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_by_month_day(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_by_month_and_month_day(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_byweekday(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_bynweekday(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_by_month_and_week_day(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_by_month_and_nweekday(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_bymonthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_bymonth_and_monthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(
                DAILY,
                count=3,
                bymonth=(1, 3),
                bymonthday=(1, 3),
                byweekday=(TU, TH),
                dtstart=datetime(1997, 9, 2, 9, 0),
            )
        )

    def test_to_str_daily_by_year_day(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_by_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_by_month_and_year_day(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=4, bymonth=(1, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_by_month_and_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=4, bymonth=(1, 7), byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_by_week_no(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_by_week_no_and_week_day(self):
        # That's a nice one. The first days of week number one
        # may be in the last year.
        self._rrulestr_reverse_test(rrule(DAILY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_by_week_no_and_week_day_large(self):
        # Another nice test. The last days of week number 52/53
        # may be in the next year.
        self._rrulestr_reverse_test(
            rrule(DAILY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_by_week_no_and_week_day_last(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_by_week_no_and_week_day53(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_by_easter(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_by_easter_pos(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_by_easter_neg(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_by_hour(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_by_minute(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_by_second(self):
        self._rrulestr_reverse_test(rrule(DAILY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_daily_by_hour_and_minute(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_by_hour_and_second(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_by_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(DAILY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_daily_by_hour_and_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(
                DAILY, count=3, byhour=(6, 18), byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)
            )
        )

    def test_to_str_daily_by_set_pos(self):
        self._rrulestr_reverse_test(
            rrule(
                DAILY, count=3, byhour=(6, 18), byminute=(15, 45), bysetpos=(3, -3), dtstart=datetime(1997, 9, 2, 9, 0)
            )
        )

    def test_to_str_hourly(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_interval(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_interval_large(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, interval=769, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_by_month(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_by_month_day(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_by_month_and_month_day(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_byweekday(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_bynweekday(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_month_and_week_day(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_month_and_nweekday(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_bymonthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_bymonth_and_monthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(
                HOURLY,
                count=3,
                bymonth=(1, 3),
                bymonthday=(1, 3),
                byweekday=(TU, TH),
                dtstart=datetime(1997, 9, 2, 9, 0),
            )
        )

    def test_to_str_hourly_by_year_day(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_month_and_year_day(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=4, bymonth=(4, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_month_and_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=4, bymonth=(4, 7), byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_week_no(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_by_week_no_and_week_day(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_week_no_and_week_day_large(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_week_no_and_week_day_last(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_week_no_and_week_day53(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_easter(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_by_easter_pos(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_by_easter_neg(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_by_hour(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_by_minute(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_by_second(self):
        self._rrulestr_reverse_test(rrule(HOURLY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_hourly_by_hour_and_minute(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_hour_and_second(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(HOURLY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_hourly_by_hour_and_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(
                HOURLY, count=3, byhour=(6, 18), byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)
            )
        )

    def test_to_str_hourly_by_set_pos(self):
        self._rrulestr_reverse_test(
            rrule(
                HOURLY,
                count=3,
                byminute=(15, 45),
                bysecond=(15, 45),
                bysetpos=(3, -3),
                dtstart=datetime(1997, 9, 2, 9, 0),
            )
        )

    def test_to_str_minutely(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_interval(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_interval_large(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, interval=1501, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_by_month(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_by_month_day(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_by_month_and_month_day(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_byweekday(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_bynweekday(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_by_month_and_week_day(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_by_month_and_nweekday(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_bymonthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_bymonth_and_monthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(
                MINUTELY,
                count=3,
                bymonth=(1, 3),
                bymonthday=(1, 3),
                byweekday=(TU, TH),
                dtstart=datetime(1997, 9, 2, 9, 0),
            )
        )

    def test_to_str_minutely_by_year_day(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_by_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_by_month_and_year_day(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=4, bymonth=(4, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_by_month_and_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(
                MINUTELY, count=4, bymonth=(4, 7), byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0)
            )
        )

    def test_to_str_minutely_by_week_no(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_by_week_no_and_week_day(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_by_week_no_and_week_day_large(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_by_week_no_and_week_day_last(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_by_week_no_and_week_day53(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_by_easter(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_by_easter_pos(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_by_easter_neg(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_by_hour(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_by_minute(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_by_second(self):
        self._rrulestr_reverse_test(rrule(MINUTELY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_minutely_by_hour_and_minute(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_by_hour_and_second(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_by_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_minutely_by_hour_and_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(
                MINUTELY,
                count=3,
                byhour=(6, 18),
                byminute=(6, 18),
                bysecond=(6, 18),
                dtstart=datetime(1997, 9, 2, 9, 0),
            )
        )

    def test_to_str_minutely_by_set_pos(self):
        self._rrulestr_reverse_test(
            rrule(MINUTELY, count=3, bysecond=(15, 30, 45), bysetpos=(3, -3), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_interval(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, interval=2, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_interval_large(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, interval=90061, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_by_month(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, bymonth=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_by_month_day(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, bymonthday=(1, 3), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_by_month_and_month_day(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, bymonth=(1, 3), bymonthday=(5, 7), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_byweekday(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_bynweekday(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_by_month_and_week_day(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, bymonth=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_by_month_and_nweekday(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, bymonth=(1, 3), byweekday=(TU(1), TH(-1)), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_bymonthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, bymonthday=(1, 3), byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_bymonth_and_monthday_and_weekday(self):
        self._rrulestr_reverse_test(
            rrule(
                SECONDLY,
                count=3,
                bymonth=(1, 3),
                bymonthday=(1, 3),
                byweekday=(TU, TH),
                dtstart=datetime(1997, 9, 2, 9, 0),
            )
        )

    def test_to_str_secondly_by_year_day(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=4, byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_by_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=4, byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_by_month_and_year_day(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=4, bymonth=(4, 7), byyearday=(1, 100, 200, 365), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_by_month_and_year_day_neg(self):
        self._rrulestr_reverse_test(
            rrule(
                SECONDLY, count=4, bymonth=(4, 7), byyearday=(-365, -266, -166, -1), dtstart=datetime(1997, 9, 2, 9, 0)
            )
        )

    def test_to_str_secondly_by_week_no(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, byweekno=20, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_by_week_no_and_week_day(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, byweekno=1, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_by_week_no_and_week_day_large(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, byweekno=52, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_by_week_no_and_week_day_last(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, byweekno=-1, byweekday=SU, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_by_week_no_and_week_day53(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, byweekno=53, byweekday=MO, dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_by_easter(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, byeaster=0, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_by_easter_pos(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, byeaster=1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_by_easter_neg(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, byeaster=-1, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_by_hour(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, byhour=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_by_minute(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_by_second(self):
        self._rrulestr_reverse_test(rrule(SECONDLY, count=3, bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_to_str_secondly_by_hour_and_minute(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, byhour=(6, 18), byminute=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_by_hour_and_second(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, byhour=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_by_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, byminute=(6, 18), bysecond=(6, 18), dtstart=datetime(1997, 9, 2, 9, 0))
        )

    def test_to_str_secondly_by_hour_and_minute_and_second(self):
        self._rrulestr_reverse_test(
            rrule(
                SECONDLY,
                count=3,
                byhour=(6, 18),
                byminute=(6, 18),
                bysecond=(6, 18),
                dtstart=datetime(1997, 9, 2, 9, 0),
            )
        )

    def test_to_str_secondly_by_hour_and_minute_and_second_bug(self):
        # This explores a bug found by Mathieu Bridon.
        self._rrulestr_reverse_test(
            rrule(SECONDLY, count=3, bysecond=(0,), byminute=(1,), dtstart=datetime(2010, 3, 22, 12, 1))
        )

    def test_to_str_with_wkst(self):
        self._rrulestr_reverse_test(rrule(WEEKLY, count=3, wkst=SU, dtstart=datetime(1997, 9, 2, 9, 0)))

    def test_replace_if_set(self):
        rr = rrule(YEARLY, count=1, bymonthday=5, dtstart=datetime(1997, 1, 1))
        newrr = rr.replace(bymonthday=6)
        self.assertEqual(list(rr), [datetime(1997, 1, 5)])
        self.assertEqual(list(newrr), [datetime(1997, 1, 6)])

    def test_replace_if_not_set(self):
        rr = rrule(YEARLY, count=1, dtstart=datetime(1997, 1, 1))
        newrr = rr.replace(bymonthday=6)
        self.assertEqual(list(rr), [datetime(1997, 1, 1)])
        self.assertEqual(list(newrr), [datetime(1997, 1, 6)])


@pytest.mark.rrule
@freeze_time(datetime(2018, 3, 6, 5, 36, tzinfo=tz.UTC), MODULE)
def test_generated_aware_dtstart():
    dtstart_exp = datetime(2018, 3, 6, 5, 36, tzinfo=tz.UTC)
    until = datetime(2018, 3, 6, 8, 0, tzinfo=tz.UTC)

    rule_without_dtstart = rrule(freq=HOURLY, until=until)
    rule_with_dtstart = rrule(freq=HOURLY, dtstart=dtstart_exp, until=until)
    assert list(rule_without_dtstart) == list(rule_with_dtstart)


@pytest.mark.rrule
@pytest.mark.rrulestr
@pytest.mark.xfail(reason="rrulestr loses time zone, gh issue #637")
@freeze_time(datetime(2018, 3, 6, 5, 36, tzinfo=tz.UTC), MODULE)
def test_generated_aware_dtstart_rrulestr():
    rrule_without_dtstart = rrule(freq=HOURLY, until=datetime(2018, 3, 6, 8, 0, tzinfo=tz.UTC))
    rrule_r = rrulestr(str(rrule_without_dtstart))

    assert list(rrule_r) == list(rrule_without_dtstart)


@pytest.mark.rruleset
class RRuleSetTest(unittest.TestCase):
    def test_set(self):
        rrset = rruleset()
        rrset.rrule(rrule(YEARLY, count=2, byweekday=TU, dtstart=datetime(1997, 9, 2, 9, 0)))
        rrset.rrule(rrule(YEARLY, count=1, byweekday=TH, dtstart=datetime(1997, 9, 2, 9, 0)))
        self.assertEqual(
            list(rrset), [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)]
        )

    def test_set_date(self):
        rrset = rruleset()
        rrset.rrule(rrule(YEARLY, count=1, byweekday=TU, dtstart=datetime(1997, 9, 2, 9, 0)))
        rrset.rdate(datetime(1997, 9, 4, 9))
        rrset.rdate(datetime(1997, 9, 9, 9))
        self.assertEqual(
            list(rrset), [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)]
        )

    def test_set_exrule(self):
        rrset = rruleset()
        rrset.rrule(rrule(YEARLY, count=6, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0)))
        rrset.exrule(rrule(YEARLY, count=3, byweekday=TH, dtstart=datetime(1997, 9, 2, 9, 0)))
        self.assertEqual(
            list(rrset), [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 9, 9, 0), datetime(1997, 9, 16, 9, 0)]
        )

    def test_set_exdate(self):
        rrset = rruleset()
        rrset.rrule(rrule(YEARLY, count=6, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0)))
        rrset.exdate(datetime(1997, 9, 4, 9))
        rrset.exdate(datetime(1997, 9, 11, 9))
        rrset.exdate(datetime(1997, 9, 18, 9))
        self.assertEqual(
            list(rrset), [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 9, 9, 0), datetime(1997, 9, 16, 9, 0)]
        )

    def test_set_exdate_rev_order(self):
        rrset = rruleset()
        rrset.rrule(rrule(MONTHLY, count=5, bymonthday=10, dtstart=datetime(2004, 1, 1, 9, 0)))
        rrset.exdate(datetime(2004, 4, 10, 9, 0))
        rrset.exdate(datetime(2004, 2, 10, 9, 0))
        self.assertEqual(
            list(rrset), [datetime(2004, 1, 10, 9, 0), datetime(2004, 3, 10, 9, 0), datetime(2004, 5, 10, 9, 0)]
        )

    def test_set_date_and_ex_date(self):
        rrset = rruleset()
        rrset.rdate(datetime(1997, 9, 2, 9))
        rrset.rdate(datetime(1997, 9, 4, 9))
        rrset.rdate(datetime(1997, 9, 9, 9))
        rrset.rdate(datetime(1997, 9, 11, 9))
        rrset.rdate(datetime(1997, 9, 16, 9))
        rrset.rdate(datetime(1997, 9, 18, 9))
        rrset.exdate(datetime(1997, 9, 4, 9))
        rrset.exdate(datetime(1997, 9, 11, 9))
        rrset.exdate(datetime(1997, 9, 18, 9))
        self.assertEqual(
            list(rrset), [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 9, 9, 0), datetime(1997, 9, 16, 9, 0)]
        )

    def test_set_date_and_ex_rule(self):
        rrset = rruleset()
        rrset.rdate(datetime(1997, 9, 2, 9))
        rrset.rdate(datetime(1997, 9, 4, 9))
        rrset.rdate(datetime(1997, 9, 9, 9))
        rrset.rdate(datetime(1997, 9, 11, 9))
        rrset.rdate(datetime(1997, 9, 16, 9))
        rrset.rdate(datetime(1997, 9, 18, 9))
        rrset.exrule(rrule(YEARLY, count=3, byweekday=TH, dtstart=datetime(1997, 9, 2, 9, 0)))
        self.assertEqual(
            list(rrset), [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 9, 9, 0), datetime(1997, 9, 16, 9, 0)]
        )

    def test_set_count(self):
        rrset = rruleset()
        rrset.rrule(rrule(YEARLY, count=6, byweekday=(TU, TH), dtstart=datetime(1997, 9, 2, 9, 0)))
        rrset.exrule(rrule(YEARLY, count=3, byweekday=TH, dtstart=datetime(1997, 9, 2, 9, 0)))
        self.assertEqual(rrset.count(), 3)

    def test_set_cache_pre(self):
        rrset = rruleset()
        rrset.rrule(rrule(YEARLY, count=2, byweekday=TU, dtstart=datetime(1997, 9, 2, 9, 0)))
        rrset.rrule(rrule(YEARLY, count=1, byweekday=TH, dtstart=datetime(1997, 9, 2, 9, 0)))
        self.assertEqual(
            list(rrset), [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)]
        )

    def test_set_cache_post(self):
        rrset = rruleset(cache=True)
        rrset.rrule(rrule(YEARLY, count=2, byweekday=TU, dtstart=datetime(1997, 9, 2, 9, 0)))
        rrset.rrule(rrule(YEARLY, count=1, byweekday=TH, dtstart=datetime(1997, 9, 2, 9, 0)))
        for _ in rrset:
            pass
        self.assertEqual(
            list(rrset), [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)]
        )

    def test_set_cache_post_internal(self):
        rrset = rruleset(cache=True)
        rrset.rrule(rrule(YEARLY, count=2, byweekday=TU, dtstart=datetime(1997, 9, 2, 9, 0)))
        rrset.rrule(rrule(YEARLY, count=1, byweekday=TH, dtstart=datetime(1997, 9, 2, 9, 0)))
        for _ in rrset:
            pass
        self.assertEqual(
            list(rrset._cache), [datetime(1997, 9, 2, 9, 0), datetime(1997, 9, 4, 9, 0), datetime(1997, 9, 9, 9, 0)]
        )

    def test_set_rrule_count(self):
        # Test that the count is updated when an rrule is added
        _ = rruleset(cache=False)
        for cache in (True, False):
            rrset = rruleset(cache=cache)
            rrset.rrule(rrule(YEARLY, count=2, byweekday=TH, dtstart=datetime(1983, 4, 1)))
            rrset.rrule(rrule(WEEKLY, count=4, byweekday=FR, dtstart=datetime(1991, 6, 3)))

            # Check the length twice - first one sets a cache, second reads it
            self.assertEqual(rrset.count(), 6)
            self.assertEqual(rrset.count(), 6)

            # This should invalidate the cache and force an update
            rrset.rrule(rrule(MONTHLY, count=3, dtstart=datetime(1994, 1, 3)))

            self.assertEqual(rrset.count(), 9)
            self.assertEqual(rrset.count(), 9)

    def test_set_rdate_count(self):
        # Test that the count is updated when an rdate is added
        _ = rruleset(cache=False)
        for cache in (True, False):
            rrset = rruleset(cache=cache)
            rrset.rrule(rrule(YEARLY, count=2, byweekday=TH, dtstart=datetime(1983, 4, 1)))
            rrset.rrule(rrule(WEEKLY, count=4, byweekday=FR, dtstart=datetime(1991, 6, 3)))

            # Check the length twice - first one sets a cache, second reads it
            self.assertEqual(rrset.count(), 6)
            self.assertEqual(rrset.count(), 6)

            # This should invalidate the cache and force an update
            rrset.rdate(datetime(1993, 2, 14))

            self.assertEqual(rrset.count(), 7)
            self.assertEqual(rrset.count(), 7)

    def test_set_exrule_count(self):
        # Test that the count is updated when an exrule is added
        _ = rruleset(cache=False)
        for cache in (True, False):
            rrset = rruleset(cache=cache)
            rrset.rrule(rrule(YEARLY, count=2, byweekday=TH, dtstart=datetime(1983, 4, 1)))
            rrset.rrule(rrule(WEEKLY, count=4, byweekday=FR, dtstart=datetime(1991, 6, 3)))

            # Check the length twice - first one sets a cache, second reads it
            self.assertEqual(rrset.count(), 6)
            self.assertEqual(rrset.count(), 6)

            # This should invalidate the cache and force an update
            rrset.exrule(rrule(WEEKLY, count=2, interval=2, dtstart=datetime(1991, 6, 14)))

            self.assertEqual(rrset.count(), 4)
            self.assertEqual(rrset.count(), 4)

    def test_set_exdate_count(self):
        # Test that the count is updated when an rdate is added
        for cache in (True, False):
            rrset = rruleset(cache=cache)
            rrset.rrule(rrule(YEARLY, count=2, byweekday=TH, dtstart=datetime(1983, 4, 1)))
            rrset.rrule(rrule(WEEKLY, count=4, byweekday=FR, dtstart=datetime(1991, 6, 3)))

            # Check the length twice - first one sets a cache, second reads it
            self.assertEqual(rrset.count(), 6)
            self.assertEqual(rrset.count(), 6)

            # This should invalidate the cache and force an update
            rrset.exdate(datetime(1991, 6, 28))

            self.assertEqual(rrset.count(), 5)
            self.assertEqual(rrset.count(), 5)
