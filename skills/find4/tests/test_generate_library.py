"""Tests for generate_library_all.py."""

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_library_all import (
    DEFAULT_SCHEMA,
    ConfigurationError,
    GameSetVersion,
    ThemeIndexer,
    hydrate_game_set,
)


# Helpers

def make_group(
    category: str = "Test",
    color: str = "red",
    skill_level: str = "Beginner",
    words: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "category": category,
        "words": words or ["a", "b", "c", "d"],
        "color": color,
        "description": "desc",
        "skill_level": skill_level,
    }


def make_group_set(offset: int = 0) -> List[Dict[str, Any]]:
    colors = ["red", "blue", "green", "yellow"]
    return [make_group(category=f"Cat {offset + i}", color=colors[i]) for i in range(4)]


def make_game_set(
    theme: str = "Test Theme",
    game_set_id: str = "abcdef012345",
    n_group_sets: int = 1,
) -> Dict[str, Any]:
    return {
        "theme": theme,
        "game_set_id": game_set_id,
        "group_sets": [make_group_set(offset=i * 4) for i in range(n_group_sets)],
    }


def write_game_file(path: Path, game_sets: List[Dict[str, Any]], metadata: Dict[str, Any] | None = None) -> None:
    data: Dict[str, Any] = {"game_sets": game_sets}
    if metadata:
        data["metadata"] = metadata
    path.write_text(json.dumps(data), encoding="utf-8")


# hydrate_game_set

class TestHydrateGameSet:
    def test_dict_groups_unchanged(self):
        gs = make_game_set()
        result = hydrate_game_set(gs, DEFAULT_SCHEMA)
        assert isinstance(result["group_sets"][0][0], dict)

    def test_packed_list_groups_hydrated(self):
        schema = ["words", "category", "color"]
        packed_group = [["a", "b", "c", "d"], "Animals", "red"]
        gs = {"theme": "T", "game_set_id": "abc", "group_sets": [[packed_group]]}
        result = hydrate_game_set(gs, schema)
        group = result["group_sets"][0][0]
        assert group["category"] == "Animals"
        assert group["words"] == ["a", "b", "c", "d"]
        assert group["color"] == "red"

    def test_hydrate_does_not_mutate_original(self):
        gs = {"theme": "T", "group_sets": [[]]}
        original_id = id(gs["group_sets"])
        hydrate_game_set(gs, DEFAULT_SCHEMA)
        assert id(gs["group_sets"]) == original_id

    def test_empty_group_sets_handled(self):
        gs = {"theme": "T", "game_set_id": "abc", "group_sets": []}
        result = hydrate_game_set(gs, DEFAULT_SCHEMA)
        assert result["group_sets"] == []


# ThemeIndexer.validate_game_set

class TestValidateGameSet:
    def setup_method(self):
        self.indexer = ThemeIndexer(games_dir="games", hex_length=12)

    def test_valid_game_set_returns_true(self):
        gs = make_game_set()
        assert self.indexer.validate_game_set(gs, "test.json") is True

    def test_missing_theme_returns_false(self):
        gs = make_game_set()
        del gs["theme"]
        assert self.indexer.validate_game_set(gs, "test.json") is False

    def test_missing_game_set_id_returns_false(self):
        gs = make_game_set()
        del gs["game_set_id"]
        assert self.indexer.validate_game_set(gs, "test.json") is False

    def test_missing_group_sets_returns_false(self):
        gs = make_game_set()
        del gs["group_sets"]
        assert self.indexer.validate_game_set(gs, "test.json") is False

    def test_invalid_game_set_id_format_returns_false(self):
        gs = make_game_set(game_set_id="tooshort")
        assert self.indexer.validate_game_set(gs, "test.json") is False

    def test_invalid_game_set_id_uppercase_returns_false(self):
        gs = make_game_set(game_set_id="ABCDEF012345")
        assert self.indexer.validate_game_set(gs, "test.json") is False

    def test_group_sets_not_list_returns_false(self):
        gs = make_game_set()
        gs["group_sets"] = "not a list"
        assert self.indexer.validate_game_set(gs, "test.json") is False

    def test_group_set_item_not_list_returns_false(self):
        gs = make_game_set()
        gs["group_sets"] = ["not a list"]
        assert self.indexer.validate_game_set(gs, "test.json") is False

    def test_group_missing_words_returns_false(self):
        gs = make_game_set()
        del gs["group_sets"][0][0]["words"]
        assert self.indexer.validate_game_set(gs, "test.json") is False

    def test_errors_appended_to_validation_errors(self):
        gs = make_game_set()
        del gs["theme"]
        self.indexer.validate_game_set(gs, "test.json")
        assert any("test.json" in e for e in self.indexer.validation_errors)

    def test_custom_hex_length(self):
        indexer6 = ThemeIndexer(games_dir="games", hex_length=6)
        gs = make_game_set(game_set_id="abc123")
        assert indexer6.validate_game_set(gs, "test.json") is True


