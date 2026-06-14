"""Type-narrowing helpers at the untyped-``Any`` / typed-domain boundary.

These functions exist so that callers reading values out of ``json.loads``
(or any other ``Any``-typed source) can hand them off to typed domain code
without sprinkling ``isinstance`` ladders through every call site. Each
helper returns ``None`` when the value is not of the expected shape; it
never raises and never silently widens the result type.
"""

from __future__ import annotations

from typing import Any


def as_int(value: Any) -> int | None:
    """Return ``value`` as ``int`` if it is a real number, else ``None``.

    Booleans are rejected explicitly: ``bool`` is a subclass of ``int`` in
    Python, but ``True``/``False`` are never meaningful integer payloads in
    our domain (e.g. an Extra Mana balance), so we don't want them to leak
    through as ``1``/``0``. Floats are truncated via ``int(value)``.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def as_str(value: Any) -> str | None:
    """Return ``value`` if it is a ``str``, else ``None``."""
    return value if isinstance(value, str) else None


def as_dict(value: Any) -> dict[str, Any] | None:
    """Return ``value`` if it is a ``dict``, else ``None``.

    JSON object keys are always strings, so callers can treat the result as
    ``dict[str, Any]``; the keys are not re-validated here.
    """
    return value if isinstance(value, dict) else None
