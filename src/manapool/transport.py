"""HTTP transport seam.

Everything that talks to the network goes through a ``Transport``. The real
implementation wraps a ``requests.Session``; tests inject a fake.
"""

from __future__ import annotations

from typing import Any, Protocol

import requests

from manapool.config import Settings


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

    @property
    def cookies(self) -> Any:
        return self._session.cookies

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self._session.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self._session.post(url, **kwargs)
