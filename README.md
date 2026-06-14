# Mana Pool Daily Reward automation

Checks and (optionally) claims the [Mana Pool](https://manapool.com) **Daily
Reward / Extra Mana** for your account, without a browser. It talks to Mana
Pool's HTTP endpoints directly:

- logs in via the SvelteKit form action `POST /auth?/signin`,
- reads Daily Reward eligibility from `GET /daily/__data.json`,
- reads the Extra Mana balance from Supabase (PostgREST), and
- claims via the SvelteKit form action `POST /daily` when eligible.

No Selenium, Playwright, or headless browser is used.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
cp .env.example .env
# then edit .env with your Mana Pool email + password
```

`.env` (git-ignored) holds your credentials:

```dotenv
MANAPOOL_ACCOUNT_USERNAME=you@example.com
MANAPOOL_ACCOUNT_PASSWORD=your-password
```

Credentials are read only at runtime and are sent only to `manapool.com` /
`sb-api.manapool.com` for authentication.

## Usage

`uv sync` installs the package, exposing the `manapool` console script (you can
also run `uv run python -m manapool`).

Check status and auto-claim when eligible:

```bash
uv run manapool
```

Check status only (never claims):

```bash
uv run manapool --check-only
```

Print diagnostics (endpoint responses and data keys) to stderr:

```bash
uv run manapool --debug
```

Example output:

```text
Mana Pool - Daily Reward status
  Extra Mana available:   16
  Available next month:   1,396
  Eligible (recent order): yes
  Claimed today (UTC):     no
  Time until reset (UTC):  05:53:58

Claiming today's Daily Reward...
Claimed! Awarded 10 Extra Mana.
```

### Scheduled runs (GitHub Actions)

`.github/workflows/daily-reward.yml` runs `manapool` daily at 01:00 UTC
(9 PM EDT / 8 PM EST). To enable it on your fork, add two repository secrets:

- `MANAPOOL_ACCOUNT_USERNAME`
- `MANAPOOL_ACCOUNT_PASSWORD`

You can also trigger the workflow manually from the Actions tab.

### Exit codes

Defined as `ExitCode(IntEnum)` in `src/manapool/service.py`:

| Code | Name | Meaning |
| --- | --- | --- |
| 0 | `SUCCESS` | Status reported; reward claimed, already claimed, or check-only |
| 1 | `FAILURE` | Could not read status / claim failed |
| 2 | `AUTH_FAILED` | Missing credentials or sign-in failed |
| 3 | `NOT_ELIGIBLE` | Claim requested but the account is not eligible |

## Project layout

The code is split by domain under `src/manapool/`:

- `cli.py` - argument parsing and the `python -m manapool` entry point.
- `service.py` - the check/claim orchestration (`DailyRewardService`).
- `client.py` - `ManaPoolClient`, the HTTP API surface.
- `transport.py` - the `Transport` protocol and the `requests`-backed implementation.
- `auth/` - SvelteKit sign-in and Supabase session reconstruction.
- `parsing/` - SvelteKit `devalue` decoding and nested-structure search.
- `presentation.py` - pure status formatting.
- `config.py`, `console.py`, `models.py`, `errors.py` - settings/credentials, output, domain models, exceptions.

Network access and I/O are injected (`Transport`, `Console`), so the tests run
entirely against fakes with no credentials or network.

## Running tests

```bash
uv run --group dev pytest
```

## How eligibility works

- The reward can be claimed **once per UTC day** and resets at **00:00 UTC**.
- To be eligible you must have **made a purchase in the last 30 days**, or have
  an alternate-entry allowance. See the
  [official rules](https://manapool.com/daily/rules). If you are not eligible,
  the script reports it and exits with code 3 instead of claiming.
- The awarded amount is randomized server-side per Mana Pool's published odds.

## Notes

- This is an unofficial tool that mimics the website's own requests; Mana Pool
  may change its endpoints at any time.
- Run `--debug` if the output looks wrong; it prints the HTTP status and the
  data keys returned by each endpoint (no secret values).
