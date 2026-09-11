"""Tests for add_ids.py."""

import hashlib
import json
import sys
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from add_ids import calculate_jsondata_ids


# Helpers

def make_group(
    category: str = "Test Category",
    words: List[str] | None = None,
    color: str = "red",
    description: str = "A description",
) -> Dict[str, Any]:
    return {
        "category": category,
        "words": words or ["alpha", "beta", "gamma", "delta"],
        "color": color,
        "description": description,
        "skill_level": "Beginner",
    }


def make_group_set(offset: int = 0) -> List[Dict[str, Any]]:
    colors = ["red", "blue", "green", "yellow"]
    return [make_group(category=f"Cat{offset + i}", color=colors[i]) for i in range(4)]


def make_data(n_game_sets: int = 1, n_group_sets: int = 1) -> Dict[str, Any]:
    return {
        "game_sets": [
            {
                "theme": f"Theme {t}",
                "group_sets": [make_group_set(offset=t * 10 + g * 4) for g in range(n_group_sets)],
            }
            for t in range(n_game_sets)
        ]
    }


# ID presence and format

class TestIdPresence:
    def test_game_set_id_added(self):
        data = make_data()
        result = calculate_jsondata_ids(data)
        assert "game_set_id" in result["game_sets"][0]

    def test_group_set_id_added_to_each_group(self):
        data = make_data()
        result = calculate_jsondata_ids(data)
        for group in result["game_sets"][0]["group_sets"][0]:
            assert "group_set_id" in group

    def test_group_item_id_added_to_each_group(self):
        data = make_data()
        result = calculate_jsondata_ids(data)
        for group in result["game_sets"][0]["group_sets"][0]:
            assert "group_item_id" in group

    def test_id_registry_added(self):
        data = make_data()
        result = calculate_jsondata_ids(data)
        assert "id_registry" in result

    def test_id_registry_keys(self):
        data = make_data()
        result = calculate_jsondata_ids(data)
        reg = result["id_registry"]
        assert set(reg.keys()) == {"group_set_ids", "game_set_ids", "group_item_ids"}


# ID format

class TestIdFormat:
    def test_game_set_id_is_12_hex_chars_by_default(self):
        data = make_data()
        result = calculate_jsondata_ids(data, hex_length=12)
        gid = result["game_sets"][0]["game_set_id"]
        assert isinstance(gid, str)
        assert len(gid) == 12
        assert all(c in "0123456789abcdef" for c in gid)

    def test_group_item_id_format(self):
        data = make_data()
        result = calculate_jsondata_ids(data, hex_length=12)
        iid = result["game_sets"][0]["group_sets"][0][0]["group_item_id"]
        assert len(iid) == 12
        assert all(c in "0123456789abcdef" for c in iid)

    def test_custom_hex_length_6(self):
        data = make_data()
        result = calculate_jsondata_ids(data, hex_length=6)
        gid = result["game_sets"][0]["game_set_id"]
        assert len(gid) == 6

    def test_custom_hex_length_24(self):
        data = make_data()
        result = calculate_jsondata_ids(data, hex_length=24)
        gid = result["game_sets"][0]["game_set_id"]
        assert len(gid) == 24


# Determinism

