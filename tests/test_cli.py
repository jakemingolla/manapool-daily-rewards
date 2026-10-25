"""Tests for argument parsing and the credential gate."""

from __future__ import annotations

import json

from manapool import cli


def test_parser_flags():
    args = cli.build_parser().parse_args(["--check-only", "--json", "--debug"])
    assert args.check_only is True
    assert args.json is True
    assert args.debug is True


def test_parser_defaults():
    args = cli.build_parser().parse_args([])
    assert args.check_only is False
    assert args.json is False
    assert args.debug is False


def test_main_missing_credentials_returns_2(monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_credentials", lambda: None)
    code = cli.main([])
    assert code == 2
    captured = capsys.readouterr()
    assert "MANAPOOL_ACCOUNT_USERNAME" in captured.err


def test_main_missing_credentials_json(monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_credentials", lambda: None)
    code = cli.main(["--json"])
    assert code == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)["error"].startswith("set MANAPOOL_ACCOUNT_USERNAME")
    assert captured.err == ""


def _stub_service(monkeypatch, seen: dict) -> None:
    class FakeService:
        def __init__(self, client, console) -> None:
            pass

        def run(self, credentials, **kwargs) -> int:
            seen.update(kwargs)
            return 0

    monkeypatch.setattr(cli, "load_credentials", lambda: "creds")
    monkeypatch.setattr(cli, "Settings", lambda: None)
    monkeypatch.setattr(cli, "RequestsTransport", lambda settings: None)
    monkeypatch.setattr(
        cli, "ManaPoolClient", lambda transport, settings, console: None
    )
    monkeypatch.setattr(cli, "DailyRewardService", FakeService)


def test_main_forwards_json_flag(monkeypatch):
    seen: dict = {}
    _stub_service(monkeypatch, seen)
    assert cli.main(["--json"]) == 0
    assert seen == {"check_only": False, "json_output": True}


def test_main_forwards_default_output_mode(monkeypatch):
    seen: dict = {}
    _stub_service(monkeypatch, seen)
    assert cli.main([]) == 0
    assert seen == {"check_only": False, "json_output": False}
