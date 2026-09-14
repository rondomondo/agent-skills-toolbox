"""Tests for finalize_metadata.py."""

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from finalize_metadata import finalize_metadata, generate_url_safe_hash


# Helpers

def make_group(color: str = "red", category: str = "Test") -> Dict[str, Any]:
    return {
        "category": category,
        "words": ["a", "b", "c", "d"],
        "color": color,
        "description": "desc",
        "skill_level": "Beginner",
    }


def make_minimal_data(source: str = "test-source") -> Dict[str, Any]:
    return {
        "metadata": {
            "generated_at": "2024-01-01T00:00:00+00:00",
            "source": source,
        },
        "game_sets": [
            {
                "theme": "Test Theme",
                "game_set_id": "abcdef012345",
                "group_sets": [[make_group()]],
            }
        ],
        "id_registry": {
            "game_set_ids": ["abcdef012345"],
            "group_set_ids": ["aabbcc"],
            "group_item_ids": ["112233"],
        },
    }


# finalize_metadata — basic behaviour

class TestFinalizeMetadataBasic:
    def test_returns_dict(self):
        data = make_minimal_data()
        result = finalize_metadata(data, "src")
        assert isinstance(result, dict)

    def test_sets_source_id(self):
        data = make_minimal_data()
        result = finalize_metadata(data, "https://example.com/article")
        assert result["metadata"]["source_id"] == "https://example.com/article"

    def test_sets_step(self):
        data = make_minimal_data()
        result = finalize_metadata(data, "src")
        assert result["metadata"]["step"] == "finalize_metadata"

    def test_sets_modified_at(self):
        data = make_minimal_data()
        result = finalize_metadata(data, "src")
        assert "modified_at" in result["metadata"]
        assert isinstance(result["metadata"]["modified_at"], str)
        assert "T" in result["metadata"]["modified_at"]

    def test_raises_when_metadata_missing(self):
        data = {"game_sets": []}
        with pytest.raises(RuntimeError, match="metadata"):
            finalize_metadata(data, "src")

    def test_does_not_mutate_original(self):
        data = make_minimal_data()
        original = copy.deepcopy(data)
        finalize_metadata(data, "src")
        assert data == original


# id_registry promotion

class TestIdRegistryPromotion:
    def test_id_registry_moved_into_metadata(self):
        data = make_minimal_data()
        result = finalize_metadata(data, "src")
        assert "id_registry" in result["metadata"]

    def test_id_registry_removed_from_root(self):
        data = make_minimal_data()
        result = finalize_metadata(data, "src")
        assert "id_registry" not in result

    def test_id_registry_content_preserved(self):
        data = make_minimal_data()
        original_registry = copy.deepcopy(data["id_registry"])
        result = finalize_metadata(data, "src")
        assert result["metadata"]["id_registry"] == original_registry

    def test_no_id_registry_at_root_is_safe(self):
        data = make_minimal_data()
        del data["id_registry"]
        result = finalize_metadata(data, "src")
        assert "id_registry" not in result


# Promoted flag cleanup

class TestPromotedFlagCleanup:
    def test_removes_promoted_flag_if_present(self):
        data = make_minimal_data()
        data["metadata"]["promoted"] = True
        result = finalize_metadata(data, "src")
        assert "promoted" not in result["metadata"]

    def test_no_error_when_promoted_absent(self):
        data = make_minimal_data()
        result = finalize_metadata(data, "src")
        assert "promoted" not in result["metadata"]


# Fingerprint (metadata.id)

class TestFingerprintId:
    def test_id_added_to_metadata(self):
        data = make_minimal_data()
        result = finalize_metadata(data, "src")
        assert "id" in result["metadata"]

    def test_id_is_string(self):
        data = make_minimal_data()
        result = finalize_metadata(data, "src")
        assert isinstance(result["metadata"]["id"], str)

    def test_id_is_16_chars_by_default(self):
        data = make_minimal_data()
        result = finalize_metadata(data, "src")
        assert len(result["metadata"]["id"]) == 16

    def test_id_is_url_safe(self):
        data = make_minimal_data()
        result = finalize_metadata(data, "src")
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        assert all(c in allowed for c in result["metadata"]["id"])

    def test_different_source_produces_different_id(self):
        d1 = make_minimal_data()
        d2 = make_minimal_data()
        r1 = finalize_metadata(d1, "source-a")
        r2 = finalize_metadata(d2, "source-b")
        assert r1["metadata"]["id"] != r2["metadata"]["id"]

    def test_different_game_content_produces_different_id(self):
        d1 = make_minimal_data()
        d2 = make_minimal_data()
        d2["game_sets"][0]["theme"] = "Completely Different"
        r1 = finalize_metadata(d1, "src")
        r2 = finalize_metadata(d2, "src")
        assert r1["metadata"]["id"] != r2["metadata"]["id"]


# Existing metadata fields are not overwritten except the explicit ones

class TestMetadataPreservation:
    def test_generated_at_preserved(self):
        data = make_minimal_data()
        data["metadata"]["generated_at"] = "2020-06-15T12:00:00+00:00"
        result = finalize_metadata(data, "src")
        assert result["metadata"]["generated_at"] == "2020-06-15T12:00:00+00:00"

    def test_custom_metadata_field_preserved(self):
        data = make_minimal_data()
        data["metadata"]["custom_key"] = "keep_me"
        result = finalize_metadata(data, "src")
        assert result["metadata"]["custom_key"] == "keep_me"


# generate_url_safe_hash

class TestGenerateUrlSafeHash:
    def test_returns_string(self):
        assert isinstance(generate_url_safe_hash("hello"), str)

    def test_default_length_16(self):
        assert len(generate_url_safe_hash("hello")) == 16

    def test_custom_length_8(self):
        assert len(generate_url_safe_hash("hello", length=8)) == 8

    def test_custom_length_22(self):
        assert len(generate_url_safe_hash("hello", length=22)) == 22

    def test_url_safe_characters_only(self):
        h = generate_url_safe_hash({"key": "value"})
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        assert all(c in allowed for c in h)

    def test_same_input_same_hash(self):
        assert generate_url_safe_hash("input") == generate_url_safe_hash("input")

    def test_different_inputs_different_hashes(self):
        assert generate_url_safe_hash("aaa") != generate_url_safe_hash("bbb")

    def test_accepts_dict(self):
        h = generate_url_safe_hash({"a": 1, "b": 2})
        assert isinstance(h, str)
        assert len(h) == 16

    def test_accepts_bytes(self):
        h = generate_url_safe_hash(b"raw bytes")
        assert isinstance(h, str)

    def test_dict_is_order_stable(self):
        h1 = generate_url_safe_hash({"b": 2, "a": 1})
        h2 = generate_url_safe_hash({"a": 1, "b": 2})
        assert h1 == h2
