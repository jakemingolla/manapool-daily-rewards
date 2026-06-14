"""Tests for SvelteKit devalue decoding."""

from __future__ import annotations

import math

from manapool.parsing.devalue import unflatten


def test_bare_number_is_returned_as_is():
    assert unflatten(42) == 42


def test_nested_object_and_array():
    payload = [{"name": 1, "items": 2}, "Ada", [3, 4], "x", "y"]
    assert unflatten(payload) == {"name": "Ada", "items": ["x", "y"]}


def test_sentinels_referenced_by_object_fields():
    payload = [{"n": -3, "p": -4, "neg": -5, "z": -6, "u": -1}]
    result = unflatten(payload)
    assert math.isnan(result["n"])
    assert result["p"] == math.inf
    assert result["neg"] == -math.inf
    assert result["z"] == 0.0 and math.copysign(1, result["z"]) == -1
    assert result["u"] is None


def test_holes_and_undefined_in_array():
    payload = [[1, -1, -2], "z"]
    assert unflatten(payload) == ["z", None, None]


def test_date_and_bigint_tags():
    assert unflatten([{"d": 1}, ["Date", "2020-01-01"]]) == {"d": "2020-01-01"}
    assert unflatten([{"b": 1}, ["BigInt", "123"]]) == {"b": 123}


def test_set_tag():
    payload = [{"s": 1}, ["Set", 2, 3], "a", "b"]
    assert unflatten(payload) == {"s": ["a", "b"]}


def test_map_tag():
    payload = [{"m": 1}, ["Map", 2, 3, 4, 5], "k1", "v1", "k2", "v2"]
    assert unflatten(payload) == {"m": {"k1": "v1", "k2": "v2"}}
