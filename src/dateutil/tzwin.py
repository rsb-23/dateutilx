# tzwin has moved to dateutil.tz.win
from .tz.win import TzRes, TzWin, TzWinLocal  # noqa

__all__ = ["TzRes", "TzWin", "TzWinLocal"]

tzres = TzRes
tzwin = TzWin
tzwinlocal = TzWinLocal
