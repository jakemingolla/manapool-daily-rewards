"""Authentication: SvelteKit sign-in and Supabase session reconstruction."""

from __future__ import annotations

from manapool.auth.login import extract_action_message, is_authenticated, login
from manapool.auth.supabase import supabase_session_from_cookies

__all__ = [
    "extract_action_message",
    "is_authenticated",
    "login",
    "supabase_session_from_cookies",
]
