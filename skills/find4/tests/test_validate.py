"""Tests for validate.py."""

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate import (
    Issue,
    apply_fix,
    validate,
    validate_game_set,
    validate_group,
    validate_group_set,
    _add_ids,
    _add_metadata,
    _detect_bare_group_sets,
    _is_valid_hex_id,
    _wrap_bare_structure,
)


# Fixtures

def make_group(
    words: List[str] | None = None,
    category: str = "Test Category",
    color: str = "red",
    description: str = "Test description",
    skill_level: str = "Beginner",
    **extra: Any,
) -> Dict[str, Any]:
    g: Dict[str, Any] = {
        "words": words if words is not None else ["alpha", "beta", "gamma", "delta"],
        "category": category,
        "color": color,
        "description": description,
        "skill_level": skill_level,
    }
    g.update(extra)
    return g


def make_group_set(colors: List[str] | None = None) -> List[Dict[str, Any]]:
    palette = colors or ["red", "blue", "green", "yellow"]
    return [make_group(color=c, category=f"Cat {i}") for i, c in enumerate(palette)]


def make_game_set(theme: str = "Test Theme", n_group_sets: int = 1) -> Dict[str, Any]:
    return {
        "theme": theme,
        "group_sets": [make_group_set() for _ in range(n_group_sets)],
    }


def make_valid_data(n_game_sets: int = 1) -> Dict[str, Any]:
    return {"game_sets": [make_game_set(f"Theme {i}") for i in range(n_game_sets)]}


# _is_valid_hex_id

class TestIsHex12:
    def test_valid_12_char(self):
        assert _is_valid_hex_id("abcdef012345", 12) is True

    def test_valid_custom_length(self):
        assert _is_valid_hex_id("abc123", 6) is True

    def test_uppercase_invalid(self):
        assert _is_valid_hex_id("ABCDEF012345", 12) is False

    def test_wrong_length(self):
        assert _is_valid_hex_id("abcdef01234", 12) is False

    def test_non_hex_chars(self):
        assert _is_valid_hex_id("abcdefg01234", 12) is False

    def test_non_string(self):
        assert _is_valid_hex_id(123456789012, 12) is False

    def test_empty_string(self):
        assert _is_valid_hex_id("", 12) is False


# _detect_bare_group_sets

class TestDetectBareGroupSets:
    def test_detects_bare(self):
        data = {"group_sets": [[]], "theme": "t"}
        assert _detect_bare_group_sets(data) is True

    def test_not_bare_when_game_sets_present(self):
        data = {"game_sets": [], "group_sets": [[]]}
        assert _detect_bare_group_sets(data) is False

    def test_not_bare_without_group_sets(self):
        data = {"game_sets": []}
        assert _detect_bare_group_sets(data) is False

    def test_non_dict(self):
        assert _detect_bare_group_sets([]) is False


# validate_group

class TestValidateGroup:
    def test_valid_group_no_issues(self):
        issues = validate_group(make_group(), "path")
        assert issues == []

    def test_missing_required_field(self):
        g = make_group()
        del g["category"]
        issues = validate_group(g, "path")
        assert any("missing required field 'category'" in str(i) for i in issues)

    def test_words_not_list(self):
        g = make_group()
        g["words"] = "not a list"
        issues = validate_group(g, "path")
        assert any("words" in str(i) for i in issues)

    def test_words_wrong_count(self):
        g = make_group(words=["a", "b", "c"])
        issues = validate_group(g, "path")
        assert any("4 items" in str(i) for i in issues)

    def test_words_non_string_items(self):
        g = make_group(words=["a", "b", "c", 4])
        issues = validate_group(g, "path")
        assert any("strings" in str(i) for i in issues)

    def test_invalid_color(self):
        g = make_group(color="pink")
        issues = validate_group(g, "path")
        assert any("color" in str(i) for i in issues)

    def test_valid_colors(self):
        for color in ("red", "blue", "green", "yellow", "orange", "indigo", "purple", "teal"):
            assert validate_group(make_group(color=color), "path") == []

    def test_invalid_skill_level(self):
        g = make_group(skill_level="Novice")
        issues = validate_group(g, "path")
        assert any("skill_level" in str(i) for i in issues)

    def test_valid_skill_levels(self):
        for lvl in ("Beginner", "Intermediate", "Advanced", "Expert"):
            assert validate_group(make_group(skill_level=lvl), "path") == []

    def test_not_a_dict(self):
        issues = validate_group("not a dict", "path")
        assert any("object" in str(i) for i in issues)

    def test_strict_requires_ids(self):
        issues = validate_group(make_group(), "path", strict=True)
        tags = {i.tag for i in issues}
        assert "missing_group_item_id" in tags
        assert "missing_group_set_id" in tags

    def test_strict_accepts_valid_ids(self):
        g = make_group()
        g["group_item_id"] = "abcdef012345"
        g["group_set_id"] = "abcdef012345"
        issues = validate_group(g, "path", strict=True, hex_length=12)
        assert issues == []

    def test_invalid_id_format_reported(self):
        g = make_group()
        g["group_item_id"] = "tooshort"
        g["group_set_id"] = "abcdef012345"
        issues = validate_group(g, "path", strict=False)
        assert any("group_item_id" in str(i) for i in issues)

    def test_custom_hex_length(self):
        g = make_group()
        g["group_item_id"] = "abcdef"
        g["group_set_id"] = "abcdef"
        issues = validate_group(g, "path", strict=True, hex_length=6)
        assert issues == []


