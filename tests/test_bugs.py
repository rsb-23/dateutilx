"""
It contains testcases for bugs raised in this or dateutil repo.
It can be later moved to respective category tests.
ups#1: upstream, GH#1: current repo
"""

from datetime import datetime

from dateutil import parser


def test_parse_colon_separated_date():
    """ups#1447"""
    result = parser.parse("2023:03:14 12:10:29")

    assert result == datetime(2023, 3, 14, 12, 10, 29)


def test_parse_nospace():
    """ups#1442"""
    result = parser.parse("20010203 040506789")
    assert result == datetime(2001, 2, 3, 4, 5, 6, 789000)


def test_parse_bd_year():
    """ups#1191"""
    result = parser.parse("may15,2021")
    assert result == datetime(2021, 5, 15, 0, 0)
