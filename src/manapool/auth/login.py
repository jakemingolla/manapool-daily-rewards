"""Sign in via the SvelteKit ``/auth?/signin`` form action."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from manapool.config import Credentials, Settings
from manapool.errors import ManaPoolError, NotAuthenticated
from manapool.parsing import find_key, unflatten
from manapool.transport import Transport

# Verifies that a session is actually usable by fetching a SvelteKit
# ``__data.json`` endpoint. Provided by the client so this module need not
# depend on it directly.
SessionFetcher = Callable[[str], dict[str, Any]]


def login(
    transport: Transport,
    credentials: Credentials,
    settings: Settings,
    *,
    fetch: SessionFetcher,
) -> None:
    """Authenticate via the SvelteKit ``/auth?/signin`` form action.

    On success the ``mp-auth-token`` session cookie is stored in the transport's
    cookie jar. ``fetch`` is used to confirm the session actually works rather
    than trusting the cookie name.
    """
    resp = transport.post(
        f"{settings.base_url}/auth",
        params={"/signin": ""},
        data={
            "email": credentials.email,
            "password": credentials.password,
            "method": "password",
            "next": "/",
            "is_seller": "false",
        },
        headers={
            "Origin": settings.base_url,
            "Accept": "application/json",
            "x-sveltekit-action": "true",
        },
        allow_redirects=False,
        timeout=settings.timeout,
    )

    if resp.status_code >= 500:
        raise ManaPoolError(f"Sign-in failed: server returned {resp.status_code}")

    # The SvelteKit action returns a JSON result. A redirect type means success;
    # a failure type carries the error message produced by the auth handler.
    try:
        result = resp.json()
    except ValueError:
        result = None

    if isinstance(result, dict) and result.get("type") == "failure":
        message = extract_action_message(result) or "invalid credentials"
        raise ManaPoolError(f"Sign-in rejected: {message}")

    if not is_authenticated(fetch):
        message = extract_action_message(result) if isinstance(result, dict) else None
        raise ManaPoolError(
            "Sign-in did not establish a session"
            + (f" ({message})" if message else "")
        )


def extract_action_message(result: dict[str, Any]) -> str | None:
    """Pull a human-readable message out of a SvelteKit action result."""
    data = result.get("data")
    if isinstance(data, str):
        try:
            decoded = unflatten(json.loads(data))
        except (ValueError, IndexError, KeyError):
            return None
        for key in ("message", "text", "error"):
            found = find_key(decoded, key)
            if isinstance(found, str):
                return found
            if isinstance(found, dict):
                text = found.get("text") or found.get("message")
                if isinstance(text, str):
                    return text
    return None


def is_authenticated(fetch: SessionFetcher) -> bool:
    """Return whether the session backing ``fetch`` is logged in."""
    try:
        data = fetch("/__data.json")
    except NotAuthenticated:
        return False
    return bool(data.get("user"))
