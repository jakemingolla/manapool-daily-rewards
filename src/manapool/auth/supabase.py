"""Reconstruct the Supabase session stored in the ``mp-auth-token`` cookie."""

from __future__ import annotations

import base64
import binascii
import json
import urllib.parse
from collections.abc import Iterable
from typing import Any

from manapool.console import Console


def supabase_session_from_cookies(
    cookies: Iterable[Any],
    auth_cookie_name: str,
    *,
    console: Console | None = None,
) -> dict[str, Any] | None:
    """Reconstruct the Supabase session stored in the auth cookie.

    @supabase/ssr stores the session as ``base64-<base64url(JSON)>`` and splits
    long values across ``mp-auth-token.0``, ``mp-auth-token.1``, etc.
    """
    whole: str | None = None
    chunks: dict[int, str] = {}
    cookie_list = list(cookies)
    for cookie in cookie_list:
        if cookie.name == auth_cookie_name:
            whole = cookie.value
        elif cookie.name.startswith(auth_cookie_name + "."):
            suffix = cookie.name[len(auth_cookie_name) + 1 :]
            if suffix.isdigit():
                chunks[int(suffix)] = cookie.value or ""

    if chunks:
        raw = "".join(chunks[i] for i in sorted(chunks))
    elif whole is not None:
        raw = whole
    else:
        if console is not None:
            names = sorted(c.name for c in cookie_list)
            console.debug(f"[debug] no auth cookie found; cookies={names}")
        return None

    raw = urllib.parse.unquote(raw)
    if raw.startswith("base64-"):
        encoded = raw[len("base64-") :]
        padded = encoded + "=" * (-len(encoded) % 4)
        for decoder in (base64.urlsafe_b64decode, base64.b64decode):
            try:
                return json.loads(decoder(padded))
            except (binascii.Error, ValueError):
                continue
        if console is not None:
            console.debug("[debug] failed to decode base64 auth cookie")
        return None

    try:
        return json.loads(raw)
    except ValueError:
        if console is not None:
            console.debug("[debug] auth cookie is not JSON")
        return None
