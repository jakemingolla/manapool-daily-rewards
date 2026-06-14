"""Runtime configuration: endpoint settings and credential loading."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

USERNAME_ENV = "MANAPOOL_ACCOUNT_USERNAME"
PASSWORD_ENV = "MANAPOOL_ACCOUNT_PASSWORD"


@dataclass(frozen=True)
class Settings:
    """Endpoints and constants for the Mana Pool / Supabase HTTP API."""

    base_url: str = "https://manapool.com"
    # Supabase backend (publishable anon key is public; embedded in the site HTML).
    supabase_url: str = "https://sb-api.manapool.com"
    supabase_anon_key: str = "sb_publishable_mwzveHhY-M-t19HCwYC1lw_pRUJyYZP"
    auth_cookie_name: str = "mp-auth-token"
    user_agent: str = DEFAULT_USER_AGENT
    timeout: int = 30


@dataclass(frozen=True)
class Credentials:
    """Mana Pool account login credentials."""

    email: str
    password: str


def load_credentials(env: Mapping[str, str] | None = None) -> Credentials | None:
    """Load credentials from the environment (and ``.env`` when ``env`` is None).

    Pass an explicit ``env`` mapping in tests to avoid touching the real
    environment or ``.env`` file. Returns ``None`` when either value is missing.
    """
    if env is None:
        try:
            load_dotenv()
        except OSError:
            # .env may be unreadable (e.g. restricted permissions); fall back to
            # variables already present in the environment.
            pass
        env = os.environ

    email = env.get(USERNAME_ENV)
    password = env.get(PASSWORD_ENV)
    if not email or not password:
        return None
    return Credentials(email=email, password=password)
