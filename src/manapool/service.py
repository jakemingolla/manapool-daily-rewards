"""Orchestration: check status and claim the Daily Reward when eligible."""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from manapool.client import ManaPoolClient
from manapool.config import Credentials
from manapool.console import Console
from manapool.errors import ManaPoolError
from manapool.models import Status
from manapool.presentation import (
    claim_to_dict,
    format_mana,
    render_json,
    render_status,
    status_to_dict,
)

DAILY_RULES_URL = "https://manapool.com/daily/rules"


class ExitCode(IntEnum):
    """Process exit codes for the ``manapool`` CLI.

    Values are part of the public CLI contract and are documented in the
    README; do not renumber existing members.
    """

    SUCCESS = 0
    FAILURE = 1
    AUTH_FAILED = 2
    NOT_ELIGIBLE = 3


class DailyRewardService:
    """Drives the check/claim flow using an injected client and console."""

    def __init__(self, client: ManaPoolClient, console: Console) -> None:
        self._client = client
        self._console = console

    def run(
        self,
        credentials: Credentials,
        *,
        check_only: bool = False,
        json_output: bool = False,
    ) -> ExitCode:
        try:
            self._client.login(credentials)
        except ManaPoolError as exc:
            return self._fail(json_output, f"ERROR: {exc}", ExitCode.AUTH_FAILED)

        try:
            status = self._client.get_status()
        except ManaPoolError as exc:
            return self._fail(
                json_output,
                f"ERROR: could not read status: {exc}",
                ExitCode.FAILURE,
            )

        if json_output:
            return self._run_json(status, check_only)

        self._print_status(status)

        if check_only:
            return ExitCode.SUCCESS

        if status.already_claimed:
            self._console.out("\nNothing to do: today's reward was already claimed.")
            return ExitCode.SUCCESS

        if not status.eligible:
            self._console.err(
                "\nNot eligible to claim: no purchase in the last 30 days "
                "(or no alternate-entry allowance). See " + DAILY_RULES_URL
            )
            return ExitCode.NOT_ELIGIBLE

        self._console.out("\nClaiming today's Daily Reward...")
        try:
            result = self._client.claim(status.claim_form_data)
        except ManaPoolError as exc:
            self._console.err(f"ERROR: {exc}")
            return ExitCode.FAILURE

        amount = result.award_amount
        title = result.award_title
        if amount is not None:
            suffix = f" ({title})" if title else ""
            self._console.out(
                f"Claimed! Awarded {format_mana(amount)} Extra Mana{suffix}."
            )
        else:
            self._console.out("Claim submitted.")

        self._report_after(status, amount)
        return ExitCode.SUCCESS

    def _print_status(self, status: Status) -> None:
        for line in render_status(status):
            self._console.out(line)

    def _fail(self, json_output: bool, message: str, code: ExitCode) -> ExitCode:
        if json_output:
            self._emit_json({"error": message.removeprefix("ERROR: ")})
        else:
            self._console.err(message)
        return code

    def _emit_json(self, payload: Any) -> None:
        self._console.out(render_json(payload))

    def _run_json(self, status: Status, check_only: bool) -> ExitCode:
        payload: dict[str, Any] = {
            "status": status_to_dict(status),
            "claimed": False,
            "claim": None,
            "status_after": None,
        }

        if check_only or status.already_claimed:
            self._emit_json(payload)
            return ExitCode.SUCCESS

        if not status.eligible:
            payload["error"] = (
                "Not eligible to claim: no purchase in the last 30 days "
                "(or no alternate-entry allowance). See " + DAILY_RULES_URL
            )
            self._emit_json(payload)
            return ExitCode.NOT_ELIGIBLE

        try:
            result = self._client.claim(status.claim_form_data)
        except ManaPoolError as exc:
            payload["error"] = str(exc)
            self._emit_json(payload)
            return ExitCode.FAILURE

        payload["claimed"] = True
        payload["claim"] = claim_to_dict(result)
        try:
            payload["status_after"] = status_to_dict(self._client.get_status())
        except ManaPoolError:
            pass
        self._emit_json(payload)
        return ExitCode.SUCCESS

    def _report_after(self, before_status: Status, amount: int | None) -> None:
        try:
            after = self._client.get_status()
        except ManaPoolError:
            return
        self._print_status(after)
        if amount is None and after.extra_mana_available is not None:
            before = before_status.extra_mana_available
            if before is not None:
                gained = after.extra_mana_available - before
                if gained > 0:
                    self._console.out(f"Extra Mana increased by {gained:,}.")
