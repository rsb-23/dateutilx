import calendar
import datetime as dt
import operator
from math import copysign
from types import NotImplementedType
from typing import Self
from warnings import warn

from dateutilx.weekday import Weekday, weekdays

__all__ = ["RelativeDelta"]
Number = float | int


class RelativeDelta:
    """
    The relativedelta type is designed to be applied to an existing datetime and
    can replace specific components of that datetime, or represents an interval
    of time.

    It is based on the specification of the excellent work done by M.-A. Lemburg
    in his
    `mx.DateTime <https://www.egenix.com/products/python/mxBase/mxDateTime/>`_ extension.
    However, notice that this type does *NOT* implement the same algorithm as
    his work. Do *NOT* expect it to behave like mx.DateTime's counterpart.

    There are two different ways to build a relativedelta instance. The
    first one is passing it two date/datetime classes::

        relativedelta(datetime1, datetime2)

    The second one is passing it any number of the following keyword arguments::

        relativedelta(arg1=x,arg2=y,arg3=z...)

        year, month, day, hour, minute, second, microsecond:
            Absolute information (argument is singular); adding or subtracting a
            relativedelta with absolute information does not perform an arithmetic
            operation, but rather REPLACES the corresponding value in the
            original datetime with the value(s) in relativedelta.

        years, months, weeks, days, hours, minutes, seconds, microseconds:
            Relative information, may be negative (argument is plural); adding
            or subtracting a relativedelta with relative information performs
            the corresponding arithmetic operation on the original datetime value
            with the information in the relativedelta.

        weekday:
            One of the weekday instances (MO, TU, etc) available in the
            relativedelta module. These instances may receive a parameter N,
            specifying the Nth weekday, which could be positive or negative
            (like MO(+1) or MO(-2)). Not specifying it is the same as specifying
            +1. You can also use an integer, where 0=MO. This argument is always
            relative e.g. if the calculated date is already Monday, using MO(1)
            or MO(-1) won't change the day. To effectively make it absolute, use
            it in combination with the day argument (e.g. day=1, MO(1) for first
            Monday of the month).

        leapdays:
            Will add given days to the date found, if year is a leap
            year, and the date found is post 28 of february.

        yearday, nlyearday:
            Set the yearday or the non-leap year day (jump leap days).
            These are converted to day/month/leapdays information.

    There are relative and absolute forms of the keyword
    arguments. The plural is relative, and the singular is
    absolute. For each argument in the order below, the absolute form
    is applied first (by setting each attribute to that value) and
    then the relative form (by adding the value to the attribute).

    The order of attributes considered when this relativedelta is
    added to a datetime is:

    1. Year
    2. Month
    3. Day
    4. Hours
    5. Minutes
    6. Seconds
    7. Microseconds

    Finally, weekday is applied, using the rule described above.

    For example

    >>> from datetime import datetime
    >>> from dateutilx.relativedelta import RelativeDelta, MO
    >>> dt_ = datetime(2018, 4, 9, 13, 37, 0)
    >>> delta = RelativeDelta(hours=25, day=1, weekday=MO(1))
    >>> dt_ + delta
    dt.datetime(2018, 4, 2, 14, 37)

    First, the day is set to 1 (the first of the month), then 25 hours
    are added, to get to the 2nd day and 14th hour, finally the
    weekday is applied, but since the 2nd is already a Monday there is
    no effect.

    """

    # pylint: disable=r0913
    def __init__(
        self,
        dt1=None,
        dt2=None,
        *,
        years=0,
        months=0,
        days: Number = 0,
        leapdays=0,
        weeks=0,
        hours=0,
        minutes=0,
        seconds=0,
        microseconds=0,
        year=None,
        month=None,
        day=None,
        weekday: Weekday | int | None = None,
        yearday=None,
        nlyearday=None,
        hour=None,
        minute=None,
        second=None,
        microsecond=None,
    ):
        if dt1 and dt2:
            self._init_from_dates(dt1, dt2)
        else:
            # Relative information
            self.years = years
            self.months = months
            self.days = days + weeks * 7
            self.leapdays = leapdays
            self.hours = hours
            self.minutes = minutes
            self.seconds = seconds
            self.microseconds = microseconds

            # Absolute information
            self.year = year
            self.month = month
            self.day = day
            self.hour = hour
            self.minute = minute
            self.second = second
            self.microsecond = microsecond
            self.weekday: Weekday | None = weekdays[weekday] if isinstance(weekday, int) else weekday

            self._init_from_fields(yearday=yearday, nlyearday=nlyearday)
        self._fix()

    def _init_from_dates(self, dt1: dt.date | dt.datetime, dt2: dt.date | dt.datetime) -> None:
        # datetime is a subclass of date. So both must be date
        if not (isinstance(dt1, dt.date) and isinstance(dt2, dt.date)):
            raise TypeError("relativedelta only diffs datetime/date")

        # We allow two dates, or two datetimes, so we coerce them to be
        # of the same type
        if isinstance(dt1, dt.datetime) != isinstance(dt2, dt.datetime):
            if not isinstance(dt1, dt.datetime):
                dt1 = dt.datetime.fromordinal(dt1.toordinal())
            elif not isinstance(dt2, dt.datetime):
                dt2 = dt.datetime.fromordinal(dt2.toordinal())

        self._reset()

        # Get year / month delta between the two
        months = (dt1.year - dt2.year) * 12 + (dt1.month - dt2.month)
        self._set_months(months)

        # Remove the year/month delta so the timedelta is just well-defined
        # time units (seconds, days and microseconds)
        dtm = self.__radd__(dt2)

        # If we've overshot our target, make an adjustment
        if dt1 < dt2:
            compare = operator.gt
            increment = 1
        else:
            compare = operator.lt
            increment = -1

        while compare(dt1, dtm):
            months += increment
            self._set_months(months)
            dtm = self.__radd__(dt2)

        # Get the timedelta between the "months-adjusted" date and dt1
        delta = dt1 - dtm
        self.seconds = delta.seconds + delta.days * 86400
        self.microseconds = delta.microseconds

    def _init_from_fields(self, yearday: int, nlyearday: int) -> None:
        # Check for non-integer values in integer-only quantities
        if any(x is not None and x != int(x) for x in (self.years, self.months)):
            raise ValueError("Non-integer years and months are ambiguous and not currently supported.")

        self.years = int(self.years)
        self.months = int(self.months)

        absolute_fields = (self.year, self.month, self.day, self.hour, self.minute, self.second, self.microsecond)
        if any(x is not None and int(x) != x for x in absolute_fields):
            # For now we'll deprecate floats - later it'll be an error.
            warn(
                "Non-integer value passed as absolute information. "
                + "This is not a well-defined condition and will raise "
                + "errors in future versions.",
                DeprecationWarning,
            )

        yday = nlyearday or yearday

        if yearday and not nlyearday and yearday > 59:
            self.leapdays = -1

        if yday:
            if not 1 <= yday <= 366:
                raise ValueError(f"invalid year day ({yday})")

            resolved = dt.date(2001, 1, 1) + dt.timedelta(days=yday - 1)
            self.day, self.month = resolved.day, resolved.month

    def _absolutes(self) -> dict[str, Number]:
        return {
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "hour": self.hour,
            "minute": self.minute,
            "second": self.second,
            "microsecond": self.microsecond,
        }

    def _relatives(self) -> dict[str, Number]:
        return {
            "years": self.years,
            "months": self.months,
            "days": self.days,
            "hours": self.hours,
            "minutes": self.minutes,
            "seconds": self.seconds,
            "microseconds": self.microseconds,
        }

    def _reset(self):
        self.leapdays = 0
        self.weekday = None
        self._has_time = 0

        for attr in ("years", "months", "days", "hours", "minutes", "seconds", "microseconds"):
            setattr(self, attr, 0)

        for attr in ("year", "month", "day", "hour", "minute", "second", "microsecond"):
            setattr(self, attr, None)

    def _fix(self):
        if abs(self.microseconds) > 999999:
            s = _sign(self.microseconds)
            div, mod = divmod(self.microseconds * s, 1000000)
            self.microseconds = mod * s
            self.seconds += div * s
        if abs(self.seconds) > 59:
            s = _sign(self.seconds)
            div, mod = divmod(self.seconds * s, 60)
            self.seconds = mod * s
            self.minutes += div * s
        if abs(self.minutes) > 59:
            s = _sign(self.minutes)
            div, mod = divmod(self.minutes * s, 60)
            self.minutes = mod * s
            self.hours += div * s
        if abs(self.hours) > 23:
            s = _sign(self.hours)
            div, mod = divmod(self.hours * s, 24)
            self.hours = mod * s
            self.days += div * s
        if abs(self.months) > 11:
            s = _sign(self.months)
            div, mod = divmod(self.months * s, 12)
            self.months = mod * s
            self.years += div * s
        # fmt:off
        if any(
                [self.hours, self.minutes, self.seconds, self.microseconds,
                 self.hour is not None, self.minute is not None,
                 self.second is not None, self.microsecond is not None]
        ):
            self._has_time = 1
        else:
            self._has_time = 0
        # fmt:on

    @property
    def weeks(self):
        return int(self.days / 7.0)

    @weeks.setter
    def weeks(self, value):
        self.days = self.days - (self.weeks * 7) + value * 7

    def _set_months(self, months):
        self.months = months
        if abs(self.months) > 11:
            s = _sign(self.months)
            div, mod = divmod(self.months * s, 12)
            self.months = mod * s
            self.years = div * s
        else:
            self.years = 0

    def _make_relativedelta(self, **kwargs) -> Self:
        """Factory method to create a new RelativeDelta with given overrides."""
        rel_fields = {field: kwargs.get(field, val) for field, val in self._relatives().items()}
        abs_fields = {field: kwargs.get(field, val) for field, val in self._absolutes().items()}
        return self.__class__(
            **rel_fields,
            **abs_fields,
            leapdays=kwargs.get("leapdays", self.leapdays),
            weekday=kwargs.get("weekday", self.weekday),
        )

    def normalized(self):
        """
        Return a version of this object represented entirely using integer
        values for the relative attributes.

        >>> RelativeDelta(days=1.5, hours=2).normalized()
        RelativeDelta(days=+1, hours=+14)

        :return:
            Returns a :class:`dateutilx.relativedelta.RelativeDelta` object.
        """
        # Cascade remainders down (rounding each to roughly nearest microsecond)
        days = int(self.days)

        hours_f = round(self.hours + 24 * (self.days - days), 11)
        hours = int(hours_f)

        minutes_f = round(self.minutes + 60 * (hours_f - hours), 10)
        minutes = int(minutes_f)

        seconds_f = round(self.seconds + 60 * (minutes_f - minutes), 8)
        seconds = int(seconds_f)

        microseconds = round(self.microseconds + 1e6 * (seconds_f - seconds))

        # Constructor carries overflow back up with call to _fix()
        return self._make_relativedelta(
            days=days, hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds
        )

    def __add__(self, other):
        if isinstance(other, RelativeDelta):
            kwargs = {
                field: val if getattr(other, field) is None else getattr(other, field)
                for field, val in self._absolutes().items()
            }
            return self._make_relativedelta(
                years=other.years + self.years,
                months=other.months + self.months,
                days=other.days + self.days,
                hours=other.hours + self.hours,
                minutes=other.minutes + self.minutes,
                seconds=other.seconds + self.seconds,
                microseconds=other.microseconds + self.microseconds,
                leapdays=other.leapdays or self.leapdays,
                **kwargs,
            )
        if isinstance(other, dt.timedelta):
            return self._make_relativedelta(
                days=self.days + other.days,
                seconds=self.seconds + other.seconds,
                microseconds=self.microseconds + other.microseconds,
            )

        if not isinstance(other, dt.date):
            return NotImplemented

        if self._has_time and not isinstance(other, dt.datetime):
            other = dt.datetime.fromordinal(other.toordinal())
        year = (self.year or other.year) + self.years
        month = self.month or other.month
        if self.months:
            assert 1 <= abs(self.months) <= 12
            month += self.months
            if month > 12:
                year += 1
                month -= 12
            elif month < 1:
                year -= 1
                month += 12
        day = min(calendar.monthrange(year, month)[1], self.day or other.day)
        repl = {"year": year, "month": month, "day": day}
        for attr in ["hour", "minute", "second", "microsecond"]:
            value = getattr(self, attr)
            if value is not None:
                repl[attr] = value
        days = self.days
        if self.leapdays and month > 2 and calendar.isleap(year):
            days += self.leapdays
        ret = other.replace(**repl) + dt.timedelta(
            days=days, hours=self.hours, minutes=self.minutes, seconds=self.seconds, microseconds=self.microseconds
        )
        if self.weekday:
            weekday, nth = self.weekday.weekday, self.weekday.n or 1
            jumpdays = (abs(nth) - 1) * 7
            if nth > 0:
                jumpdays += (7 - ret.weekday() + weekday) % 7
            else:
                jumpdays += (ret.weekday() - weekday) % 7
                jumpdays *= -1
            ret += dt.timedelta(days=jumpdays)
        return ret

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return self.__neg__().__radd__(other)

    def __sub__(self, other):
        if not isinstance(other, RelativeDelta):
            return NotImplemented  # In case the other object defines __rsub__

        kwargs = {field: getattr(other, field) if val is None else val for field, val in self._absolutes().items()}
        return self._make_relativedelta(
            years=self.years - other.years,
            months=self.months - other.months,
            days=self.days - other.days,
            hours=self.hours - other.hours,
            minutes=self.minutes - other.minutes,
            seconds=self.seconds - other.seconds,
            microseconds=self.microseconds - other.microseconds,
            leapdays=self.leapdays or other.leapdays,
            **kwargs,
        )

    def __abs__(self):
        fields = {field: abs(val) for field, val in self._relatives().items()}
        return self._make_relativedelta(**fields)

    def __neg__(self):
        fields = {field: -val for field, val in self._relatives().items()}
        return self._make_relativedelta(**fields)

    def __bool__(self) -> bool:
        return (
            any(value for value in self._relatives().values())
            or bool(self.leapdays)
            or bool(self.weekday)
            or any(value is not None for value in self._absolutes().values())
        )

    def __mul__(self, other) -> Self | NotImplementedType:
        try:
            f = float(other)
        except TypeError:
            return NotImplemented

        fields = {field: int(val * f) for field, val in self._relatives().items()}
        return self._make_relativedelta(**fields)

    __rmul__ = __mul__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RelativeDelta):
            return NotImplemented

        if bool(self.weekday) != bool(other.weekday):
            # if only 1 exists
            return False

        if self.weekday:
            if self.weekday.weekday != other.weekday.weekday:
                return False
            n1, n2 = self.weekday.n, other.weekday.n
            if n1 != n2 and not ((not n1 or n1 == 1) and (not n2 or n2 == 1)):
                return False

        return (
            all((a == b for a, b in zip(self._relatives().values(), other._relatives().values())))
            and all((a == b for a, b in zip(self._absolutes().values(), other._absolutes().values())))
            and self.leapdays == other.leapdays
            and self.weekday == other.weekday
        )

    def __hash__(self):
        # fmt: off
        return hash(
            (
                self.years, self.months, self.days, self.hours, self.minutes, self.seconds, self.microseconds,
                self.year, self.month, self.day, self.hour, self.minute, self.second, self.microsecond,
                self.leapdays, self.weekday,
            )
        )
        # fmt: on

    def __ne__(self, other):
        if not isinstance(other, RelativeDelta):
            return NotImplemented
        return not self.__eq__(other)

    def __truediv__(self, other) -> NotImplementedType | Self:
        try:
            reciprocal = 1 / float(other)
        except TypeError:
            return NotImplemented

        return self.__mul__(reciprocal)

    def __repr__(self):
        _tmp_list = []
        for attr in ["years", "months", "days", "leapdays", "hours", "minutes", "seconds", "microseconds"]:
            value = getattr(self, attr)
            if value:
                _tmp_list.append(f"{attr}={value:+g}")
        for attr in ["year", "month", "day", "weekday", "hour", "minute", "second", "microsecond"]:
            value = getattr(self, attr)
            if value is not None:
                _tmp_list.append(f"{attr}={value!r}")
        return f"{self.__class__.__name__}({', '.join(_tmp_list)})"


def _sign(x):
    return int(copysign(1, x))
