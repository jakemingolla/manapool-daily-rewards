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
from manapool.presentation import render_json
from manapool.service import DailyRewardService, ExitCode
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
        "--json",
        action="store_true",
        help="Print the results as a single JSON object instead of text.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print diagnostic details (endpoint status and data keys) to stderr.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> ExitCode:
    args = build_parser().parse_args(argv)

    console = StreamConsole(debug=args.debug)

    credentials = load_credentials()
    if credentials is None:
        message = f"set {USERNAME_ENV} and {PASSWORD_ENV} (e.g. in a .env file)."
        if args.json:
            console.out(render_json({"error": message}))
        else:
            console.err(f"ERROR: {message}")
        return ExitCode.AUTH_FAILED

    settings = Settings()
    transport = RequestsTransport(settings)
    client = ManaPoolClient(transport, settings, console)
    service = DailyRewardService(client, console)

    return service.run(
        credentials,
        check_only=args.check_only,
        json_output=args.json,
    )


if __name__ == "__main__":
    raise SystemExit(main())
