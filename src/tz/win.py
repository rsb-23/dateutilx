"""
Wrapper for _win.py to handle platform dependent import
"""

from src.helper import is_windows_os

if is_windows_os():
    from ._win import TzRes, TzWin, TzWinLocal
else:
    TzRes = TzWin = TzWinLocal = None

# Alias
tzres = TzRes
tzwin = TzWin
tzwinlocal = TzWinLocal
