"""Tests for the check/claim orchestration."""

from __future__ import annotations

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
