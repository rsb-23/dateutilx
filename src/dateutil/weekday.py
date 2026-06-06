from dateutil.helper import Day


class NthWeekday:
    def __init__(self, weekday: Day, n: int | None = None):
        if n == 0:
            raise ValueError("Can't create nth-weekday with n==0")

        self.weekday = weekday
        self.n = n

    def __call__(self, n: int):
        if n == self.n:
            return self
        return NthWeekday(self.weekday, n)

    def __eq__(self, other) -> bool:
        try:
            if self.weekday != other.weekday or self.n != other.n:
                return False
        except AttributeError:
            return False
        return True

    def __repr__(self):
        name = self.weekday.name
        return f"{name}({self.n:+d})" if self.n else name


# pylint: disable=r0903
class Weekday(NthWeekday):
    def __init__(self, weekday_: int, n: int | None = None):
        super().__init__(weekday=Day(weekday_), n=n)


MO, TU, WE, TH, FR, SA, SU = weekdays = tuple(Weekday(x) for x in range(7))

# Alias
weekday = Weekday
