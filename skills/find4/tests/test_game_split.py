"""Tests for game_split.py -- make_slug, split_game, mark_combined, and CLI main()."""

import json
import sys
import tempfile
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# Shared fixtures

def make_group(color: str = "red", category: str = "Cat", group_item_id: str = "aabbcc", group_set_id: str = "112233") -> Dict[str, Any]:
    return {
        "words": ["alpha", "beta", "gamma", "delta"],
        "category": category,
        "color": color,
        "description": "desc",
        "skill_level": "Beginner",
        "group_item_id": group_item_id,
        "group_set_id": group_set_id,
    }


def make_game_set(theme: str, game_set_id: str, group_set_id: str = "112233", group_item_ids: list[str] | None = None) -> Dict[str, Any]:
    colors = ["red", "blue", "green", "yellow"]
    ids = group_item_ids or [f"item{i}" for i in range(4)]
    return {
        "theme": theme,
        "group_sets": [[
            make_group(color=c, category=f"Cat {i}", group_item_id=ids[i], group_set_id=group_set_id)
            for i, c in enumerate(colors)
        ]],
        "game_set_id": game_set_id,
    }


def make_combined_data() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": "42ec491b61f410059dd248",
            "generated_at": "2026-05-04T14:10:00Z",
            "source_id": "test.pdf",
            "id_registry": {
                "game_set_ids": ["8a468e", "5cbc0c"],
                "group_set_ids": ["gs001", "gs002"],
                "group_item_ids": ["gi001", "gi002", "gi003", "gi004", "gi005", "gi006", "gi007", "gi008"],
            },
        },
        "game_sets": [
            make_game_set(
                "eBPF Core Architecture & Runtime",
                "8a468e",
                group_set_id="gs001",
                group_item_ids=["gi001", "gi002", "gi003", "gi004"],
            ),
            make_game_set(
                "eBPF Development Ecosystem & Tools",
                "5cbc0c",
                group_set_id="gs002",
                group_item_ids=["gi005", "gi006", "gi007", "gi008"],
            ),
        ],
    }


# TestMakeSlug

class TestMakeSlug:
    def test_basic_lowercasing(self):
        import game_split
        assert game_split.make_slug("Hello World") == "hello-world"

    def test_ampersand_converted_to_and(self):
        import game_split
        assert game_split.make_slug("Rock & Roll") == "rock-and-roll"

    def test_spaces_become_hyphens(self):
        import game_split
        assert game_split.make_slug("foo bar baz") == "foo-bar-baz"

    def test_special_chars_stripped(self):
        import game_split
        assert game_split.make_slug("hello! world?") == "hello-world"

    def test_leading_trailing_hyphens_stripped(self):
        import game_split
        assert game_split.make_slug("!hello world!") == "hello-world"

    def test_mixed_case_with_ampersand_and_spaces(self):
        import game_split
        assert game_split.make_slug("eBPF Core Architecture & Runtime") == "ebpf-core-architecture-and-runtime"


# TestCollectIds

class TestCollectIds:
    def test_collects_game_set_id(self):
        import game_split
        gs = make_game_set("T", "game1", group_set_id="gs1", group_item_ids=["i1", "i2", "i3", "i4"])
        gids, _, _ = game_split._collect_ids(gs)
        assert gids == {"game1"}

    def test_collects_group_set_ids(self):
        import game_split
        gs = make_game_set("T", "game1", group_set_id="gs1", group_item_ids=["i1", "i2", "i3", "i4"])
        _, gsids, _ = game_split._collect_ids(gs)
        assert gsids == {"gs1"}

    def test_collects_group_item_ids(self):
        import game_split
        gs = make_game_set("T", "game1", group_set_id="gs1", group_item_ids=["i1", "i2", "i3", "i4"])
        _, _, giids = game_split._collect_ids(gs)
        assert giids == {"i1", "i2", "i3", "i4"}

    def test_missing_game_set_id_returns_empty_set(self):
        import game_split
        gs = {"theme": "T", "group_sets": []}
        gids, gsids, giids = game_split._collect_ids(gs)
        assert gids == set()
        assert gsids == set()
        assert giids == set()


# TestPruneIdRegistry

