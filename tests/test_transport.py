"""Tests for the real ``RequestsTransport`` wiring (no network)."""

from __future__ import annotations

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from manapool.config import Settings
from manapool.transport import RequestsTransport


def test_user_agent_is_applied_to_session():
    transport = RequestsTransport(Settings(user_agent="ua/1"))
    assert transport._session.headers["User-Agent"] == "ua/1"


def test_retry_adapter_mounted_for_http_and_https():
    transport = RequestsTransport(Settings())
    http = transport._session.get_adapter("http://example.com")
    https = transport._session.get_adapter("https://example.com")
    assert isinstance(http, HTTPAdapter)
    assert isinstance(https, HTTPAdapter)
    # Same adapter instance is reused across schemes.
    assert http is https


def test_retry_policy_is_idempotent_only_and_targets_transient_failures():
    transport = RequestsTransport(Settings())
    adapter = transport._session.get_adapter("https://example.com")
    retry = adapter.max_retries
    assert isinstance(retry, Retry)
    assert retry.total == 3
    assert retry.backoff_factor == 0.5
    # POST must never be retried (claim submissions are not idempotent).
    assert retry.allowed_methods is not None
    assert "POST" not in retry.allowed_methods
    assert {"GET", "HEAD", "OPTIONS"}.issubset(retry.allowed_methods)
    # Retry on transient server-side failures (and rate limits).
    assert retry.status_forcelist is not None
    assert set(retry.status_forcelist) >= {500, 502, 503, 504}
    assert 429 in retry.status_forcelist
    # Let callers see the final status code rather than raising on it.
    assert retry.raise_on_status is False