# validate_group_set

class TestValidateGroupSet:
    def test_valid_group_set(self):
        issues = validate_group_set(make_group_set(), "path")
        assert issues == []

    def test_not_a_list(self):
        issues = validate_group_set({"not": "a list"}, "path")
        assert any("list" in str(i) for i in issues)

    def test_wrong_number_of_groups(self):
        gs = make_group_set()[:3]
        issues = validate_group_set(gs, "path")
        assert any("exactly 4 groups" in str(i) for i in issues)

    def test_duplicate_colors(self):
        gs = [make_group(color="red", category=f"Cat {i}") for i in range(4)]
        issues = validate_group_set(gs, "path")
        assert any("distinct" in str(i) for i in issues)

    def test_all_same_colors_is_one_distinct_error(self):
        gs = [make_group(color="red", category=f"Cat {i}") for i in range(4)]
        issues = validate_group_set(gs, "path")
        distinct_errors = [i for i in issues if "distinct" in str(i)]
        assert len(distinct_errors) == 1


# validate_game_set

class TestValidateGameSet:
    def test_valid_game_set(self):
        issues = validate_game_set(make_game_set(), "path")
        assert issues == []

    def test_not_a_dict(self):
        issues = validate_game_set("bad", "path")
        assert any("object" in str(i) for i in issues)

    def test_missing_theme(self):
        gs = make_game_set()
        del gs["theme"]
        issues = validate_game_set(gs, "path")
        assert any("theme" in str(i) for i in issues)

    def test_missing_group_sets(self):
        gs = make_game_set()
        del gs["group_sets"]
        issues = validate_game_set(gs, "path")
        assert any("group_sets" in str(i) for i in issues)

    def test_group_sets_not_list(self):
        gs = make_game_set()
        gs["group_sets"] = "not a list"
        issues = validate_game_set(gs, "path")
        assert any("must be a list" in str(i) for i in issues)

    def test_strict_requires_game_set_id(self):
        issues = validate_game_set(make_game_set(), "path", strict=True)
        tags = {i.tag for i in issues if i.tag}
        assert "missing_game_set_id" in tags

    def test_invalid_game_set_id_format(self):
        gs = make_game_set()
        gs["game_set_id"] = "tooshort"
        issues = validate_game_set(gs, "path")
        assert any("game_set_id" in str(i) for i in issues)

    def test_valid_game_set_id_accepted(self):
        gs = make_game_set()
        gs["game_set_id"] = "abcdef012345"
        issues = validate_game_set(gs, "path", strict=True)
        strict_id_errors = [i for i in issues if i.tag == "missing_game_set_id"]
        assert strict_id_errors == []


# validate (top-level)

