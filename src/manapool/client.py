"""High-level Mana Pool API client built on top of an injected transport."""

from __future__ import annotations

import json
from typing import Any

from manapool import endpoints
from manapool.auth import login as auth_login
from manapool.auth import supabase_session_from_cookies
from manapool.config import Credentials, Settings
from manapool.console import Console, StreamConsole
from manapool.errors import ManaPoolError, NotAuthenticated
from manapool.models import ClaimResult, Status
from manapool.parsing import find_key, unflatten
from manapool.transport import Transport

_REDIRECT_CODES = (301, 302, 303, 307, 308)


class ManaPoolClient:
    """Talks to Mana Pool's SvelteKit + Supabase HTTP endpoints.

    All network access goes through ``transport`` so the client can be driven
    by a fake in tests.
    """

    def __init__(
        self,
        transport: Transport,
        settings: Settings | None = None,
        console: Console | None = None,
    ) -> None:
        self._transport = transport
        self._settings = settings if settings is not None else Settings()
        self._console = console if console is not None else StreamConsole()

    def login(self, credentials: Credentials) -> None:
        """Authenticate via the SvelteKit ``/auth?/signin`` form action."""
        auth_login(
            self._transport,
            credentials,
            self._settings,
            fetch=self.fetch_node_data,
        )

    def fetch_node_data(self, path: str) -> dict[str, Any]:
        """Fetch a SvelteKit ``__data.json`` endpoint and merge all node data."""
        resp = self._transport.get(
            f"{self._settings.base_url}{path}",
            headers={"Accept": "application/json"},
            allow_redirects=False,
            timeout=self._settings.timeout,
        )
        location = resp.headers.get("location", "")
        self._console.debug(
            f"[debug] GET {path} -> {resp.status_code}"
            + (f" location={location}" if location else "")
        )
        if resp.status_code in _REDIRECT_CODES:
            raise NotAuthenticated(f"{path} redirected (not authenticated)")

        try:
            payload = resp.json()
        except ValueError as exc:
            raise ManaPoolError(f"Unexpected non-JSON response from {path}") from exc

        if payload.get("type") == "redirect":
            raise NotAuthenticated(f"{path} returned a redirect (not authenticated)")
        if payload.get("type") != "data":
            raise ManaPoolError(f"Unexpected response shape from {path}: {payload!r}")

        merged: dict[str, Any] = {}
        nodes = payload.get("nodes", [])
        for position, node in enumerate(nodes):
            if not node:
                self._console.debug(f"[debug]   node[{position}]: empty")
                continue
            node_type = node.get("type")
            if node_type != "data" or not node.get("data"):
                self._console.debug(f"[debug]   node[{position}]: type={node_type}")
                continue
            decoded = unflatten(node["data"])
            if isinstance(decoded, dict):
                self._console.debug(
                    f"[debug]   node[{position}] keys: {sorted(decoded.keys())}"
                )
                merged.update(decoded)
            else:
                self._console.debug(
                    f"[debug]   node[{position}]: non-dict {type(decoded).__name__}"
                )
        return merged

    def fetch_extra_mana(self) -> dict[str, Any]:
        """Read the current Extra Mana balance from Supabase (PostgREST).

        The ``/settings/extra-mana`` page uses a browser-side universal load, so
        the balance is not present in ``__data.json``; we query the database
        directly, scoped to the user by row-level security via their access
        token. The request is routed through the same transport; requests scopes
        cookies by domain, so the manapool.com auth cookie is never sent to
        sb-api.manapool.com and only the explicit Bearer token authorizes it.
        """
        supa = supabase_session_from_cookies(
            self._transport.cookies,
            self._settings.auth_cookie_name,
            console=self._console,
        )
        token = supa.get("access_token") if isinstance(supa, dict) else None
        if not token:
            return {}

        url = f"{self._settings.supabase_url}{endpoints.EXTRA_MANA}"
        resp = self._transport.get(
            url,
            params={"select": "points,pending_points"},
            headers={
                "apikey": self._settings.supabase_anon_key,
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=self._settings.timeout,
        )
        self._console.debug(f"[debug] GET {url} -> {resp.status_code}")
        if resp.status_code != 200:
            return {}
        try:
            rows = resp.json()
        except ValueError:
            return {}
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            return rows[0]
        return {}

    def get_status(self) -> Status:
        """Collect Daily Reward eligibility and Extra Mana balance."""
        daily = self.fetch_node_data(endpoints.DAILY_DATA)
        balance = self.fetch_extra_mana()

        form = daily.get("form")
        return Status(
            already_claimed=bool(daily.get("alreadyClaimed")),
            eligible=bool(daily.get("hasRecentOrder")),
            seconds_until_reset=int(daily.get("secondsUntilMidnightTonight") or 0),
            extra_mana_available=balance.get("points"),
            pending_extra_mana=balance.get("pending_points"),
            claim_form_data=find_key(form, "data") if form else None,
        )

    def claim(self, form_data: Any) -> ClaimResult:
        """Submit the Daily Reward claim via the default ``POST /daily`` action."""
        body: dict[str, str] = {}
        if isinstance(form_data, dict):
            for key, value in form_data.items():
                if value is None:
                    continue
                if value is True:
                    body[key] = "true"
                elif value is False:
                    body[key] = "false"
                else:
                    body[key] = str(value)

        resp = self._transport.post(
            f"{self._settings.base_url}{endpoints.CLAIM_DAILY}",
            data=body,
            headers={
                "Origin": self._settings.base_url,
                "Accept": "application/json",
                "x-sveltekit-action": "true",
                # SvelteKit form actions parse the body with request.formData();
                # set the form content type explicitly so an empty body (no claim
                # fields) is still accepted instead of rejected with HTTP 415.
                "Content-Type": "application/x-www-form-urlencoded",
            },
            allow_redirects=False,
            timeout=self._settings.timeout,
        )
        if resp.status_code >= 400:
            raise ManaPoolError(f"Claim failed: server returned {resp.status_code}")

        award_amount: Any = None
        award_title: Any = None
        try:
            result = resp.json()
        except ValueError:
            result = None

        if isinstance(result, dict) and isinstance(result.get("data"), str):
            try:
                decoded = unflatten(json.loads(result["data"]))
                award_amount = find_key(decoded, "awardAmount")
                award_title = find_key(decoded, "awardTitle")
            except (ValueError, IndexError, KeyError):
                pass

        return ClaimResult(award_amount=award_amount, award_title=award_title)
