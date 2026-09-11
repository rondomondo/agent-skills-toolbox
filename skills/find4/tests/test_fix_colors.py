"""Tests for fix_colors.py."""

import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from fix_colors import COLOR_PALETTE, REQUIRED_COUNT, fix_color_groups


# Helpers

def make_group(color: str = "red", category: str = "Test") -> Dict[str, Any]:
    return {"category": category, "words": ["a", "b", "c", "d"], "color": color}


def make_group_set(colors: List[str] | None = None) -> List[Dict[str, Any]]:
    palette = colors or ["red", "blue", "green", "yellow"]
    return [make_group(color=c, category=f"Cat {i}") for i, c in enumerate(palette)]


def make_data(group_sets: List[List[Dict[str, Any]]] | None = None) -> Dict[str, Any]:
    return {
        "game_sets": [
            {"theme": "T", "group_sets": group_sets or [make_group_set()]}
        ]
    }


# Pass-through for already-valid data

class TestPassThrough:
    def test_valid_data_unchanged(self):
        data = make_data()
        result = fix_color_groups(data)
        colors = [g["color"] for g in result["game_sets"][0]["group_sets"][0]]
        assert colors == ["red", "blue", "green", "yellow"]

    def test_all_8_palette_colors_accepted(self):
        for i in range(0, len(COLOR_PALETTE), 4):
            four = COLOR_PALETTE[i:i + 4]
            data = make_data([make_group_set(four)])
            result = fix_color_groups(data)
            out = [g["color"] for g in result["game_sets"][0]["group_sets"][0]]
            assert set(out) == set(four)

    def test_valid_returns_same_structure(self):
        data = make_data()
        result = fix_color_groups(data)
        assert "game_sets" in result
        assert len(result["game_sets"]) == 1

    def test_does_not_mutate_original_when_valid(self):
        data = make_data()
        original_colors = [g["color"] for g in data["game_sets"][0]["group_sets"][0]]
        fix_color_groups(data)
        assert [g["color"] for g in data["game_sets"][0]["group_sets"][0]] == original_colors


# Color fixing

class TestColorFix:
    def test_duplicate_colors_replaced(self):
        gs = [make_group(color="red", category=f"Cat {i}") for i in range(4)]
        data = make_data([gs])
        result = fix_color_groups(data)
        out = [g["color"] for g in result["game_sets"][0]["group_sets"][0]]
        assert out == COLOR_PALETTE[:4]

    def test_invalid_color_replaced(self):
        gs = make_group_set(["red", "blue", "green", "pink"])
        data = make_data([gs])
        result = fix_color_groups(data)
        out = [g["color"] for g in result["game_sets"][0]["group_sets"][0]]
        assert all(c in COLOR_PALETTE for c in out)

    def test_missing_color_field_replaced(self):
        gs = [{"category": f"Cat {i}", "words": ["a", "b", "c", "d"]} for i in range(4)]
        data = make_data([gs])
        result = fix_color_groups(data)
        out = [g["color"] for g in result["game_sets"][0]["group_sets"][0]]
        assert out == COLOR_PALETTE[:4]

    def test_empty_color_string_replaced(self):
        gs = make_group_set(["red", "blue", "", "yellow"])
        data = make_data([gs])
        result = fix_color_groups(data)
        out = [g["color"] for g in result["game_sets"][0]["group_sets"][0]]
        assert out == COLOR_PALETTE[:4]

    def test_fixed_colors_are_first_four_palette_colors(self):
        gs = [make_group(color="pink", category=f"Cat {i}") for i in range(4)]
        data = make_data([gs])
        result = fix_color_groups(data)
        out = [g["color"] for g in result["game_sets"][0]["group_sets"][0]]
        assert out == ["red", "blue", "green", "yellow"]

    def test_uppercase_color_is_valid_because_comparison_is_lowercased(self):
        # The script lowercases colors before comparing against the palette,
        # so "Red" passes validation — it is NOT replaced.
        gs = make_group_set(["Red", "blue", "green", "yellow"])
        data = make_data([gs])
        result = fix_color_groups(data)
        out = [g["color"] for g in result["game_sets"][0]["group_sets"][0]]
        assert out == ["Red", "blue", "green", "yellow"]


# Multiple group_sets

class TestMultipleGroupSets:
    def test_only_invalid_group_set_fixed(self):
        valid_gs = make_group_set(["red", "blue", "green", "yellow"])
        bad_gs = [make_group(color="pink", category=f"Cat {i}") for i in range(4)]
        data = make_data([valid_gs, bad_gs])
        result = fix_color_groups(data)
        group_sets = result["game_sets"][0]["group_sets"]
        valid_out = [g["color"] for g in group_sets[0]]
        bad_out = [g["color"] for g in group_sets[1]]
        assert valid_out == ["red", "blue", "green", "yellow"]
        assert bad_out == COLOR_PALETTE[:4]

    def test_all_group_sets_validated(self):
        bad1 = [make_group(color="pink", category=f"Cat {i}") for i in range(4)]
        bad2 = [make_group(color="cyan", category=f"Cat {i}") for i in range(4)]
        data = make_data([bad1, bad2])
        result = fix_color_groups(data)
        for gs in result["game_sets"][0]["group_sets"]:
            out = [g["color"] for g in gs]
            assert out == COLOR_PALETTE[:4]


# Multiple game_sets

class TestMultipleGameSets:
    def test_multiple_game_sets_each_fixed(self):
        bad = [make_group(color="pink", category=f"Cat {i}") for i in range(4)]
        data = {
            "game_sets": [
                {"theme": "T1", "group_sets": [bad]},
                {"theme": "T2", "group_sets": [bad]},
            ]
        }
        result = fix_color_groups(data)
        for gs_obj in result["game_sets"]:
            out = [g["color"] for g in gs_obj["group_sets"][0]]
            assert out == COLOR_PALETTE[:4]


# Missing keys (graceful handling)

class TestMissingKeys:
    def test_no_game_sets_key_returns_unchanged(self):
        data: Dict[str, Any] = {"other": "stuff"}
        result = fix_color_groups(data)
        assert result == {"other": "stuff"}

    def test_game_set_without_group_sets_skipped(self):
        data = {"game_sets": [{"theme": "T"}]}
        result = fix_color_groups(data)
        assert result == {"game_sets": [{"theme": "T"}]}

    def test_empty_game_sets_list_returns_unchanged(self):
        data: Dict[str, Any] = {"game_sets": []}
        result = fix_color_groups(data)
        assert result == {"game_sets": []}


# Idempotency

class TestIdempotency:
    def test_running_twice_gives_same_result(self):
        gs = [make_group(color="pink", category=f"Cat {i}") for i in range(4)]
        data = make_data([gs])
        first = fix_color_groups(data)
        second = fix_color_groups(first)
        out1 = [g["color"] for g in first["game_sets"][0]["group_sets"][0]]
        out2 = [g["color"] for g in second["game_sets"][0]["group_sets"][0]]
        assert out1 == out2

    def test_valid_data_identical_after_two_runs(self):
        data = make_data()
        r1 = fix_color_groups(data)
        r2 = fix_color_groups(r1)
        assert r1 == r2
