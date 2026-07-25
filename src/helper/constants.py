import calendar
from enum import IntEnum


class Frequency(IntEnum):
    YEARLY = 0
    MONTHLY = 1
    WEEKLY = 2
    DAILY = 3
    HOURLY = 4
    MINUTELY = 5
    SECONDLY = 6


class Day(IntEnum):
    MO = 0
    TU = 1
    WE = 2
    TH = 3
    FR = 4
    SA = 5
    SU = 6

    # Alias
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6

    @property
    def full_name(self):
        return calendar.day_name[self.value]

    @property
    def short_name(self):
        return calendar.day_abbr[self.value]


class Month(IntEnum):
    JAN = 1
    FEB = 2
    MAR = 3
    APR = 4
    MAY = 5
    JUN = 6
    JUL = 7
    AUG = 8
    SEP = 9
    OCT = 10
    NOV = 11
    DEC = 12

    @property
    def full_name(self):
        return calendar.month_name[self.value]

    @property
    def short_name(self):
        return calendar.month_abbr[self.value]
