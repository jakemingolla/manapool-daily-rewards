"""Exception types for talking to Mana Pool."""

from __future__ import annotations


class ManaPoolError(Exception):
    """Raised for unrecoverable problems talking to Mana Pool."""


class NotAuthenticated(ManaPoolError):
    """Raised when an endpoint redirects to /auth (session missing/expired)."""
