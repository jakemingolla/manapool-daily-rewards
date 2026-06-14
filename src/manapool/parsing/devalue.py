"""Decode SvelteKit's devalue-flattened payloads.

See https://github.com/Rich-Harris/devalue for the wire format.
"""

from __future__ import annotations

import math
from typing import Any

# devalue sentinel indices.
_UNDEFINED = -1
_HOLE = -2
_NAN = -3
_POSITIVE_INFINITY = -4
_NEGATIVE_INFINITY = -5
_NEGATIVE_ZERO = -6


def unflatten(parsed: Any) -> Any:
    """Decode SvelteKit's devalue-flattened array into a Python value.

    The payload is a list where element 0 is the root and every field value is
    an integer index into the list (negative values are sentinels).
    """
    if isinstance(parsed, (int, float)) and not isinstance(parsed, bool):
        # A bare number means the whole value is a single sentinel/primitive.
        parsed = [parsed]

    values = parsed
    seen: dict[int, Any] = {}

    def hydrate(index: int) -> Any:
        if index == _UNDEFINED or index == _HOLE:
            return None
        if index == _NAN:
            return math.nan
        if index == _POSITIVE_INFINITY:
            return math.inf
        if index == _NEGATIVE_INFINITY:
            return -math.inf
        if index == _NEGATIVE_ZERO:
            return -0.0
        if index in seen:
            return seen[index]

        value = values[index]
        if value is None or not isinstance(value, (list, dict)):
            return value

        if isinstance(value, list):
            # A leading string element marks a typed value (Date, Set, ...).
            if value and isinstance(value[0], str):
                tag = value[0]
                if tag == "Date":
                    return value[1]  # keep the ISO string
                if tag == "BigInt":
                    return int(value[1])
                if tag in ("RegExp", "Object"):
                    return value[1]
                if tag == "Set":
                    result_set: list[Any] = []
                    seen[index] = result_set
                    for i in value[1:]:
                        result_set.append(hydrate(i))
                    return result_set
                if tag == "Map":
                    result_map: dict[Any, Any] = {}
                    seen[index] = result_map
                    rest = value[1:]
                    for i in range(0, len(rest) - 1, 2):
                        result_map[hydrate(rest[i])] = hydrate(rest[i + 1])
                    return result_map
                # Unknown tag: fall through and treat as a plain array.
            array: list[Any] = []
            seen[index] = array
            for i in value:
                array.append(None if i == _HOLE else hydrate(i))
            return array

        obj: dict[str, Any] = {}
        seen[index] = obj
        for key, i in value.items():
            obj[key] = hydrate(i)
        return obj

    return hydrate(0)
