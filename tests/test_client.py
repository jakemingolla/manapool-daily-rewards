"""Tests for the ManaPoolClient HTTP surface."""

from __future__ import annotations

import base64
import json

import pytest

from manapool.client import ManaPoolClient
from manapool.config import Settings
from manapool.errors import ManaPoolError, NotAuthenticated

from conftest import FakeCookie, FakeResponse, FakeTransport

SETTINGS = Settings()


def _node_data_payload(*nodes):
    return {"type": "data", "nodes": list(nodes)}


def test_fetch_node_data_redirect_raises_not_authenticated():
    transport = FakeTransport()
    transport.register(
        "GET", "/daily/__data.json", FakeResponse(status_code=302)
    )
    client = ManaPoolClient(transport, SETTINGS)
    with pytest.raises(NotAuthenticated):
        client.fetch_node_data("/daily/__data.json")


def test_fetch_node_data_non_json_raises():
    transport = FakeTransport()
    transport.register("GET", "/daily/__data.json", FakeResponse(status_code=200))
    client = ManaPoolClient(transport, SETTINGS)
    with pytest.raises(ManaPoolError, match="non-JSON"):
        client.fetch_node_data("/daily/__data.json")


def test_fetch_node_data_merges_nodes_and_skips_others():
    transport = FakeTransport()
    payload = _node_data_payload(
        None,
        {"type": "skip"},
        {"type": "data", "data": [{"a": 1}, "x"]},
        {"type": "data", "data": [{"b": 1}, "y"]},
    )
    transport.register("GET", "/daily/__data.json", FakeResponse(json_data=payload))
    client = ManaPoolClient(transport, SETTINGS)
    assert client.fetch_node_data("/daily/__data.json") == {"a": "x", "b": "y"}


def _auth_cookie(access_token: str) -> FakeCookie:
    raw = json.dumps({"access_token": access_token}).encode()
    encoded = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
    return FakeCookie(SETTINGS.auth_cookie_name, "base64-" + encoded)


def test_get_status_maps_fields():
    transport = FakeTransport(cookies=[_auth_cookie("tok")])
    daily = _node_data_payload(
        {
            "type": "data",
            "data": [
                {
                    "alreadyClaimed": 1,
                    "hasRecentOrder": 2,
                    "secondsUntilMidnightTonight": 3,
                },
                False,
                True,
                3600,
            ],
        }
    )
    transport.register("GET", "/daily/__data.json", FakeResponse(json_data=daily))
    transport.register(
        "GET",
        "/rest/v1/extra_mana",
        FakeResponse(json_data=[{"points": 16, "pending_points": 1396}]),
    )

    client = ManaPoolClient(transport, SETTINGS)
    status = client.get_status()

    assert status.already_claimed is False
    assert status.eligible is True
    assert status.seconds_until_reset == 3600
    assert status.extra_mana_available == 16
    assert status.pending_extra_mana == 1396
    assert status.claim_form_data is None


def test_fetch_extra_mana_without_token_returns_empty():
    transport = FakeTransport()
    client = ManaPoolClient(transport, SETTINGS)
    assert client.fetch_extra_mana() == {}


def test_claim_parses_award_and_serializes_form():
    transport = FakeTransport()
    data = json.dumps([{"awardAmount": 1, "awardTitle": 2}, 10, "Daily"])
    transport.register(
        "POST", "/daily", FakeResponse(json_data={"type": "success", "data": data})
    )
    client = ManaPoolClient(transport, SETTINGS)

    result = client.claim({"flag": True, "skip": None, "count": 5, "off": False})

    assert result.award_amount == 10
    assert result.award_title == "Daily"
    sent_kwargs = transport.calls[0][2]
    assert sent_kwargs["data"] == {"flag": "true", "count": "5", "off": "false"}
    assert (
        sent_kwargs["headers"]["Content-Type"]
        == "application/x-www-form-urlencoded"
    )


def test_claim_http_error_raises():
    transport = FakeTransport()
    transport.register("POST", "/daily", FakeResponse(status_code=500))
    client = ManaPoolClient(transport, SETTINGS)
    with pytest.raises(ManaPoolError, match="Claim failed"):
        client.claim({})
