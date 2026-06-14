"""Mana Pool Daily Reward (Extra Mana) automation.

Browserless: talks to Mana Pool's SvelteKit + Supabase HTTP endpoints directly.

Flow:
  1. Log in via the SvelteKit form action ``POST /auth?/signin`` (sets the
     ``mp-auth-token`` session cookie in the transport cookie jar).
  2. Read status from ``/daily/__data.json`` and the Extra Mana balance from
     Supabase (PostgREST).
  3. If eligible and not yet claimed today, claim via the default form action
     ``POST /daily`` and report the awarded amount / new balance.

The Daily Reward resets at 00:00 UTC and can be claimed once per UTC day.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
