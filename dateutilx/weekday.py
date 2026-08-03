from typing import Any

from dateutilx.helper import Day


class NthWeekday:
    __slots__ = ["n", "weekday"]

    def __init__(self, wkday: Day, n: int | None = None):
        if n == 0:
            raise ValueError("Can't create nth-weekday with n==0")

        self.weekday = wkday
        self.n = n

    def __call__(self, n: int):
        return self if n == self.n else NthWeekday(self.weekday, n)

    def __eq__(self, other: Any) -> bool:
        try:
            return (self.weekday, self.n) == (other.weekday, other.n)
        except AttributeError:
            return False

    def __hash__(self):
        return hash((self.weekday, self.n))

    def __repr__(self) -> str:
        name = self.weekday.name
        return f"{name}({self.n:+d})" if self.n else name


# pylint: disable=r0903
class Weekday(NthWeekday):
    def __init__(self, wkday: int, n: int | None = None):
        if not 0 <= wkday <= 6:
            raise ValueError(f"Weekday must be between 0 and 6, got {wkday}")
        super().__init__(wkday=Day(wkday), n=n)


MO, TU, WE, TH, FR, SA, SU = weekdays = tuple(Weekday(x) for x in range(7))
