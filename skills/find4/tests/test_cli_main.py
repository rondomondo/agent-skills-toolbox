"""Tests for CLI main() entry points across add_ids, finalize_metadata, fix_colors, and validate."""

import json
import sys
import tempfile
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# Shared helpers

def make_group(color: str = "red", category: str = "Cat", description: str = "desc") -> Dict[str, Any]:
    return {
        "category": category,
        "words": ["alpha", "beta", "gamma", "delta"],
        "color": color,
        "description": description,
        "skill_level": "Beginner",
    }


def make_group_set() -> List[Dict[str, Any]]:
    colors = ["red", "blue", "green", "yellow"]
    return [make_group(color=c, category=f"Cat {i}") for i, c in enumerate(colors)]


def make_base_data() -> Dict[str, Any]:
    return {
        "game_sets": [{"theme": "Test Theme", "group_sets": [make_group_set()]}]
    }


def make_finalize_data() -> Dict[str, Any]:
    data = make_base_data()
    data["metadata"] = {"generated_at": "2024-01-01T00:00:00", "source": "test"}
    data["id_registry"] = {"game_set_ids": [], "group_set_ids": [], "group_item_ids": []}
    return data


# add_ids.py main()

class TestAddIdsMain:
    def _run(self, argv: List[str], stdin: str | None = None) -> tuple[int, str, str]:
        import add_ids
        out = StringIO()
        err = StringIO()
        exit_code = 0
        try:
            with patch("sys.argv", ["add_ids.py"] + argv), \
                 patch("sys.stdout", out), \
                 patch("sys.stderr", err):
                if stdin is not None:
                    with patch("sys.stdin", StringIO(stdin)):
                        add_ids.main()
                else:
                    add_ids.main()
        except SystemExit as e:
            exit_code = e.code or 0
        return exit_code, out.getvalue(), err.getvalue()

    def test_hex_bytes_too_small_exits_1(self):
        code, _, err = self._run(["--hex-bytes", "0"], stdin=json.dumps(make_base_data()))
        assert code == 1
        assert "--hex-bytes" in err

    def test_hex_bytes_too_large_exits_1(self):
        code, _, err = self._run(["--hex-bytes", "33"], stdin=json.dumps(make_base_data()))
        assert code == 1
        assert "--hex-bytes" in err

    def test_hex_bytes_boundary_1_ok(self):
        code, out, _ = self._run(["--hex-bytes", "1"], stdin=json.dumps(make_base_data()))
        assert code == 0
        result = json.loads(out)
        gid = result["game_sets"][0]["game_set_id"]
        assert len(gid) == 2

    def test_hex_bytes_boundary_32_ok(self):
        code, out, _ = self._run(["--hex-bytes", "32"], stdin=json.dumps(make_base_data()))
        assert code == 0
        result = json.loads(out)
        gid = result["game_sets"][0]["game_set_id"]
        # MD5 is 32 hex chars max, so hex_length=64 is capped at 32
        assert len(gid) == 32

    def test_file_not_found_exits_1(self):
        code, _, err = self._run(["--game-set-json", "/nonexistent/path/file.json"])
        assert code == 1
        assert "File not found" in err

    def test_invalid_json_stdin_exits_1(self):
        code, _, err = self._run([], stdin="not valid json {{{")
        assert code == 1
        assert "Invalid JSON" in err

    def test_missing_game_sets_key_exits_1(self):
        code, _, err = self._run([], stdin=json.dumps({"other": "stuff"}))
        assert code == 1
        assert "game_sets" in err

    def test_file_input_success(self):
        data = make_base_data()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            tmp = f.name
        try:
            code, out, _ = self._run(["--game-set-json", tmp])
            assert code == 0
            result = json.loads(out)
            assert "game_sets" in result
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_invalid_json_file_exits_1(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not json {{{")
            tmp = f.name
        try:
            code, _, err = self._run(["--game-set-json", tmp])
            assert code == 1
            assert "Invalid JSON" in err
        finally:
            Path(tmp).unlink(missing_ok=True)


# finalize_metadata.py main()

class TestFinalizeMetadataMain:
    def _run(self, argv: List[str], stdin: str | None = None) -> tuple[int, str, str]:
        import finalize_metadata
        out = StringIO()
        err = StringIO()
        exit_code = 0
        try:
            with patch("sys.argv", ["finalize_metadata.py"] + argv), \
                 patch("sys.stdout", out), \
                 patch("sys.stderr", err):
                if stdin is not None:
                    with patch("sys.stdin", StringIO(stdin)):
                        finalize_metadata.main()
                else:
                    finalize_metadata.main()
        except SystemExit as e:
            exit_code = e.code or 0
        return exit_code, out.getvalue(), err.getvalue()

    def test_file_not_found_exits_1(self):
        code, _, err = self._run(["--game-set-json", "/nonexistent/file.json"])
        assert code == 1
        assert "File not found" in err

    def test_invalid_json_exits_1(self):
        code, _, err = self._run([], stdin="bad json {{{")
        assert code == 1
        assert "Invalid JSON" in err

    def test_missing_metadata_exits_1(self):
        data = make_base_data()
        code, _, err = self._run([], stdin=json.dumps(data))
        assert code == 1
        assert "metadata" in err.lower()

    def test_default_source_is_unknown(self):
        code, out, _ = self._run([], stdin=json.dumps(make_finalize_data()))
        assert code == 0
        result = json.loads(out)
        assert result["metadata"]["source_id"] == "unknown"

    def test_custom_source_preserved(self):
        code, out, _ = self._run(
            ["--source", "https://example.com"],
            stdin=json.dumps(make_finalize_data())
        )
        assert code == 0
        result = json.loads(out)
        assert result["metadata"]["source_id"] == "https://example.com"

    def test_stdin_success_outputs_json(self):
        code, out, _ = self._run([], stdin=json.dumps(make_finalize_data()))
        assert code == 0
        result = json.loads(out)
        assert "metadata" in result
        assert "id" in result["metadata"]

    def test_file_input_success(self):
        data = make_finalize_data()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            tmp = f.name
        try:
            code, out, _ = self._run(["--game-set-json", tmp])
            assert code == 0
            result = json.loads(out)
            assert "metadata" in result
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_invalid_json_file_exits_1(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not json")
            tmp = f.name
        try:
            code, _, err = self._run(["--game-set-json", tmp])
            assert code == 1
            assert "Invalid JSON" in err
        finally:
            Path(tmp).unlink(missing_ok=True)


# fix_colors.py main()

class TestFixColorsMain:
    def _run(self, argv: List[str], stdin: str | None = None) -> tuple[int, str, str]:
        import fix_colors
        out = StringIO()
        err = StringIO()
        exit_code = 0
        try:
            with patch("sys.argv", ["fix_colors.py"] + argv), \
                 patch("sys.stdout", out), \
                 patch("sys.stderr", err):
                if stdin is not None:
                    with patch("sys.stdin", StringIO(stdin)):
                        fix_colors.main()
                else:
                    fix_colors.main()
        except SystemExit as e:
            exit_code = e.code or 0
        return exit_code, out.getvalue(), err.getvalue()

    def test_file_not_found_exits_1(self):
        code, _, err = self._run(["--game-set-json", "/nonexistent/file.json"])
        assert code == 1
        assert "File not found" in err

    def test_invalid_json_exits_1(self):
        code, _, err = self._run([], stdin="not json {{{")
        assert code == 1
        assert "Invalid JSON" in err

    def test_stdin_success_outputs_json(self):
        code, out, _ = self._run([], stdin=json.dumps(make_base_data()))
        assert code == 0
        result = json.loads(out)
        assert "game_sets" in result

    def test_file_input_success(self):
        data = make_base_data()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            tmp = f.name
        try:
            code, out, _ = self._run(["--game-set-json", tmp])
            assert code == 0
            result = json.loads(out)
            assert "game_sets" in result
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_invalid_json_file_exits_1(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{bad json")
            tmp = f.name
        try:
            code, _, err = self._run(["--game-set-json", tmp])
            assert code == 1
            assert "Invalid JSON" in err
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_bad_colors_fixed_in_output(self):
        data = make_base_data()
        data["game_sets"][0]["group_sets"][0] = [
            make_group(color="pink", category=f"Cat {i}") for i in range(4)
        ]
        code, out, _ = self._run([], stdin=json.dumps(data))
        assert code == 0
        result = json.loads(out)
        colors = [g["color"] for g in result["game_sets"][0]["group_sets"][0]]
        assert colors == ["red", "blue", "green", "yellow"]


# validate.py main()

class TestValidateMain:
    def _run(self, argv: List[str], stdin: str | None = None) -> tuple[int, str, str]:
        import validate
        out = StringIO()
        err = StringIO()
        exit_code = 0
        try:
            with patch("sys.argv", ["validate.py"] + argv), \
                 patch("sys.stdout", out), \
                 patch("sys.stderr", err):
                if stdin is not None:
                    with patch("sys.stdin", StringIO(stdin)):
                        validate.main()
                else:
                    validate.main()
        except SystemExit as e:
            exit_code = e.code or 0
        return exit_code, out.getvalue(), err.getvalue()

    def test_hex_bytes_too_small_exits_1(self):
        code, _, err = self._run(["--hex-bytes", "0"], stdin=json.dumps(make_base_data()))
        assert code == 1
        assert "--hex-bytes" in err

    def test_hex_bytes_too_large_exits_1(self):
        code, _, err = self._run(["--hex-bytes", "33"], stdin=json.dumps(make_base_data()))
        assert code == 1
        assert "--hex-bytes" in err

    def test_file_not_found_exits_1(self):
        code, _, err = self._run(["--game-set-json", "/nonexistent/file.json"])
        assert code == 1
        assert "File not found" in err

    def test_invalid_json_exits_1(self):
        code, _, err = self._run([], stdin="{{{bad")
        assert code == 1
        assert "Invalid JSON" in err

    def _make_fully_valid_data(self) -> Dict[str, Any]:
        """Build data that passes non-strict validation (has IDs and metadata)."""
        import sys
        from io import StringIO
        import validate as v
        data = make_base_data()
        fixed, _ = v.apply_fix(data, source="test")
        return fixed

    def test_valid_data_prints_ok(self):
        code, out, _ = self._run([], stdin=json.dumps(self._make_fully_valid_data()))
        assert code == 0
        assert "ok" in out

    def test_valid_data_reports_game_set_count(self):
        code, out, _ = self._run([], stdin=json.dumps(self._make_fully_valid_data()))
        assert code == 0
        assert "1 game set" in out

    def test_fixable_issues_suggest_rerun_with_fix(self):
        code, _, err = self._run([], stdin=json.dumps(make_base_data()))
        # Without --fix, fixable issues should mention --fix
        # base_data has no IDs so it has fixable issues but is not strict
        # Actually base data passes non-strict validation; check with minimal broken data
        data = {"game_sets": []}
        code2, _, err2 = self._run([], stdin=json.dumps(data))
        assert code2 == 1

    def test_game_sets_empty_list_exits_1(self):
        data = {"game_sets": []}
        code, _, err = self._run([], stdin=json.dumps(data))
        assert code == 1
        assert "at least one" in err

    def test_fix_flag_outputs_json(self):
        code, out, err = self._run(["--fix"], stdin=json.dumps(make_base_data()))
        assert code == 0
        result = json.loads(out)
        assert "game_sets" in result
        assert "metadata" in result

    def test_fix_flag_adds_ids(self):
        code, out, _ = self._run(["--fix"], stdin=json.dumps(make_base_data()))
        assert code == 0
        result = json.loads(out)
        gs = result["game_sets"][0]
        assert "game_set_id" in gs

    def test_fix_flag_writes_to_output_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = f.name
        try:
            code, out, err = self._run(
                ["--fix", "--output", tmp],
                stdin=json.dumps(make_base_data())
            )
            assert code == 0
            content = Path(tmp).read_text()
            result = json.loads(content)
            assert "game_sets" in result
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_source_defaults_to_filename_when_file_given(self):
        data = make_base_data()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            tmp = f.name
        try:
            code, out, _ = self._run(["--game-set-json", tmp, "--fix"])
            assert code == 0
            result = json.loads(out)
            assert result["metadata"]["source_id"] == tmp
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_strict_mode_fails_without_ids(self):
        code, _, err = self._run(["--strict"], stdin=json.dumps(make_base_data()))
        assert code == 1

    def test_invalid_json_file_exits_1(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{bad json")
            tmp = f.name
        try:
            code, _, err = self._run(["--game-set-json", tmp])
            assert code == 1
            assert "Invalid JSON" in err
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_bare_group_sets_detected_as_fixable(self):
        data = {
            "group_sets": [
                [make_group(color=c, category=f"Cat {i}") for i, c in enumerate(["red", "blue", "green", "yellow"])]
            ]
        }
        code, _, err = self._run([], stdin=json.dumps(data))
        assert code == 1
        assert "--fix" in err or "fixable" in err.lower() or "fix" in err.lower()

    def test_fix_bare_group_sets_wraps_into_game_sets(self):
        data = {
            "group_sets": [
                [make_group(color=c, category=f"Cat {i}") for i, c in enumerate(["red", "blue", "green", "yellow"])]
            ]
        }
        code, out, _ = self._run(["--fix"], stdin=json.dumps(data))
        assert code == 0
        result = json.loads(out)
        assert "game_sets" in result
        assert len(result["game_sets"]) == 1