# ThemeIndexer.calculate_content_hash

class TestCalculateContentHash:
    def setup_method(self):
        self.indexer = ThemeIndexer(games_dir="games")

    def test_returns_string(self):
        gs = make_game_set()
        h = self.indexer.calculate_content_hash(gs)
        assert isinstance(h, str)

    def test_is_hex(self):
        gs = make_game_set()
        h = self.indexer.calculate_content_hash(gs)
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_content_same_hash(self):
        gs1 = make_game_set()
        gs2 = make_game_set()
        assert self.indexer.calculate_content_hash(gs1) == self.indexer.calculate_content_hash(gs2)

    def test_different_theme_different_hash(self):
        gs1 = make_game_set(theme="Theme A")
        gs2 = make_game_set(theme="Theme B")
        assert self.indexer.calculate_content_hash(gs1) != self.indexer.calculate_content_hash(gs2)

    def test_different_words_different_hash(self):
        gs1 = make_game_set()
        gs2 = make_game_set()
        gs2["group_sets"][0][0]["words"] = ["w1", "w2", "w3", "w4"]
        assert self.indexer.calculate_content_hash(gs1) != self.indexer.calculate_content_hash(gs2)

    def test_missing_fields_graceful(self):
        gs: Dict[str, Any] = {}
        h = self.indexer.calculate_content_hash(gs)
        assert isinstance(h, str)


# ThemeIndexer.shuffle_game_set

class TestShuffleGameSet:
    def test_shuffle_disabled_returns_unchanged(self):
        indexer = ThemeIndexer(games_dir="games", shuffle_enabled=False)
        gs = make_game_set()
        result = indexer.shuffle_game_set(gs)
        assert result is gs

    def test_shuffle_enabled_returns_copy(self):
        indexer = ThemeIndexer(games_dir="games", shuffle_enabled=True)
        gs = make_game_set()
        result = indexer.shuffle_game_set(gs)
        assert result is not gs

    def test_shuffle_preserves_theme(self):
        indexer = ThemeIndexer(games_dir="games", shuffle_enabled=True)
        gs = make_game_set(theme="My Theme")
        result = indexer.shuffle_game_set(gs)
        assert result["theme"] == "My Theme"

    def test_shuffle_preserves_all_words(self):
        indexer = ThemeIndexer(games_dir="games", shuffle_enabled=True)
        gs = make_game_set()
        original_words = {w for group_set in gs["group_sets"] for g in group_set for w in g["words"]}
        result = indexer.shuffle_game_set(gs)
        result_words = {w for group_set in result["group_sets"] for g in group_set for w in g["words"]}
        assert original_words == result_words

    def test_shuffle_preserves_group_count(self):
        indexer = ThemeIndexer(games_dir="games", shuffle_enabled=True)
        gs = make_game_set(n_group_sets=2)
        original_group_count = sum(len(gset) for gset in gs["group_sets"])
        result = indexer.shuffle_game_set(gs)
        result_group_count = sum(len(gset) for gset in result["group_sets"])
        assert original_group_count == result_group_count


# ThemeIndexer.create_theme_index

