"""Orchestration: check status and claim the Daily Reward when eligible."""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from manapool.client import ManaPoolClient
from manapool.config import Credentials
from manapool.console import Console
from manapool.errors import ManaPoolError
from manapool.models import Status
from manapool.presentation import format_mana, render_status

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

    def run(self, credentials: Credentials, *, check_only: bool = False) -> ExitCode:
        try:
            self._client.login(credentials)
        except ManaPoolError as exc:
            self._console.err(f"ERROR: {exc}")
            return ExitCode.AUTH_FAILED

        try:
            status = self._client.get_status()
        except ManaPoolError as exc:
            self._console.err(f"ERROR: could not read status: {exc}")
            return ExitCode.FAILURE

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

    def _report_after(self, before_status: Status, amount: Any) -> None:
        try:
            after = self._client.get_status()
        except ManaPoolError:
            return
        self._print_status(after)
        if amount is None and isinstance(after.extra_mana_available, (int, float)):
            before = before_status.extra_mana_available
            if isinstance(before, (int, float)):
                gained = int(after.extra_mana_available) - int(before)
                if gained > 0:
                    self._console.out(f"Extra Mana increased by {gained:,}.")
