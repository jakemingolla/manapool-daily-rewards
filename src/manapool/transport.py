"""HTTP transport seam.

Everything that talks to the network goes through a ``Transport``. The real
implementation wraps a ``requests.Session``; tests inject a fake.
"""

from __future__ import annotations

from typing import Any, Protocol

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from manapool.config import Settings

# Retry transient server/network failures on idempotent methods only. The
# daily-rewards CLI runs unattended (cron), so surviving a brief 5xx or socket
# blip is worth a few hundred milliseconds; POSTs (the claim itself) are
# deliberately excluded to avoid duplicate submissions.
_RETRY_TOTAL = 3
_RETRY_BACKOFF_FACTOR = 0.5
_RETRY_STATUS_FORCELIST = (429, 500, 502, 503, 504)
_RETRY_ALLOWED_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def _build_retry_adapter() -> HTTPAdapter:
    retry = Retry(
        total=_RETRY_TOTAL,
        backoff_factor=_RETRY_BACKOFF_FACTOR,
        status_forcelist=_RETRY_STATUS_FORCELIST,
        allowed_methods=_RETRY_ALLOWED_METHODS,
        respect_retry_after_header=True,
        # Surface the final response to callers; they already inspect
        # ``status_code`` and decide how to react.
        raise_on_status=False,
    )
    return HTTPAdapter(max_retries=retry)


class Transport(Protocol):
    """Minimal HTTP surface the client and auth layers depend on."""

    @property
    def cookies(self) -> Any:
        """Cookie jar (iterable of objects with ``name``/``value``)."""
        ...

    def get(self, url: str, **kwargs: Any) -> requests.Response: ...

    def post(self, url: str, **kwargs: Any) -> requests.Response: ...


class RequestsTransport:
    """``Transport`` backed by a persistent ``requests.Session``."""

    def __init__(self, settings: Settings) -> None:
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": settings.user_agent})
        adapter = _build_retry_adapter()
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    @property
    def cookies(self) -> Any:
        return self._session.cookies

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self._session.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self._session.post(url, **kwargs)
