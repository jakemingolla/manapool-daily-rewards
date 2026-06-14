"""Tests for reconstructing the Supabase session from cookies."""

from __future__ import annotations

import base64
import json
import urllib.parse

from conftest import FakeCookie

from manapool.auth.supabase import supabase_session_from_cookies

COOKIE = "mp-auth-token"


def _base64_cookie(payload: dict) -> str:
    raw = json.dumps(payload).encode()
    encoded = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
    return "base64-" + encoded


def test_single_base64_cookie():
    value = _base64_cookie({"access_token": "tok"})
    cookies = [FakeCookie(COOKIE, value)]
    assert supabase_session_from_cookies(cookies, COOKIE) == {"access_token": "tok"}


def test_chunked_base64_cookie():
    value = _base64_cookie({"access_token": "abcdef"})
    midpoint = len(value) // 2
    cookies = [
        FakeCookie(f"{COOKIE}.0", value[:midpoint]),
        FakeCookie(f"{COOKIE}.1", value[midpoint:]),
    ]
    assert supabase_session_from_cookies(cookies, COOKIE) == {"access_token": "abcdef"}


def test_plain_json_cookie():
    cookies = [FakeCookie(COOKIE, json.dumps({"access_token": "plain"}))]
    assert supabase_session_from_cookies(cookies, COOKIE) == {"access_token": "plain"}


def test_url_encoded_json_cookie():
    raw = urllib.parse.quote(json.dumps({"access_token": "enc"}))
    cookies = [FakeCookie(COOKIE, raw)]
    assert supabase_session_from_cookies(cookies, COOKIE) == {"access_token": "enc"}


def test_missing_cookie_returns_none():
    cookies = [FakeCookie("other", "x")]
    assert supabase_session_from_cookies(cookies, COOKIE) is None
