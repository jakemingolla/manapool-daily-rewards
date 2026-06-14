"""Search helpers for nested decoded structures."""

from __future__ import annotations

from typing import Any


def find_key(node: Any, key: str) -> Any:
    """Depth-first search a nested structure for the first value of ``key``."""
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for child in node.values():
            found = find_key(child, key)
            if found is not None:
                return found
    elif isinstance(node, list):
        for child in node:
            found = find_key(child, key)
            if found is not None:
                return found
    return None
