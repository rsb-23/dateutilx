==
tz
==
.. py:currentmodule:: dateutilx.tz

.. automodule:: dateutilx.tz

Objects
-------
.. py:data:: dateutilx.tz.UTC

    A convenience instance of :class:`dateutilx.tz.tzutc`.

    .. versionadded:: 2.7.0

Functions
---------

.. autofunction:: gettz

    .. automethod:: gettz.nocache
    .. automethod:: gettz.cache_clear


.. autofunction:: datetime_ambiguous
.. autofunction:: datetime_exists

.. autofunction:: resolve_imaginary


Classes
-------

.. autoclass:: tzutc

.. autoclass:: tzoffset

.. autoclass:: tzlocal

.. autoclass:: tzwinlocal
    :members: display, transitions

    .. note::

        Only available on Windows

.. autoclass:: tzrange

.. autoclass:: tzstr

.. autoclass:: tzical
    :members:

.. autoclass:: tzwin
    :members: display, transitions, list

    .. note::

        Only available on Windows
