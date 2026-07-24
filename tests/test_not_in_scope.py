"""
Covers testcases which are either out of scope of this project or not feasible to support.
"""

from datetime import datetime

import pytest

from src.errors import ParserError
from src.parser import parse


class TestParseUnimplementedCases:
    tzinfos = None

    @pytest.mark.xfail
    def test_somewhat_ambiguous_string(self):
        # Ref: github issue #487
        # The parser is choosing the wrong part for hour causing datetime to raise an exception.
        dtstr = "1237 PM BRST Mon Oct 30 2017"
        res = parse(dtstr, tzinfo=self.tzinfos)
        assert res == datetime(2017, 10, 30, 12, 37, tzinfo=self.tzinfos)

    @pytest.mark.xfail
    def test_ymdh_m_s(self):
        # found in nasdaq's ftp data
        dstr = "1991041310:19:24"
        expected = datetime(1991, 4, 13, 10, 19, 24)
        res = parse(dstr)
        assert res == expected, (res, expected)

    @pytest.mark.xfail
    def test_first_century(self):
        dstr = "0031 Nov 03"
        expected = datetime(31, 11, 3)
        res = parse(dstr)
        assert res == expected, res

    @pytest.mark.xfail
    def test_era_trailing_year_with_dots(self):
        dstr = "A.D.2001"
        res = parse(dstr)
        assert res.year == 2001, res

    @pytest.mark.xfail
    def test_ad_nospace(self):
        expected = datetime(6, 5, 19)
        for dstr in [" 6AD May 19", " 06AD May 19", " 006AD May 19", " 0006AD May 19"]:
            res = parse(dstr)
            assert res == expected, (dstr, res)

    @pytest.mark.xfail
    def test_four_letter_day(self):
        dstr = "Frid Dec 30, 2016"
        expected = datetime(2016, 12, 30)
        res = parse(dstr)
        assert res == expected

    @pytest.mark.xfail
    def test_non_date_number(self):
        dstr = "1,700"
        with pytest.raises(ParserError):
            parse(dstr)

    @pytest.mark.xfail
    def test_on_era(self):
        # This could be classified as an "eras" test, but the relevant part
        # about this is the ` on `
        dstr = "2:15 PM on January 2nd 1973 A.D."
        expected = datetime(1973, 1, 2, 14, 15)
        res = parse(dstr)
        assert res == expected

    @pytest.mark.xfail
    def test_extraneous_year(self):
        # This was found in the wild at insidertrading.org
        dstr = "2011 MARTIN CHILDREN'S IRREVOCABLE TRUST u/a/d NOVEMBER 7, 2012"
        res = parse(dstr, fuzzy_with_tokens=True)
        expected = datetime(2012, 11, 7)
        assert res == expected

    @pytest.mark.xfail
    def test_extraneous_year_tokens(self):
        # This was found in the wild at insidertrading.org
        # Unlike in the case above, identifying the first "2012" as the year
        # would not be a problem, but inferring that the latter 2012 is hhmm
        # is a problem.
        dstr = "2012 MARTIN CHILDREN'S IRREVOCABLE TRUST u/a/d NOVEMBER 7, 2012"
        expected = datetime(2012, 11, 7)
        res, tokens = parse(dstr, fuzzy_with_tokens=True)  # pylint: disable=e0633
        assert res == expected
        assert tokens == ("2012 MARTIN CHILDREN'S IRREVOCABLE TRUST u/a/d ",)

    @pytest.mark.xfail
    def test_extraneous_year2(self):
        # This was found in the wild at insidertrading.org
        dstr = "Berylson Amy Smith 1998 Grantor Retained Annuity Trust u/d/t November 2, 1998 f/b/o Jennifer L Berylson"
        res = parse(dstr, fuzzy_with_tokens=True)
        expected = datetime(1998, 11, 2)
        assert res == expected

    @pytest.mark.xfail
    def test_extraneous_year3(self):
        # This was found in the wild at insidertrading.org
        dstr = "SMITH R &  WEISS D 94 CHILD TR FBO M W SMITH UDT 12/1/1994"
        res = parse(dstr, fuzzy_with_tokens=True)
        expected = datetime(1994, 12, 1)
        assert res == expected

    @pytest.mark.xfail
    def test_unambiguous_yyyymm(self):
        # 171206 can be parsed as YYMMDD. However, 201712 cannot be parsed
        # as instance of YYMMDD and parser could fallback to YYYYMM format.
        dstr = "201712"
        res = parse(dstr)
        expected = datetime(2017, 12, 1)
        assert res == expected

    @pytest.mark.xfail
    def test_extraneous_numerical_content(self):
        # ref: https://github.com/dateutil/dateutil/issues/1029
        # parser interprets price and percentage as parts of the date
        dstr = "£14.99 (25% off, until April 20)"
        res = parse(dstr, fuzzy=True, default=datetime(2000, 1, 1))
        expected = datetime(2000, 4, 20)
        assert res == expected
