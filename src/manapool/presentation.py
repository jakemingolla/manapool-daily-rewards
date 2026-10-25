"""Pure formatting helpers that turn a Status into display strings or JSON."""

from __future__ import annotations

import json
from typing import Any

from manapool.models import ClaimResult, Status


def format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_mana(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{int(value):,}"
    return "unknown"


def render_status(status: Status) -> list[str]:
    """Render a status snapshot as the lines to print to the user."""
    lines = [
        "Mana Pool - Daily Reward status",
        f"  Extra Mana available:   {format_mana(status.extra_mana_available)}",
    ]
    if status.pending_extra_mana is not None:
        lines.append(
            f"  Available next month:   {format_mana(status.pending_extra_mana)}"
        )
    lines.append(f"  Eligible (recent order): {'yes' if status.eligible else 'no'}")
    lines.append(
        f"  Claimed today (UTC):     {'yes' if status.already_claimed else 'no'}"
    )
    lines.append(
        f"  Time until reset (UTC):  {format_duration(status.seconds_until_reset)}"
    )
    return lines


def status_to_dict(status: Status) -> dict[str, Any]:
    """Convert a status snapshot to a JSON-serializable mapping."""
    data: dict[str, Any] = {
        "extra_mana_available": status.extra_mana_available,
        "eligible": status.eligible,
        "already_claimed": status.already_claimed,
        "seconds_until_reset": status.seconds_until_reset,
    }
    if status.pending_extra_mana is not None:
        data["pending_extra_mana"] = status.pending_extra_mana
    return data


def claim_to_dict(result: ClaimResult) -> dict[str, Any]:
    """Convert a claim outcome to a JSON-serializable mapping."""
    return {
        "award_amount": result.award_amount,
        "award_title": result.award_title,
    }


def render_json(payload: Any) -> str:
    """Serialize a payload as pretty-printed JSON."""
    return json.dumps(payload, indent=2)