class TestPruneIdRegistry:
    def test_keeps_only_matching_ids(self):
        import game_split
        registry = {
            "game_set_ids": ["a", "b"],
            "group_set_ids": ["g1", "g2"],
            "group_item_ids": ["i1", "i2", "i3"],
        }
        result = game_split._prune_id_registry(registry, {"a"}, {"g1"}, {"i1", "i2"})
        assert result["game_set_ids"] == ["a"]
        assert result["group_set_ids"] == ["g1"]
        assert result["group_item_ids"] == ["i1", "i2"]

    def test_preserves_order(self):
        import game_split
        registry = {"game_set_ids": ["z", "a", "m"], "group_set_ids": [], "group_item_ids": []}
        result = game_split._prune_id_registry(registry, {"z", "m"}, set(), set())
        assert result["game_set_ids"] == ["z", "m"]

    def test_empty_registry_returns_empty_lists(self):
        import game_split
        result = game_split._prune_id_registry({}, {"a"}, {"g"}, {"i"})
        assert result == {"game_set_ids": [], "group_set_ids": [], "group_item_ids": []}

    def test_no_matches_returns_empty_lists(self):
        import game_split
        registry = {"game_set_ids": ["x"], "group_set_ids": ["y"], "group_item_ids": ["z"]}
        result = game_split._prune_id_registry(registry, set(), set(), set())
        assert result == {"game_set_ids": [], "group_set_ids": [], "group_item_ids": []}


# TestMarkCombined

class TestMarkCombined:
    def test_returns_new_object(self):
        import game_split
        data = make_combined_data()
        result = game_split.mark_combined(data, None)
        assert result is not data

    def test_does_not_mutate_input(self):
        import game_split
        data = make_combined_data()
        game_split.mark_combined(data, Path("/some/file.json"))
        assert "split_info" not in data["metadata"]

    def test_role_is_combined(self):
        import game_split
        result = game_split.mark_combined(make_combined_data(), None)
        assert result["metadata"]["split_info"]["role"] == "combined"

    def test_source_file_recorded_when_path_given(self):
        import game_split
        p = Path("/tmp/my-game.json")
        result = game_split.mark_combined(make_combined_data(), p)
        assert result["metadata"]["split_info"]["source_file"] == str(p)

    def test_source_file_is_none_when_no_path(self):
        import game_split
        result = game_split.mark_combined(make_combined_data(), None)
        assert result["metadata"]["split_info"]["source_file"] is None

    def test_split_at_is_iso_timestamp(self):
        import game_split
        result = game_split.mark_combined(make_combined_data(), None)
        ts = result["metadata"]["split_info"]["split_at"]
        assert "T" in ts and "Z" in ts or "+" in ts

    def test_existing_metadata_preserved(self):
        import game_split
        result = game_split.mark_combined(make_combined_data(), None)
        assert result["metadata"]["id"] == "42ec491b61f410059dd248"


# TestSplitGame

