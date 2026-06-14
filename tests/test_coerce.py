"""Tests for the typed-domain coercion helpers."""

from __future__ import annotations

from manapool.coerce import as_dict, as_int, as_str


def test_as_int_passes_through_ints():
    assert as_int(0) == 0
    assert as_int(16) == 16
    assert as_int(-3) == -3


def test_as_int_truncates_floats():
    assert as_int(1.0) == 1
    assert as_int(1.9) == 1
    assert as_int(-1.5) == -1


def test_as_int_rejects_bools():
    assert as_int(True) is None
    assert as_int(False) is None


def test_as_int_rejects_other_types():
    assert as_int(None) is None
    assert as_int("5") is None
    assert as_int([1]) is None
    assert as_int({"a": 1}) is None


def test_as_str():
    assert as_str("hello") == "hello"
    assert as_str("") == ""
    assert as_str(None) is None
    assert as_str(5) is None
    assert as_str(["a"]) is None


def test_as_dict():
    assert as_dict({"a": 1}) == {"a": 1}
    assert as_dict({}) == {}
    assert as_dict(None) is None
    assert as_dict([("a", 1)]) is None
    assert as_dict("a=1") is None
