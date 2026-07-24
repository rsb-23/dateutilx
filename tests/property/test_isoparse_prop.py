import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src import tz
from src.parser import isoparse

# Strategies
TIME_ZONE_STRATEGY = st.sampled_from(
    [None, tz.UTC] + [tz.gettz(zname) for zname in ("US/Eastern", "US/Pacific", "Australia/Sydney", "Europe/London")]
)
ASCII_STRATEGY = st.characters(max_codepoint=127)


@pytest.mark.skip(reason="Needs fixing")
@pytest.mark.isoparser
@settings(deadline=3000)
@given(dt=st.datetimes(timezones=TIME_ZONE_STRATEGY), sep=ASCII_STRATEGY)
def test_timespec_auto(dt, sep):
    if dt.tzinfo is not None:
        # Assume offset has no sub-second components
        assume(dt.utcoffset().total_seconds() % 60 == 0)

    dtstr = dt.isoformat(sep=sep)
    dt_rt = isoparse(dtstr)

    assert dt_rt == dt
