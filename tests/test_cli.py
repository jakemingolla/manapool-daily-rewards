"""Tests for argument parsing and the credential gate."""

from __future__ import annotations

from manapool import cli


def test_parser_flags():
    args = cli.build_parser().parse_args(["--check-only", "--debug"])
    assert args.check_only is True
    assert args.debug is True


def test_parser_defaults():
    args = cli.build_parser().parse_args([])
    assert args.check_only is False
    assert args.debug is False


def test_main_missing_credentials_returns_2(monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_credentials", lambda: None)
    code = cli.main([])
    assert code == 2
    captured = capsys.readouterr()
    assert "MANAPOOL_ACCOUNT_USERNAME" in captured.err
