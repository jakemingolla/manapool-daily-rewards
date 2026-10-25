"""Tests for the check/claim orchestration."""

from __future__ import annotations

import json

from conftest import FakeClient, RecordingConsole

from manapool.config import Credentials
from manapool.errors import ManaPoolError
from manapool.models import ClaimResult, Status
from manapool.service import DailyRewardService

CREDS = Credentials(email="me@example.com", password="secret")


def _status(**overrides) -> Status:
    base = dict(
        already_claimed=False,
        eligible=True,
        seconds_until_reset=3600,
        extra_mana_available=16,
        pending_extra_mana=1396,
        claim_form_data={"id": "1"},
    )
    base.update(overrides)
    return Status(**base)


def _json_payload(console: RecordingConsole) -> dict:
    assert len(console.out_lines) == 1
    return json.loads(console.out_lines[0])


def test_login_failure_returns_2():
    client = FakeClient(login_error=ManaPoolError("nope"))
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS)
    assert code == 2
    assert any("nope" in line for line in console.err_lines)


def test_status_read_failure_returns_1():
    client = FakeClient(status_error=ManaPoolError("boom"))
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS)
    assert code == 1
    assert any("could not read status" in line for line in console.err_lines)


def test_check_only_returns_0_without_claim():
    client = FakeClient(statuses=[_status()])
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS, check_only=True)
    assert code == 0
    assert client.claim_calls == []


def test_already_claimed_returns_0():
    client = FakeClient(statuses=[_status(already_claimed=True)])
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS)
    assert code == 0
    assert client.claim_calls == []
    assert any("already claimed" in line for line in console.out_lines)


def test_not_eligible_returns_3():
    client = FakeClient(statuses=[_status(eligible=False)])
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS)
    assert code == 3
    assert client.claim_calls == []
    assert any("Not eligible" in line for line in console.err_lines)


def test_eligible_claims_and_reports_award():
    before = _status(extra_mana_available=16)
    after = _status(already_claimed=True, extra_mana_available=26)
    client = FakeClient(
        statuses=[before, after],
        claim_result=ClaimResult(award_amount=10, award_title="Daily"),
    )
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS)

    assert code == 0
    assert client.claim_calls == [{"id": "1"}]
    assert any(
        "Claimed! Awarded 10 Extra Mana (Daily)." in line for line in console.out_lines
    )


def test_json_check_only_emits_single_object():
    client = FakeClient(statuses=[_status()])
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(
        CREDS, check_only=True, json_output=True
    )

    assert code == 0
    assert client.claim_calls == []
    payload = _json_payload(console)
    assert payload["claimed"] is False
    assert payload["claim"] is None
    assert payload["status_after"] is None
    assert payload["status"]["extra_mana_available"] == 16
    assert payload["status"]["pending_extra_mana"] == 1396
    assert console.err_lines == []


def test_json_already_claimed_emits_object_without_claim():
    client = FakeClient(statuses=[_status(already_claimed=True)])
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS, json_output=True)

    assert code == 0
    assert client.claim_calls == []
    payload = _json_payload(console)
    assert payload["claimed"] is False
    assert payload["status"]["already_claimed"] is True
    assert "error" not in payload


def test_json_status_read_failure_returns_1():
    client = FakeClient(status_error=ManaPoolError("boom"))
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS, json_output=True)

    assert code == 1
    assert _json_payload(console) == {"error": "could not read status: boom"}


def test_json_claims_and_reports_award():
    before = _status(extra_mana_available=16)
    after = _status(already_claimed=True, extra_mana_available=26)
    client = FakeClient(
        statuses=[before, after],
        claim_result=ClaimResult(award_amount=10, award_title="Daily"),
    )
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS, json_output=True)

    assert code == 0
    assert client.claim_calls == [{"id": "1"}]
    payload = _json_payload(console)
    assert payload["claimed"] is True
    assert payload["claim"] == {"award_amount": 10, "award_title": "Daily"}
    assert payload["status_after"]["already_claimed"] is True
    assert payload["status_after"]["extra_mana_available"] == 26


def test_json_claim_succeeds_when_refetch_fails():
    class RefetchFails(FakeClient):
        def get_status(self) -> Status:
            if self.status_calls == 1:
                raise ManaPoolError("refetch failed")
            return super().get_status()

    client = RefetchFails(
        statuses=[_status()],
        claim_result=ClaimResult(award_amount=10, award_title="Daily"),
    )
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS, json_output=True)

    assert code == 0
    payload = _json_payload(console)
    assert payload["claimed"] is True
    assert payload["claim"] == {"award_amount": 10, "award_title": "Daily"}
    assert payload["status_after"] is None


def test_json_not_eligible_returns_3_with_error():
    client = FakeClient(statuses=[_status(eligible=False)])
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS, json_output=True)

    assert code == 3
    payload = _json_payload(console)
    assert payload["claimed"] is False
    assert "Not eligible to claim" in payload["error"]


def test_json_login_failure_returns_2():
    client = FakeClient(login_error=ManaPoolError("nope"))
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS, json_output=True)

    assert code == 2
    assert _json_payload(console) == {"error": "nope"}
    assert console.err_lines == []


def test_json_claim_failure_returns_1():
    client = FakeClient(
        statuses=[_status()],
        claim_error=ManaPoolError("claim blew up"),
    )
    console = RecordingConsole()
    code = DailyRewardService(client, console).run(CREDS, json_output=True)

    assert code == 1
    payload = _json_payload(console)
    assert payload["error"] == "claim blew up"
    assert payload["claimed"] is False
