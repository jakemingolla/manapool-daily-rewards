"""URL paths the client speaks to on Mana Pool's back-end.

This module is the project's API contract: every server path the client hits
lives here so a back-end URL change is a single-file edit. Only path
components live here; the hosts they hang off come from
:class:`manapool.config.Settings` (``base_url`` for manapool.com,
``supabase_url`` for the Supabase PostgREST gateway).
"""

from __future__ import annotations

# SvelteKit form action ``POST {base_url}/auth?/signin``: signs the user in
# and stores the ``mp-auth-token`` session cookie.
SIGN_IN = "/auth"

# Default SvelteKit form action ``POST {base_url}/daily``: claims today's
# Daily Reward.
CLAIM_DAILY = "/daily"

# SvelteKit ``__data.json`` for the Daily Reward page; carries claim
# eligibility and the form data the claim action expects.
DAILY_DATA = "/daily/__data.json"

# Site-wide ``__data.json``; carries the ``user`` node when authenticated and
# is used as a session probe after sign-in.
SESSION_PROBE = "/__data.json"

# Supabase PostgREST read of the user's Extra Mana balance row.
EXTRA_MANA = "/rest/v1/extra_mana"