class TestSplitGame:
    def test_two_game_sets_produces_two_files(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            paths = game_split.split_game(data, out)
            assert len(paths) == 2
            for p in paths:
                assert p.exists()

    def test_returns_two_paths(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir))
            assert len(paths) == 2

    def test_each_output_file_contains_exactly_one_game_set(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir))
            for p in paths:
                content = json.loads(p.read_text(encoding="utf-8"))
                assert len(content["game_sets"]) == 1

    def test_output_filename_derived_from_theme_slug(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir))
            names = {p.name for p in paths}
            assert "ebpf-core-architecture-and-runtime.json" in names
            assert "ebpf-development-ecosystem-and-tools.json" in names

    def test_top_level_metadata_preserved_in_each_split_file(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir))
            for p in paths:
                content = json.loads(p.read_text(encoding="utf-8"))
                assert content["metadata"]["id"] == "42ec491b61f410059dd248"

    def test_dry_run_writes_no_files(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            paths = game_split.split_game(data, out, dry_run=True)
            for p in paths:
                assert not p.exists()

    def test_dry_run_still_returns_paths(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir), dry_run=True)
            assert len(paths) == 2

    def test_empty_game_sets_raises_value_error(self):
        import game_split
        data = {**make_combined_data(), "game_sets": []}
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="game_sets"):
                game_split.split_game(data, Path(tmpdir))

    def test_missing_game_sets_key_raises_value_error(self):
        import game_split
        data = {"metadata": {"id": "abc"}}
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="game_sets"):
                game_split.split_game(data, Path(tmpdir))

    def test_split_info_role_is_split(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir))
            for p in paths:
                content = json.loads(p.read_text(encoding="utf-8"))
                assert content["metadata"]["split_info"]["role"] == "split"

    def test_split_info_parent_id_matches_combined(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir))
            for p in paths:
                content = json.loads(p.read_text(encoding="utf-8"))
                assert content["metadata"]["split_info"]["parent_id"] == "42ec491b61f410059dd248"

    def test_split_info_theme_matches_game_set(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir))
            contents = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
            themes = {c["metadata"]["split_info"]["theme"] for c in contents}
            assert themes == {"eBPF Core Architecture & Runtime", "eBPF Development Ecosystem & Tools"}

    def test_split_info_slug_matches_filename(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir))
            for p in paths:
                content = json.loads(p.read_text(encoding="utf-8"))
                assert content["metadata"]["split_info"]["slug"] == p.stem

    def test_split_info_parent_file_recorded_when_source_path_given(self):
        import game_split
        data = make_combined_data()
        fake_path = Path("/tmp/combined.json")
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir), source_path=fake_path)
            for p in paths:
                content = json.loads(p.read_text(encoding="utf-8"))
                assert content["metadata"]["split_info"]["parent_file"] == str(fake_path)

    def test_split_info_parent_file_is_none_without_source_path(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir))
            for p in paths:
                content = json.loads(p.read_text(encoding="utf-8"))
                assert content["metadata"]["split_info"]["parent_file"] is None

    def test_id_registry_pruned_to_this_game_set_only(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir))
            first = json.loads(paths[0].read_text(encoding="utf-8"))
            second = json.loads(paths[1].read_text(encoding="utf-8"))
            first_reg = first["metadata"]["id_registry"]
            second_reg = second["metadata"]["id_registry"]
            # game_set_ids must not overlap
            assert set(first_reg["game_set_ids"]).isdisjoint(set(second_reg["game_set_ids"]))
            # each split has exactly one game_set_id
            assert len(first_reg["game_set_ids"]) == 1
            assert len(second_reg["game_set_ids"]) == 1

    def test_id_registry_group_item_ids_match_split_content(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir))
            for p in paths:
                content = json.loads(p.read_text(encoding="utf-8"))
                reg_ids = set(content["metadata"]["id_registry"]["group_item_ids"])
                actual_ids = {
                    item["group_item_id"]
                    for gs in content["game_sets"]
                    for group_set in gs["group_sets"]
                    for item in group_set
                }
                assert reg_ids == actual_ids

    def test_id_registry_group_set_ids_match_split_content(self):
        import game_split
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = game_split.split_game(data, Path(tmpdir))
            for p in paths:
                content = json.loads(p.read_text(encoding="utf-8"))
                reg_ids = set(content["metadata"]["id_registry"]["group_set_ids"])
                actual_ids = {
                    item["group_set_id"]
                    for gs in content["game_sets"]
                    for group_set in gs["group_sets"]
                    for item in group_set
                }
                assert reg_ids == actual_ids

    def test_original_data_not_mutated(self):
        import game_split
        import copy
        data = make_combined_data()
        original = copy.deepcopy(data)
        with tempfile.TemporaryDirectory() as tmpdir:
            game_split.split_game(data, Path(tmpdir))
        assert data == original


# TestGameSplitCli

