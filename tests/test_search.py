"""Tests for the nested-structure search helper."""

from __future__ import annotations

from manapool.parsing.search import find_key


def test_find_key_in_nested_dict():
    assert find_key({"a": {"b": {"c": 5}}}, "c") == 5


def test_find_key_in_list_of_dicts():
    assert find_key([{"x": 1}, {"y": 2}], "y") == 2


def test_find_key_returns_first_match():
    assert find_key({"a": {"target": 1}}, "target") == 1


def test_find_key_missing_returns_none():
    assert find_key({"a": 1, "b": [2, 3]}, "z") is None