class TestValidate:
    def test_valid_data_no_issues(self):
        data = make_valid_data()
        issues, _ = validate(data)
        fixable_only = [i for i in issues if i.tag == "missing_metadata" or i.tag == "missing_id_registry"]
        non_fixable = [i for i in issues if not i.is_fixable()]
        assert non_fixable == []

    def test_not_a_dict(self):
        issues, _ = validate([])
        assert any("object" in str(i) for i in issues)

    def test_missing_game_sets(self):
        issues, _ = validate({})
        assert any("game_sets" in str(i) for i in issues)

    def test_empty_game_sets(self):
        issues, _ = validate({"game_sets": []})
        assert any("at least one" in str(i) for i in issues)

    def test_bare_group_sets_detected(self):
        data = {"group_sets": [make_group_set()], "theme": "T"}
        issues, suggestions = validate(data)
        tags = {i.tag for i in issues}
        assert "missing_game_sets_wrapper" in tags
        assert any("Wrap" in s for s in suggestions)

    def test_missing_metadata_is_fixable(self):
        data = make_valid_data()
        issues, _ = validate(data)
        metadata_issues = [i for i in issues if i.tag == "missing_metadata"]
        assert all(i.is_fixable() for i in metadata_issues)

    def test_strict_missing_metadata_reported(self):
        data = make_valid_data()
        issues, _ = validate(data, strict=True)
        tags = {i.tag for i in issues}
        assert "missing_metadata" in tags

    def test_strict_missing_id_registry_reported(self):
        data = make_valid_data()
        issues, _ = validate(data, strict=True)
        tags = {i.tag for i in issues}
        assert "missing_id_registry" in tags

    def test_multiple_game_sets(self):
        data = make_valid_data(n_game_sets=3)
        issues, _ = validate(data)
        non_fixable = [i for i in issues if not i.is_fixable()]
        assert non_fixable == []

    def test_custom_hex_length(self):
        data = make_valid_data()
        _add_ids(data, hex_length=6)
        issues, _ = validate(data, strict=True, hex_length=6)
        id_issues = [i for i in issues if "group_item_id" in str(i) or "group_set_id" in str(i)]
        assert id_issues == []


# Issue class

class TestIssue:
    def test_fixable_tag(self):
        i = Issue("path", "message", "missing_metadata")
        assert i.is_fixable() is True

    def test_unfixable_no_tag(self):
        i = Issue("path", "message")
        assert i.is_fixable() is False

    def test_str_includes_fix_hint(self):
        i = Issue("path", "message", "missing_metadata")
        assert "--fix" in str(i)

    def test_str_no_fix_hint_for_unfixable(self):
        i = Issue("path", "message")
        assert "--fix" not in str(i)


# _add_ids

class TestAddIds:
    def test_adds_all_id_fields(self):
        data = make_valid_data()
        result = _add_ids(data)
        gs = result["game_sets"][0]
        assert "game_set_id" in gs
        group = gs["group_sets"][0][0]
        assert "group_item_id" in group
        assert "group_set_id" in group

    def test_id_registry_structure(self):
        data = make_valid_data()
        result = _add_ids(data)
        reg = result["id_registry"]
        assert "game_set_ids" in reg
        assert "group_set_ids" in reg
        assert "group_item_ids" in reg

    def test_ids_are_valid_hex(self):
        data = make_valid_data()
        result = _add_ids(data, hex_length=12)
        for gid in result["id_registry"]["game_set_ids"]:
            assert _is_valid_hex_id(gid, 12)

    def test_ids_are_deterministic(self):
        data1 = make_valid_data()
        data2 = make_valid_data()
        r1 = _add_ids(data1)
        r2 = _add_ids(data2)
        assert r1["game_sets"][0]["game_set_id"] == r2["game_sets"][0]["game_set_id"]

    def test_same_group_set_in_two_files_same_id(self):
        data1 = make_valid_data()
        data2 = make_valid_data()
        r1 = _add_ids(data1)
        r2 = _add_ids(data2)
        gs1 = r1["game_sets"][0]["group_sets"][0][0]["group_set_id"]
        gs2 = r2["game_sets"][0]["group_sets"][0][0]["group_set_id"]
        assert gs1 == gs2

    def test_no_duplicate_ids_in_registry(self):
        # Two identical group_sets should only appear once in registry
        data = make_valid_data(n_game_sets=1)
        data["game_sets"][0]["group_sets"].append(make_group_set())
        result = _add_ids(data)
        ids = result["id_registry"]["group_set_ids"]
        assert len(ids) == len(set(ids))

    def test_custom_hex_length_short(self):
        data = make_valid_data()
        result = _add_ids(data, hex_length=6)
        gid = result["game_sets"][0]["game_set_id"]
        assert len(gid) == 6

    def test_different_content_different_ids(self):
        data1 = make_valid_data()
        data2 = make_valid_data()
        data2["game_sets"][0]["theme"] = "Completely Different Theme"
        r1 = _add_ids(data1)
        r2 = _add_ids(data2)
        assert r1["game_sets"][0]["game_set_id"] != r2["game_sets"][0]["game_set_id"]


