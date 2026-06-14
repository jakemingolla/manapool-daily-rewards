"""Domain models returned by the client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Status:
    """Daily Reward eligibility and Extra Mana balance snapshot."""

    already_claimed: bool
    eligible: bool
    seconds_until_reset: int
    extra_mana_available: int | None = None
    pending_extra_mana: int | None = None
    claim_form_data: dict[str, Any] | None = None


@dataclass(frozen=True)
class ClaimResult:
    """Outcome of submitting a Daily Reward claim."""

    award_amount: int | None = None
    award_title: str | None = None
