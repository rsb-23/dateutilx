from datetime import datetime

import pytest
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

from dateutilx import tz
from dateutilx.parser import isoparse

# Strategies
TIME_ZONE_STRATEGY = st.sampled_from(
    [None, tz.UTC] + [tz.gettz(zname) for zname in ("US/Eastern", "US/Pacific", "Australia/Sydney", "Europe/London")]
)
ASCII_STRATEGY = st.characters(max_codepoint=127)


@pytest.mark.isoparser
@settings(deadline=3000)
@given(dt_=st.datetimes(timezones=TIME_ZONE_STRATEGY), sep=ASCII_STRATEGY)
# Ambiguous in US/Eastern: the first 01:00 (EDT) and the second (EST)
@example(dt_=datetime(2020, 11, 1, 1, tzinfo=tz.gettz("US/Eastern")), sep="T")
@example(dt_=datetime(2020, 11, 1, 1, tzinfo=tz.gettz("US/Eastern"), fold=1), sep="T")
def test_timespec_auto(dt_, sep):
    if dt_.tzinfo is not None:
        # Assume offset has no sub-second components
        assume(dt_.utcoffset().total_seconds() % 60 == 0)

    dtstr = dt_.isoformat(sep=sep)
    dt_rt = isoparse(dtstr)

    # The round trip preserves the wall time and the offset.
    assert dt_rt.replace(tzinfo=None) == dt_.replace(tzinfo=None)
    assert dt_rt.utcoffset() == dt_.utcoffset()

    # According to PEP 495, if the value of fold would change the return value of utcoffset(),
    # comparisons with the datetime always return false, so we must handle the case of
    # ambiguous and imaginary datetimes here for the property to remain valid.
    if dt_.tzinfo is None or dt_.replace(fold=0).utcoffset() == dt_.replace(fold=1).utcoffset():
        assert dt_rt == dt_
    else:
        assert dt_rt != dt_
