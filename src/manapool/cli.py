"""Command-line entry point."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from manapool.client import ManaPoolClient
from manapool.config import (
    PASSWORD_ENV,
    USERNAME_ENV,
    Settings,
    load_credentials,
)
from manapool.console import StreamConsole
from manapool.service import DailyRewardService
from manapool.transport import RequestsTransport


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manapool",
        description="Check and claim the Mana Pool Daily Reward (Extra Mana).",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only report status; never claim the reward.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print diagnostic details (endpoint status and data keys) to stderr.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    console = StreamConsole(debug=args.debug)

    credentials = load_credentials()
    if credentials is None:
        console.err(
            f"ERROR: set {USERNAME_ENV} and {PASSWORD_ENV} (e.g. in a .env file)."
        )
        return 2

    settings = Settings()
    transport = RequestsTransport(settings)
    client = ManaPoolClient(transport, settings, console)
    service = DailyRewardService(client, console)

    return service.run(credentials, check_only=args.check_only)


if __name__ == "__main__":
    raise SystemExit(main())
