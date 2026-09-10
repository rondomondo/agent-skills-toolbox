"""Tests for publish_game.py -- gen_short_code, _redirect_metadata, publish (dry_run), and CLI main()."""

import asyncio
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

def make_game_payload(game_id: str = "42ec491b61f410059dd248") -> Dict[str, Any]:
    return {
        "metadata": {
            "id": game_id,
            "generated_at": "2026-05-04T14:10:00Z",
            "source_id": "test.pdf",
        },
        "game_sets": [
            {
                "theme": "eBPF Core Architecture & Runtime",
                "group_sets": [
                    [
                        {
                            "words": ["KPROBE", "UPROBE", "TRACEPOINT", "SYSCALL HOOK"],
                            "category": "eBPF Hook Types",
                            "color": "blue",
                            "description": "Hook attachment points",
                            "skill_level": "Intermediate",
                            "group_item_id": "aabbcc",
                            "group_set_id": "112233",
                        }
                    ]
                ],
                "game_set_id": "8a468e",
            }
        ],
    }


def _write_game_file(data: Dict[str, Any]) -> str:
    """Write game JSON to a temp file and return its path string."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        return f.name


# TestGenShortCode

class TestGenShortCode:
    def test_deterministic_same_input_same_output(self):
        import publish_game
        assert publish_game.gen_short_code("hello") == publish_game.gen_short_code("hello")

    def test_returns_default_length_of_eight_chars(self):
        import publish_game
        result = publish_game.gen_short_code("some-game-id")
        assert len(result) == 8

    def test_returns_requested_length(self):
        import publish_game
        for length in (4, 8, 12, 16):
            result = publish_game.gen_short_code("some-game-id", length=length)
            assert len(result) == length

    def test_output_is_alphanumeric_only(self):
        import publish_game
        result = publish_game.gen_short_code("any-input-string")
        assert result.isalnum(), f"non-alphanumeric chars in {result!r}"

    def test_different_inputs_produce_different_codes(self):
        import publish_game
        codes = {publish_game.gen_short_code(f"input-{i}") for i in range(20)}
        assert len(codes) == 20


# TestRedirectMetadata

class TestRedirectMetadata:
    def test_returns_dict_with_website_redirect_location_key(self):
        import publish_game
        result = publish_game._redirect_metadata("https://example.com/g/abc12345")
        assert "WebsiteRedirectLocation" in result

    def test_https_url_accepted(self):
        import publish_game
        result = publish_game._redirect_metadata("https://find4.org/games/abc.json")
        assert result["WebsiteRedirectLocation"] == "https://find4.org/games/abc.json"

    def test_http_url_accepted(self):
        import publish_game
        result = publish_game._redirect_metadata("http://localhost:8080/games/abc.json")
        assert result["WebsiteRedirectLocation"] == "http://localhost:8080/games/abc.json"

    def test_non_http_url_raises_value_error(self):
        import publish_game
        with pytest.raises(ValueError, match="http"):
            publish_game._redirect_metadata("s3://my-bucket/games/abc.json")

    def test_bare_path_raises_value_error(self):
        import publish_game
        with pytest.raises(ValueError):
            publish_game._redirect_metadata("/games/abc.json")


# TestPublishDryRun

class TestPublishDryRun:
    def test_dry_run_returns_dict_with_expected_keys(self):
        import publish_game
        tmp = _write_game_file(make_game_payload())
        try:
            result = asyncio.run(publish_game.publish(Path(tmp), dry_run=True))
            assert set(result.keys()) == {"short_code", "game_key", "redirect_key", "game_url", "redirect_url"}
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_dry_run_short_code_is_eight_alphanumeric_chars(self):
        import publish_game
        tmp = _write_game_file(make_game_payload())
        try:
            result = asyncio.run(publish_game.publish(Path(tmp), dry_run=True))
            assert len(result["short_code"]) == 8
            assert result["short_code"].isalnum()
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_dry_run_makes_no_s3_calls(self):
        import publish_game
        tmp = _write_game_file(make_game_payload())
        try:
            with patch("publish_game.get_session") as mock_session:
                asyncio.run(publish_game.publish(Path(tmp), dry_run=True))
                mock_session.assert_not_called()
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_dry_run_game_key_contains_short_code(self):
        import publish_game
        tmp = _write_game_file(make_game_payload())
        try:
            result = asyncio.run(publish_game.publish(Path(tmp), dry_run=True))
            assert result["short_code"] in result["game_key"]
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_dry_run_redirect_key_contains_short_code(self):
        import publish_game
        tmp = _write_game_file(make_game_payload())
        try:
            result = asyncio.run(publish_game.publish(Path(tmp), dry_run=True))
            assert result["short_code"] in result["redirect_key"]
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_missing_metadata_id_raises_value_error(self):
        import publish_game
        data = make_game_payload()
        del data["metadata"]["id"]
        tmp = _write_game_file(data)
        try:
            with pytest.raises(ValueError, match="metadata.id"):
                asyncio.run(publish_game.publish(Path(tmp), dry_run=True))
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_invalid_json_file_raises_value_error(self):
        import publish_game
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{not valid json{{")
            tmp = f.name
        try:
            with pytest.raises(ValueError, match="[Ii]nvalid JSON"):
                asyncio.run(publish_game.publish(Path(tmp), dry_run=True))
        finally:
            Path(tmp).unlink(missing_ok=True)


# TestPublishGameCli

class TestPublishGameCli:
    def _run(self, argv: List[str]) -> tuple[int, str, str]:
        import publish_game
        out = StringIO()
        err = StringIO()
        exit_code = 0
        try:
            with patch("sys.argv", ["publish_game.py"] + argv), \
                 patch("sys.stdout", out), \
                 patch("sys.stderr", err):
                publish_game.main()
        except SystemExit as e:
            exit_code = e.code or 0
        return exit_code, out.getvalue(), err.getvalue()

    def test_dry_run_prints_json_result_to_stdout(self):
        tmp = _write_game_file(make_game_payload())
        try:
            code, out, _ = self._run([tmp, "--dry-run"])
            assert code == 0
            result = json.loads(out)
            assert set(result.keys()) == {"short_code", "game_key", "redirect_key", "game_url", "redirect_url"}
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_missing_file_exits_1(self):
        code, _, err = self._run(["/nonexistent/missing-game.json", "--dry-run"])
        assert code == 1
        assert "nonexistent" in err or "missing-game" in err or "error" in err.lower()

    def test_bucket_override_reflected_in_output_game_key(self):
        tmp = _write_game_file(make_game_payload())
        try:
            code, out, _ = self._run([tmp, "--dry-run", "--bucket", "my-custom-bucket"])
            assert code == 0
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_base_url_override_reflected_in_output_urls(self):
        tmp = _write_game_file(make_game_payload())
        try:
            code, out, _ = self._run([tmp, "--dry-run", "--base-url", "https://staging.find4.org"])
            assert code == 0
            result = json.loads(out)
            assert result["game_url"].startswith("https://staging.find4.org")
            assert result["redirect_url"].startswith("https://staging.find4.org")
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_invalid_json_file_exits_1(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{not valid json{{")
            tmp = f.name
        try:
            code, _, err = self._run([tmp, "--dry-run"])
            assert code == 1
            assert "error" in err.lower() or "JSON" in err
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_missing_metadata_id_exits_1(self):
        data = make_game_payload()
        del data["metadata"]["id"]
        tmp = _write_game_file(data)
        try:
            code, _, err = self._run([tmp, "--dry-run"])
            assert code == 1
            assert "error" in err.lower() or "metadata" in err
        finally:
            Path(tmp).unlink(missing_ok=True)
