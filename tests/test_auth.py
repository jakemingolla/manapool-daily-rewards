"""Tests for the SvelteKit sign-in flow."""

from __future__ import annotations

import json

import pytest
from conftest import FakeResponse, FakeTransport

from manapool.auth.login import login
from manapool.config import Credentials, Settings
from manapool.errors import ManaPoolError

CREDS = Credentials(email="me@example.com", password="secret")
SETTINGS = Settings()


def _make_fetch(transport: FakeTransport):
    from manapool.client import ManaPoolClient

    return ManaPoolClient(transport, SETTINGS).fetch_node_data


def test_login_success():
    transport = FakeTransport()
    transport.register("POST", "/auth", FakeResponse(json_data={"type": "redirect"}))
    transport.register(
        "GET",
        "/__data.json",
        FakeResponse(
            json_data={
                "type": "data",
                "nodes": [{"type": "data", "data": [{"user": 1}, "ada"]}],
            }
        ),
    )

    login(transport, CREDS, SETTINGS, fetch=_make_fetch(transport))

    methods = [call[0] for call in transport.calls]
    assert methods[0] == "POST"


def test_login_rejected_extracts_message():
    transport = FakeTransport()
    data = json.dumps([{"message": 1}, "bad creds"])
    transport.register(
        "POST",
        "/auth",
        FakeResponse(json_data={"type": "failure", "data": data}),
    )

    with pytest.raises(ManaPoolError, match="bad creds"):
        login(transport, CREDS, SETTINGS, fetch=_make_fetch(transport))


def test_login_session_not_established():
    transport = FakeTransport()
    transport.register("POST", "/auth", FakeResponse(json_data={"type": "redirect"}))
    transport.register(
        "GET",
        "/__data.json",
        FakeResponse(status_code=302, headers={"location": "/auth"}),
    )

    with pytest.raises(ManaPoolError, match="did not establish a session"):
        login(transport, CREDS, SETTINGS, fetch=_make_fetch(transport))