class TestDeterminism:
    def test_same_input_same_ids(self):
        r1 = calculate_jsondata_ids(make_data())
        r2 = calculate_jsondata_ids(make_data())
        assert r1["game_sets"][0]["game_set_id"] == r2["game_sets"][0]["game_set_id"]
        g1 = r1["game_sets"][0]["group_sets"][0][0]
        g2 = r2["game_sets"][0]["group_sets"][0][0]
        assert g1["group_item_id"] == g2["group_item_id"]
        assert g1["group_set_id"] == g2["group_set_id"]

    def test_different_theme_different_game_set_id(self):
        d1 = make_data()
        d2 = make_data()
        d2["game_sets"][0]["theme"] = "Completely Different"
        r1 = calculate_jsondata_ids(d1)
        r2 = calculate_jsondata_ids(d2)
        assert r1["game_sets"][0]["game_set_id"] != r2["game_sets"][0]["game_set_id"]

    def test_different_words_different_group_item_id(self):
        d1 = make_data()
        d2 = make_data()
        d2["game_sets"][0]["group_sets"][0][0]["words"] = ["w1", "w2", "w3", "w4"]
        r1 = calculate_jsondata_ids(d1)
        r2 = calculate_jsondata_ids(d2)
        assert (
            r1["game_sets"][0]["group_sets"][0][0]["group_item_id"]
            != r2["game_sets"][0]["group_sets"][0][0]["group_item_id"]
        )

    def test_words_order_does_not_affect_group_item_id(self):
        """group_item_id is based on sorted(words) so order does not matter."""
        d1 = make_data()
        d2 = make_data()
        d1["game_sets"][0]["group_sets"][0][0]["words"] = ["a", "b", "c", "d"]
        d2["game_sets"][0]["group_sets"][0][0]["words"] = ["d", "c", "b", "a"]
        r1 = calculate_jsondata_ids(d1)
        r2 = calculate_jsondata_ids(d2)
        assert (
            r1["game_sets"][0]["group_sets"][0][0]["group_item_id"]
            == r2["game_sets"][0]["group_sets"][0][0]["group_item_id"]
        )


# Deduplication in id_registry

class TestRegistryDeduplication:
    def test_identical_group_sets_registered_once(self):
        data = make_data(n_game_sets=1, n_group_sets=2)
        # Make both group_sets identical
        data["game_sets"][0]["group_sets"][1] = data["game_sets"][0]["group_sets"][0]
        result = calculate_jsondata_ids(data)
        ids = result["id_registry"]["group_set_ids"]
        assert len(ids) == len(set(ids)), "No duplicate IDs expected in registry"

    def test_identical_groups_across_sets_registered_once(self):
        data = make_data(n_game_sets=2)
        # Make both game_sets use identical group content
        data["game_sets"][1]["group_sets"] = data["game_sets"][0]["group_sets"]
        result = calculate_jsondata_ids(data)
        ids = result["id_registry"]["group_item_ids"]
        assert len(ids) == len(set(ids))


# All groups in a group_set share the same group_set_id

class TestGroupSetIdConsistency:
    def test_all_groups_in_set_share_group_set_id(self):
        data = make_data()
        result = calculate_jsondata_ids(data)
        group_set = result["game_sets"][0]["group_sets"][0]
        ids = [g["group_set_id"] for g in group_set]
        assert len(set(ids)) == 1, "All groups in a group_set must share the same group_set_id"

    def test_different_group_sets_have_different_ids(self):
        data = make_data(n_group_sets=2)
        result = calculate_jsondata_ids(data)
        id0 = result["game_sets"][0]["group_sets"][0][0]["group_set_id"]
        id1 = result["game_sets"][0]["group_sets"][1][0]["group_set_id"]
        assert id0 != id1


# Multiple game sets

class TestMultipleGameSets:
    def test_multiple_game_sets_each_get_id(self):
        data = make_data(n_game_sets=3)
        result = calculate_jsondata_ids(data)
        for gs in result["game_sets"]:
            assert "game_set_id" in gs

    def test_multiple_game_sets_all_ids_in_registry(self):
        data = make_data(n_game_sets=3)
        result = calculate_jsondata_ids(data)
        game_set_ids = [gs["game_set_id"] for gs in result["game_sets"]]
        registry_ids = result["id_registry"]["game_set_ids"]
        for gid in game_set_ids:
            assert gid in registry_ids


# Hash verification (spot-check the MD5 logic)

class TestHashVerification:
    def test_group_item_id_matches_expected_md5(self):
        group = make_group(category="Animals", words=["cat", "dog", "fish", "bird"], color="blue", description="Zoo")
        data = {"game_sets": [{"theme": "T", "group_sets": [[group]]}]}
        result = calculate_jsondata_ids(data, hex_length=12)
        crucial = ["Animals", ",".join(sorted(["cat", "dog", "fish", "bird"])), "blue", "Zoo"]
        content = "|".join(crucial)
        expected = hashlib.md5(content.encode()).hexdigest()[:12]
        assert result["game_sets"][0]["group_sets"][0][0]["group_item_id"] == expected
