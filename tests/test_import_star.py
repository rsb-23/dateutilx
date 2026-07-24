"""Test for the "import *" functionality.

As import * can be only done at module level, it has been added in a separate file
"""

import pytest

prev_locals = list(locals())
from src import *  # noqa

new_locals = {name: value for name, value in locals().items() if name not in prev_locals}
new_locals.pop("prev_locals")


@pytest.mark.import_star
def test_imported_modules():
    """Test that `from dateutil import *` adds modules in __all__ locally"""
    import src as dateutilx

    assert dateutilx.easter == new_locals.pop("easter")
    assert dateutilx.parser == new_locals.pop("parser")
    assert dateutilx.relativedelta == new_locals.pop("relativedelta")
    assert dateutilx.rrule == new_locals.pop("rrule")
    assert dateutilx.tz == new_locals.pop("tz")
