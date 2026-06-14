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
    extra_mana_available: Any = None
    pending_extra_mana: Any = None
    claim_form_data: Any = None


@dataclass(frozen=True)
class ClaimResult:
    """Outcome of submitting a Daily Reward claim."""

    award_amount: Any = None
    award_title: Any = None
