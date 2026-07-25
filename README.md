> [!NOTE]
> This package is rewrite of `python-dateutil v2.9.0.post0` as base, to support active python versions only.  
> It is not related with the base project and its authors.  
> Docs of base project are under `.base_project/`

# dateutilx - powerful extensions to datetime

|                |                                                                                             |
|----------------|---------------------------------------------------------------------------------------------|
| Compatibility  | ![Py-Version]                                                                               |
| Quality Checks | [![lint check][lint-badge]]() [![tests][tests-badge]]() [![pre-commit][pre-commit-badge]]() |
| Package        | ![pypi-v] ![pypi-downloads]                                                                 |
| MetaData       | [![license-badge]][license]                                                                 |                                                                                                                                                                                           

The `dateutilx` module provides powerful extensions to the standard `datetime` module, available in Python.

## Installation

`dateutilx` can be installed from PyPI using `pip`

```
pip install dateutilx
```

## Download

dateutilx is available on PyPI
https://pypi.org/project/dateutilx/

The documentation is hosted at:
https://dateutilx.readthedocs.io/en/stable/

## Code

The code and issue tracker are hosted on GitHub:
https://github.com/rsb-23/dateutilx/

## Features

* Computing of relative deltas (next month, next year, next Monday, last week of month, etc);
* Computing of relative deltas between two given date and/or datetime objects;
* Computing of dates based on very flexible recurrence rules, using a superset of
  the [iCalendar](https://www.ietf.org/rfc/rfc2445.txt) specification. Parsing of RFC strings is supported as well.
* Generic parsing of dates in almost any string format;
* Timezone (tzinfo) implementations for tzfile (5) format files (/etc/localtime, /usr/share/zoneinfo, etc), TZ
  environment string (in all known formats), iCalendar format files, given ranges (with help from relative deltas),
  local machine timezone, fixed offset timezone, UTC timezone, and Windows registry-based time zones.
* Internal up-to-date world timezone information based on Olson's database.
* Computing of Easter Sunday dates for any given year, using Western, Orthodox or Julian algorithms;
* A comprehensive test suite.

## Quick example

Here's a snapshot, just to give an idea about the power of the package. For more examples, look at the documentation.

Suppose you want to know how much time is left, in years/months/days/etc, before the next easter happening on a year
with a Friday 13th in August, and you want to get today's date out of the "date" unix system command. Here is the code:

```pycon
>>> from datetime import *
>>> from dateutilx.easter import *
>>> from dateutilx.parser import *
>>> from dateutilx.relativedelta import RelativeDelta
>>> from dateutilx.rrule import *
>>> 
>>> now = parse("Sat Oct 11 17:13:46 UTC 2003")
>>> today = now.date()
>>> year = rrule(YEARLY, dtstart=now, bymonth=8, bymonthday=13, byweekday=FR)[0].year
>>> rdelta = relativedelta(easter(year), today)
>>> print("Today is: %s" % today)
"Today is: 2003-10-11"
>>> print("Year with next Aug 13th on a Friday is: %s" % year)
"Year with next Aug 13th on a Friday is: 2004"
>>> print("How far is the Easter of that year: %s" % rdelta)
"How far is the Easter of that year: RelativeDelta(months=+6)"
>>> print("And the Easter of that year is: %s" % (today + rdelta))
"And the Easter of that year is: 2004-04-11"
```

Being exactly 6 months ahead was **really** a coincidence :)

## Contributing

We welcome many types of contributions - bug reports, pull requests (code, infrastructure or documentation fixes). For
more information about how to contribute to the project, see the `CONTRIBUTING.md` file in the repository.

## Author

The dateutilx module is improved/re-written by rsb-23 in 2026.

## License

All contributions after December 1, 2017 released under dual license -
either [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0) or
the [BSD 3-Clause License](https://opensource.org/licenses/BSD-3-Clause). Contributions before December 1, 2017 - except
those those explicitly relicensed - are released only under the BSD 3-Clause License.


[license]: https://github.com/rsb-23/dateutilx/blob/main/LICENSE
[lint-badge]: https://github.com/rsb-23/dateutilx/actions/workflows/code-lint.yml/badge.svg
[tests-badge]: https://github.com/rsb-23/dateutilx/actions/workflows/code-test.yml/badge.svg

[license-badge]: https://img.shields.io/pypi/l/dateutilx.svg?style=flat-square
[pre-commit-badge]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
[py-version]: https://img.shields.io/pypi/pyversions/dateutilx
[pypi-downloads]: https://img.shields.io/pypi/dm/dateutilx?label=Downloads
[pypi-v]: https://img.shields.io/pypi/v/dateutilx?label=pypi