# _wrap_bare_structure

class TestWrapBareStructure:
    def test_moves_group_sets_into_game_sets(self):
        data = {"theme": "My Theme", "group_sets": [make_group_set()]}
        result = _wrap_bare_structure(data)
        assert "game_sets" in result
        assert len(result["game_sets"]) == 1
        assert result["game_sets"][0]["theme"] == "My Theme"
        assert "group_sets" not in result

    def test_preserves_extra_keys(self):
        data = {"theme": "T", "group_sets": [[]], "extra_key": "keep_me"}
        result = _wrap_bare_structure(data)
        assert result.get("extra_key") == "keep_me"

    def test_carries_over_game_set_id(self):
        data = {"theme": "T", "group_sets": [[]], "game_set_id": "abcdef012345"}
        result = _wrap_bare_structure(data)
        assert result["game_sets"][0]["game_set_id"] == "abcdef012345"

    def test_unknown_theme_fallback(self):
        data = {"group_sets": [[]]}
        result = _wrap_bare_structure(data)
        assert result["game_sets"][0]["theme"] == "Unknown Theme"


# _add_metadata

class TestAddMetadata:
    def test_adds_metadata_if_absent(self):
        data = make_valid_data()
        _add_ids(data)
        result = _add_metadata(data, source="test-source")
        assert "metadata" in result
        assert result["metadata"]["source"] == "test-source"

    def test_generates_stable_id(self):
        data = make_valid_data()
        _add_ids(data)
        r1 = _add_metadata(data, source="s")
        id1 = r1["metadata"]["id"]
        assert len(id1) == 22

    def test_promotes_id_registry_into_metadata(self):
        data = make_valid_data()
        _add_ids(data)
        result = _add_metadata(data)
        assert "id_registry" in result["metadata"]
        assert result["metadata"]["promoted"] is True

    def test_does_not_overwrite_existing_generated_at(self):
        data = make_valid_data()
        _add_ids(data)
        data["metadata"] = {"generated_at": "2024-01-01T00:00:00+00:00", "source": "original"}
        result = _add_metadata(data, source="new")
        assert result["metadata"]["generated_at"] == "2024-01-01T00:00:00+00:00"


# apply_fix

class TestApplyFix:
    def test_fix_bare_structure(self):
        data = {"theme": "T", "group_sets": [make_group_set()]}
        fixed, actions = apply_fix(data)
        assert "game_sets" in fixed
        assert any("Wrapped" in a for a in actions)

    def test_fix_adds_ids(self):
        data = make_valid_data()
        fixed, actions = apply_fix(data)
        assert "game_set_id" in fixed["game_sets"][0]
        assert any("IDs" in a or "id" in a.lower() for a in actions)

    def test_fix_adds_metadata(self):
        data = make_valid_data()
        fixed, actions = apply_fix(data)
        assert "metadata" in fixed

    def test_fix_does_not_mutate_original(self):
        data = make_valid_data()
        original_keys = set(data.keys())
        apply_fix(data)
        assert set(data.keys()) == original_keys

    def test_fixed_data_passes_strict_validation(self):
        data = make_valid_data()
        fixed, _ = apply_fix(data, hex_length=12)
        issues, _ = validate(fixed, strict=True, hex_length=12)
        non_fixable = [i for i in issues if not i.is_fixable()]
        assert non_fixable == []

    def test_custom_hex_length_passed_through(self):
        data = make_valid_data()
        fixed, _ = apply_fix(data, hex_length=6)
        gid = fixed["game_sets"][0]["game_set_id"]
        assert len(gid) == 6