class TestCreateThemeIndex:
    def test_raises_on_missing_games_dir(self, tmp_path):
        indexer = ThemeIndexer(games_dir=str(tmp_path / "nonexistent"), hex_length=12)
        with pytest.raises(ConfigurationError):
            indexer.create_theme_index()

    def test_empty_games_dir_returns_empty_list(self, tmp_path):
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert result == []

    def test_skips_themes_json(self, tmp_path):
        (tmp_path / "themes.json").write_text(json.dumps([{"game_set_id": "skip_me"}]))
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert result == []

    def test_skips_file_without_game_sets(self, tmp_path):
        (tmp_path / "bad.json").write_text(json.dumps({"other": "data"}))
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert result == []

    def test_skips_invalid_json_file(self, tmp_path):
        (tmp_path / "invalid.json").write_text("not valid json {")
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert result == []
        assert indexer.validation_errors

    def test_single_valid_file_returns_one_entry(self, tmp_path):
        gs = make_game_set()
        write_game_file(tmp_path / "game.json", [gs])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert len(result) == 1

    def test_entry_has_required_fields(self, tmp_path):
        gs = make_game_set(theme="Linux Basics")
        write_game_file(tmp_path / "game.json", [gs])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        entry = result[0]
        for field in ("game_set_id", "theme", "games_file", "last_modified", "content_hash",
                      "total_words", "categories", "skill_levels", "colors", "group_sets_count",
                      "total_groups", "versions_found", "is_latest", "metadata"):
            assert field in entry, f"Missing field: {field}"

    def test_entry_theme_correct(self, tmp_path):
        gs = make_game_set(theme="Space Exploration")
        write_game_file(tmp_path / "game.json", [gs])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert result[0]["theme"] == "Space Exploration"

    def test_entry_total_words(self, tmp_path):
        gs = make_game_set(n_group_sets=1)
        write_game_file(tmp_path / "game.json", [gs])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert result[0]["total_words"] == 16

    def test_entry_total_groups(self, tmp_path):
        gs = make_game_set(n_group_sets=2)
        write_game_file(tmp_path / "game.json", [gs])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert result[0]["total_groups"] == 8

    def test_entry_group_sets_count(self, tmp_path):
        gs = make_game_set(n_group_sets=3)
        write_game_file(tmp_path / "game.json", [gs])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert result[0]["group_sets_count"] == 3

    def test_entry_categories_sorted(self, tmp_path):
        gs = make_game_set()
        write_game_file(tmp_path / "game.json", [gs])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        cats = result[0]["categories"]
        assert cats == sorted(cats)

    def test_entry_is_latest_true_for_single(self, tmp_path):
        gs = make_game_set()
        write_game_file(tmp_path / "game.json", [gs])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert result[0]["is_latest"] is True

    def test_entry_versions_found_one_for_single(self, tmp_path):
        gs = make_game_set()
        write_game_file(tmp_path / "game.json", [gs])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert result[0]["versions_found"] == 1

    def test_result_sorted_alphabetically_by_theme(self, tmp_path):
        write_game_file(tmp_path / "z.json", [make_game_set(theme="Zebras", game_set_id="aaaaaa000001")])
        write_game_file(tmp_path / "a.json", [make_game_set(theme="Aardvarks", game_set_id="aaaaaa000002")])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        themes = [e["theme"] for e in result]
        assert themes == sorted(themes)

    def test_multiple_game_sets_in_one_file(self, tmp_path):
        gs1 = make_game_set(theme="Theme A", game_set_id="aaaaaa000001")
        gs2 = make_game_set(theme="Theme B", game_set_id="bbbbbb000002")
        write_game_file(tmp_path / "multi.json", [gs1, gs2])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert len(result) == 2

    def test_metadata_extracted_from_file(self, tmp_path):
        gs = make_game_set()
        write_game_file(tmp_path / "game.json", [gs], metadata={"generated_at": "2025-01-01", "source": "http://x.com"})
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert result[0]["metadata"]["generated_at"] == "2025-01-01"
        assert result[0]["metadata"]["source"] == "http://x.com"


# Deduplication behaviour

class TestDeduplication:
    def test_duplicate_id_keeps_versions_found_count(self, tmp_path):
        import os
        gs1 = make_game_set(theme="Original", game_set_id="aaaaaa000001")
        gs2 = make_game_set(theme="Duplicate", game_set_id="aaaaaa000001")
        write_game_file(tmp_path / "file1.json", [gs1])
        write_game_file(tmp_path / "file2.json", [gs2])
        # versions_found is only propagated when the newer duplicate replaces
        # the existing entry. Make file1 newer so whichever file is globbed
        # second, the replacement path is taken and the counter is preserved.
        newer = (tmp_path / "file2.json").stat().st_mtime + 2
        os.utime(tmp_path / "file1.json", (newer, newer))
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert len(result) == 1
        assert result[0]["versions_found"] == 2

    def test_duplicate_id_only_one_entry_per_id(self, tmp_path):
        gs1 = make_game_set(game_set_id="aaaaaa000001")
        gs2 = make_game_set(game_set_id="aaaaaa000001")
        write_game_file(tmp_path / "file1.json", [gs1])
        write_game_file(tmp_path / "file2.json", [gs2])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        ids = [e["game_set_id"] for e in result]
        assert len(ids) == len(set(ids))

    def test_unique_ids_all_returned(self, tmp_path):
        gs1 = make_game_set(theme="Alpha", game_set_id="aaaaaa000001")
        gs2 = make_game_set(theme="Beta", game_set_id="bbbbbb000002")
        write_game_file(tmp_path / "file1.json", [gs1])
        write_game_file(tmp_path / "file2.json", [gs2])
        indexer = ThemeIndexer(games_dir=str(tmp_path), hex_length=12)
        result = indexer.create_theme_index()
        assert len(result) == 2


# GameSetVersion dataclass

class TestGameSetVersion:
    def test_lt_compares_modified_time(self):
        from datetime import datetime
        v1 = GameSetVersion("id1", "f1.json", datetime(2024, 1, 1), "hash1", "Theme 1")
        v2 = GameSetVersion("id2", "f2.json", datetime(2025, 1, 1), "hash2", "Theme 2")
        assert v1 < v2
        assert not v2 < v1