class TestGameSplitCli:
    def _run(self, argv: List[str], stdin: str | None = None) -> tuple[int, str, str]:
        import game_split
        out = StringIO()
        err = StringIO()
        exit_code = 0
        try:
            with patch("sys.argv", ["game_split.py"] + argv), \
                 patch("sys.stdout", out), \
                 patch("sys.stderr", err):
                if stdin is not None:
                    with patch("sys.stdin", StringIO(stdin)):
                        game_split.main()
                else:
                    game_split.main()
        except SystemExit as e:
            exit_code = e.code or 0
        return exit_code, out.getvalue(), err.getvalue()

    def test_file_input_splits_correctly_and_prints_two_paths(self):
        data = make_combined_data()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            tmp = f.name
        try:
            with tempfile.TemporaryDirectory() as outdir:
                code, out, _ = self._run([tmp, "--output-dir", outdir])
                assert code == 0
                lines = [l for l in out.strip().splitlines() if l]
                assert len(lines) == 2
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_stdin_input_splits_correctly(self):
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as outdir:
            code, out, _ = self._run(["--output-dir", outdir], stdin=json.dumps(data))
            assert code == 0
            lines = [l for l in out.strip().splitlines() if l]
            assert len(lines) == 2

    def test_dry_run_prints_paths_but_creates_no_files(self):
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as outdir:
            code, out, _ = self._run(
                ["--dry-run", "--output-dir", outdir],
                stdin=json.dumps(data),
            )
            assert code == 0
            lines = [l for l in out.strip().splitlines() if l]
            assert len(lines) == 2
            for line in lines:
                assert not Path(line).exists()

    def test_output_dir_flag_uses_specified_dir(self):
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as outdir:
            code, out, _ = self._run(["--output-dir", outdir], stdin=json.dumps(data))
            assert code == 0
            for line in out.strip().splitlines():
                assert str(outdir) in line

    def test_default_output_dir_when_file_input_is_parent_slash_stem(self):
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "my-game.json"
            input_path.write_text(json.dumps(data), encoding="utf-8")
            code, out, _ = self._run([str(input_path)])
            assert code == 0
            for line in out.strip().splitlines():
                expected_dir = str(Path(tmpdir) / "my-game")
                assert line.startswith(expected_dir)

    def test_missing_input_file_exits_1_with_error(self):
        code, _, err = self._run(["/nonexistent/missing-file.json"])
        assert code == 1
        assert "nonexistent" in err or "missing-file" in err or "Error" in err

    def test_invalid_json_file_exits_1(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{not valid json{{")
            tmp = f.name
        try:
            code, _, err = self._run([tmp])
            assert code == 1
            assert "JSON" in err or "json" in err.lower()
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_invalid_json_stdin_exits_1(self):
        code, _, err = self._run([], stdin="{{{not json")
        assert code == 1
        assert "JSON" in err or "json" in err.lower()

    def test_no_game_sets_exits_1(self):
        data = {**make_combined_data(), "game_sets": []}
        with tempfile.TemporaryDirectory() as outdir:
            code, _, err = self._run(
                ["--output-dir", outdir],
                stdin=json.dumps(data),
            )
            assert code == 1
            assert "game_sets" in err or "Error" in err

    def test_mark_combined_rewrites_input_file(self):
        data = make_combined_data()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            tmp = Path(f.name)
        try:
            with tempfile.TemporaryDirectory() as outdir:
                code, _, _ = self._run([str(tmp), "--mark-combined", "--output-dir", outdir])
                assert code == 0
                updated = json.loads(tmp.read_text(encoding="utf-8"))
                assert updated["metadata"]["split_info"]["role"] == "combined"
        finally:
            tmp.unlink(missing_ok=True)

    def test_mark_combined_source_file_is_absolute_path(self):
        data = make_combined_data()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            tmp = Path(f.name)
        try:
            with tempfile.TemporaryDirectory() as outdir:
                self._run([str(tmp), "--mark-combined", "--output-dir", outdir])
                updated = json.loads(tmp.read_text(encoding="utf-8"))
                assert Path(updated["metadata"]["split_info"]["source_file"]).is_absolute()
        finally:
            tmp.unlink(missing_ok=True)

    def test_mark_combined_ignored_for_stdin_input(self):
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as outdir:
            code, out, _ = self._run(
                ["--mark-combined", "--output-dir", outdir],
                stdin=json.dumps(data),
            )
            assert code == 0
            lines = [l for l in out.strip().splitlines() if l]
            assert len(lines) == 2

    def test_split_files_have_pruned_id_registry(self):
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as outdir:
            code, out, _ = self._run(["--output-dir", outdir], stdin=json.dumps(data))
            assert code == 0
            for line in out.strip().splitlines():
                p = Path(line.strip())
                if not p.exists():
                    continue
                content = json.loads(p.read_text(encoding="utf-8"))
                reg = content["metadata"]["id_registry"]
                assert len(reg["game_set_ids"]) == 1
                assert len(reg["group_set_ids"]) == 1

    def test_split_files_have_split_info_metadata(self):
        data = make_combined_data()
        with tempfile.TemporaryDirectory() as outdir:
            code, out, _ = self._run(["--output-dir", outdir], stdin=json.dumps(data))
            assert code == 0
            for line in out.strip().splitlines():
                p = Path(line.strip())
                if not p.exists():
                    continue
                content = json.loads(p.read_text(encoding="utf-8"))
                assert content["metadata"]["split_info"]["role"] == "split"
                assert "split_at" in content["metadata"]["split_info"]
                assert "parent_id" in content["metadata"]["split_info"]
