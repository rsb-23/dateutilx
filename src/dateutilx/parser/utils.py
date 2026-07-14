import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed

_SEP_TABLE = str.maketrans(" :.T-/\\", "_" * 7)

UNIQUE_FORMATS = (
    # _ separated formats
    "%Y_%m_%d_%H_%M_%S_%fZ",  # 2024-01-15T10:30:00.000000Z
    "%Y_%m_%d_%H_%M_%SZ",  # 2024-01-15T10:30:00Z
    "%Y_%m_%d_%H_%M_%S_%f",  # 2024-01-15T10:30:00.000000
    "%Y_%m_%d_%H_%M_%S",  # 2024-01-15T10:30:00
    "%Y_%m_%d_%H_%M",  # 2024-01-15T10:30
    "%Y_%m_%d",  # 2024-01-15
    # Compact / EXIF-style
    "%Y%m%d_%H%M%S%f",  # 20240115 103000000000
    "%Y%m%d_%H%M%S",  # 20240115T103000
    "%Y%m%d",  # 20240115
    # RFC 2822 / email-style
    "%a,_%d_%b_%Y_%H_%M_%S",  # Mon, 15 Jan 2024 10:30:00
    # Long-form
    "%B_%d,_%Y_%H_%M_%S",  # January 15, 2024 10:30:00
    "%B_%d,_%Y",  # January 15, 2024
    "%d_%B_%Y_%H_%M_%S",  # 15 January 2024 10:30:00
    "%d_%B_%Y",  # 15 January 2024
    "%B%d,%Y",
)

AMBIGIOUS_FORMAT = (
    # Slash-separated
    "%d/%m/%Y %H:%M:%S",  # 15/01/2024 10:30:00
    "%d/%m/%Y %H:%M",  # 15/01/2024 10:30
    "%d/%m/%Y",  # 15/01/2024
    "%m/%d/%Y %H:%M:%S",  # 01/15/2024 10:30:00
    "%m/%d/%Y %H:%M",  # 01/15/2024 10:30
    "%m/%d/%Y",  # 01/15/2024
    # Dot-separated (European)
    "%d.%m.%Y %H:%M:%S",  # 15.01.2024 10:30:00
    "%d.%m.%Y %H:%M",  # 15.01.2024 10:30
    "%d.%m.%Y",  # 15.01.2024
)


def _try_parse(timestr: str, fmt: str) -> dt.datetime | None:
    try:
        parsed = dt.datetime.strptime(timestr, fmt)

        reconstructed = parsed.strftime(fmt).lower()

        # normalise microsecond fields: strftime always emits 6 digits
        if "%f" in fmt:
            reconstructed = reconstructed.rstrip("0") or "0"
        if reconstructed != timestr:
            return None
        return parsed
    except ValueError:
        return None


def standard_dt_parser(timestr: str, max_workers: int = 3) -> dt.datetime:
    timestr = str(timestr).strip()
    timestr = timestr.translate(_SEP_TABLE)
    timestr = timestr.lower()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_try_parse, timestr, fmt): fmt for fmt in UNIQUE_FORMATS}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                # Cancel remaining futures
                for pending in futures:
                    pending.cancel()
                return result

    raise ValueError(f"Unknown format: {timestr!r}")


if __name__ == "__main__":
    print(_try_parse(timestr="may15,2021", fmt="%B%d,%Y"))
