import unittest

from dateutil.weekday import FR, MO, SA, SU, TH, TU, WE, Weekday


class WeekdayTest(unittest.TestCase):
    def testInvalidNthWeekday(self):
        with self.assertRaises(ValueError):
            FR(0)

    def testWeekdayCallable(self):
        # Calling a weekday instance generates a new weekday instance with the
        # value of n changed.

        self.assertEqual(MO(1), Weekday(0, 1))

        # Calling a weekday instance with the identical n returns the original object
        fr_3 = Weekday(4, 3)
        self.assertIs(fr_3(3), fr_3)

    def testWeekdayEquality(self):
        # Two weekday objects are not equal if they have different values for n
        self.assertNotEqual(TH, TH(-1))
        self.assertNotEqual(SA(3), SA(2))

    def testWeekdayEqualitySubclass(self):
        # Two weekday objects equal if their "weekday" and "n" attributes are available and the same
        class BasicWeekday:
            def __init__(self, weekday):
                self.weekday = weekday

        class BasicNWeekday(BasicWeekday):
            def __init__(self, weekday, n=None):
                super().__init__(weekday)
                self.n = n

        mo_basic = BasicWeekday(0)

        self.assertNotEqual(MO, mo_basic)
        self.assertNotEqual(MO(1), mo_basic)

        tu_basicn = BasicNWeekday(1)

        self.assertEqual(TU, tu_basicn)
        self.assertNotEqual(TU(3), tu_basicn)

        we_basic3 = BasicNWeekday(2, 3)
        self.assertEqual(WE(3), we_basic3)
        self.assertNotEqual(WE(2), we_basic3)

    def testWeekdayReprNoN(self):
        no_n_reprs = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")
        no_n_wdays = (MO, TU, WE, TH, FR, SA, SU)

        for repstr, wday in zip(no_n_reprs, no_n_wdays):
            self.assertEqual(repr(wday), repstr)

    def testWeekdayReprWithN(self):
        with_n_reprs = ("WE(+1)", "TH(-2)", "SU(+3)")
        with_n_wdays = (WE(1), TH(-2), SU(+3))

        for repstr, wday in zip(with_n_reprs, with_n_wdays):
            self.assertEqual(repr(wday), repstr)
