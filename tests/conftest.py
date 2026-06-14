"""Shared test fakes: transport, responses, cookies, console, and client."""

from __future__ import annotations

from typing import Any

from manapool.errors import ManaPoolError
from manapool.models import ClaimResult, Status

_UNSET = object()


class FakeResponse:
    """Stand-in for ``requests.Response`` with a canned body."""

    def __init__(
        self,
        *,
        status_code: int = 200,
        json_data: Any = _UNSET,
        headers: dict[str, str] | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self._json = json_data
        self.headers = headers or {}
        self.text = text

    def json(self) -> Any:
        if self._json is _UNSET:
            raise ValueError("response body is not JSON")
        return self._json


class FakeCookie:
    def __init__(self, name: str, value: str) -> None:
        self.name = name
        self.value = value


class FakeCookieJar:
    def __init__(self, cookies: list[FakeCookie] | None = None) -> None:
        self._cookies = list(cookies or [])

    def add(self, name: str, value: str) -> None:
        self._cookies.append(FakeCookie(name, value))

    def __iter__(self):
        return iter(self._cookies)


class FakeTransport:
    """Routes requests to canned responses by URL substring, recording calls."""

    def __init__(self, cookies: list[FakeCookie] | None = None) -> None:
        self._cookies = FakeCookieJar(cookies)
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self._routes: dict[str, list[tuple[str, FakeResponse]]] = {
            "GET": [],
            "POST": [],
        }

    @property
    def cookies(self) -> FakeCookieJar:
        return self._cookies

    def register(self, method: str, fragment: str, response: FakeResponse) -> None:
        self._routes[method].append((fragment, response))

    def _respond(self, method: str, url: str, kwargs: dict[str, Any]) -> FakeResponse:
        self.calls.append((method, url, kwargs))
        for fragment, response in self._routes[method]:
            if fragment in url:
                return response
        raise AssertionError(f"unexpected {method} {url}")

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        return self._respond("GET", url, kwargs)

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        return self._respond("POST", url, kwargs)


class RecordingConsole:
    """``Console`` that captures everything written to it."""

    def __init__(self) -> None:
        self.out_lines: list[str] = []
        self.err_lines: list[str] = []
        self.debug_lines: list[str] = []

    def out(self, message: str) -> None:
        self.out_lines.append(message)

    def err(self, message: str) -> None:
        self.err_lines.append(message)

    def debug(self, message: str) -> None:
        self.debug_lines.append(message)


class FakeClient:
    """Stands in for ``ManaPoolClient`` in service-level tests."""

    def __init__(
        self,
        *,
        statuses: list[Status] | None = None,
        claim_result: ClaimResult | None = None,
        login_error: ManaPoolError | None = None,
        status_error: ManaPoolError | None = None,
        claim_error: ManaPoolError | None = None,
    ) -> None:
        self._statuses = list(statuses or [])
        self._claim_result = claim_result or ClaimResult()
        self._login_error = login_error
        self._status_error = status_error
        self._claim_error = claim_error
        self.login_calls: list[Any] = []
        self.claim_calls: list[Any] = []
        self.status_calls = 0

    def login(self, credentials: Any) -> None:
        self.login_calls.append(credentials)
        if self._login_error is not None:
            raise self._login_error

    def get_status(self) -> Status:
        self.status_calls += 1
        if self._status_error is not None:
            raise self._status_error
        if not self._statuses:
            raise AssertionError("get_status called more times than expected")
        if len(self._statuses) == 1:
            return self._statuses[0]
        return self._statuses.pop(0)

    def claim(self, form_data: Any) -> ClaimResult:
        self.claim_calls.append(form_data)
        if self._claim_error is not None:
            raise self._claim_error
        return self._claim_result
