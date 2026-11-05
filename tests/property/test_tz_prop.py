from datetime import datetime, timedelta

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from dateutilx import tz

EPOCH = datetime(1970, 1, 1)
EPOCHALYPSE = EPOCH + timedelta(seconds=2**31 - 1)
NEGATIVE_EPOCHALYPSE = EPOCH - timedelta(seconds=2**31)


@pytest.mark.gettz
@pytest.mark.parametrize("gettz_arg", [None, ""])
# TODO: Remove bounds when GH #590 is resolved
@given(dt=st.datetimes(min_value=NEGATIVE_EPOCHALYPSE, max_value=EPOCHALYPSE, timezones=st.just(tz.UTC)))
# 01:15 in America/New_York on a fall-back day, i.e. ambiguous local time.
@example(dt=datetime(2005, 10, 30, 5, 15, tzinfo=tz.UTC))
# 01:00 in America/New_York on a fall-back day: CI's falsifying example.
@example(dt=datetime(2015, 11, 1, 5, 0, tzinfo=tz.UTC))
@example(dt=NEGATIVE_EPOCHALYPSE.replace(tzinfo=tz.UTC))
@example(dt=EPOCHALYPSE.replace(tzinfo=tz.UTC))
def test_gettz_returns_local(gettz_arg, dt):
    act_tz = tz.gettz(gettz_arg)
    if isinstance(act_tz, tz.TzLocal):
        return

    dt_act = dt.astimezone(act_tz)
    dt_exp = dt.astimezone()

    assert dt_act.astimezone(tz.UTC) == dt_exp.astimezone(tz.UTC)
    assert dt_act.tzname() == dt_exp.tzname()
    assert dt_act.utcoffset() == dt_exp.utcoffset()

    # According to PEP 495, if the value of fold would change the return value
    # of utcoffset(), comparisons with the datetime always return false, so we
    # must handle the case of ambiguous and imaginary datetimes here for the
    # property to remain valid.
    if dt_act.replace(fold=0).utcoffset() == dt_act.replace(fold=1).utcoffset():
        assert dt_act == dt_exp
    else:
        # Check that the system time zone also considers the local wall time
        # ambiguous. This must be done on the naive wall time:
        # fold has no effect on the UTC-aware dt, and dt_exp carries a fixed offset.
        wall = dt_exp.replace(tzinfo=None)
        assert wall.replace(fold=0).astimezone().utcoffset() != wall.replace(fold=1).astimezone().utcoffset()
        assert dt_act != dt_exp
