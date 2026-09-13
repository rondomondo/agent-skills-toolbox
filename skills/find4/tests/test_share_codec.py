"""Tests for the v2 share URL codec (compact positional encoding)."""

import base64
import json
import zlib
from typing import Any

import pytest

SHARE_SCHEMA = ["words", "category", "color", "group_item_id", "group_set_id"]


def compact(data: dict[str, Any]) -> dict[str, Any]:
    """Encode a full game dict into the v2 wire format."""
    return {
        "v": 2,
        "game_sets": [
            {
                "theme": gs["theme"],
                "game_set_id": gs["game_set_id"],
                "group_sets": [
                    [[item.get(k) for k in SHARE_SCHEMA] for item in group_set]
                    for group_set in gs["group_sets"]
                ],
            }
            for gs in data["game_sets"]
        ],
    }


def expand(compact_data: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct a full game dict from v2 wire format."""
    return {
        "game_sets": [
            {
                "theme": gs["theme"],
                "game_set_id": gs["game_set_id"],
                "group_sets": [
                    [dict(zip(SHARE_SCHEMA, row)) for row in group_set]
                    for group_set in gs["group_sets"]
                ],
            }
            for gs in compact_data["game_sets"]
        ],
    }


def encode_url_payload(data: dict[str, Any]) -> str:
    payload = json.dumps(compact(data), separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(zlib.compress(payload, level=9)).decode()


def decode_url_payload(b64: str) -> dict[str, Any]:
    raw = zlib.decompress(base64.urlsafe_b64decode(b64))
    parsed = json.loads(raw)
    assert parsed.get("v") == 2
    return expand(parsed)


# Fixtures

def make_group_item(
    words: list[str] | None = None,
    category: str = "Test Cat",
    color: str = "red",
    group_item_id: str = "aabbcc",
    group_set_id: str = "ddeeff",
    **extra: Any,
) -> dict[str, Any]:
    return {
        "words": words or ["Alpha", "Beta", "Gamma", "Delta"],
        "category": category,
        "color": color,
        "group_item_id": group_item_id,
        "group_set_id": group_set_id,
        "url": "https://example.com",
        "description": "A test group",
        "skill_level": "Beginner",
        "additional_sources": ["https://example.com/extra"],
        **extra,
    }


def make_game(n_group_sets: int = 1) -> dict[str, Any]:
    colors = ["red", "blue", "green", "yellow"]
    return {
        "game_sets": [
            {
                "theme": "Test Theme",
                "game_set_id": "gs001",
                "group_sets": [
                    [
                        make_group_item(color=colors[i], category=f"Cat {i}", group_item_id=f"item{j}{i}")
                        for i in range(4)
                    ]
                    for j in range(n_group_sets)
                ],
            }
        ]
    }


# compact()

class TestCompact:
    def test_version_field_is_2(self):
        result = compact(make_game())
        assert result["v"] == 2

    def test_preserves_theme_and_game_set_id(self):
        data = make_game()
        result = compact(data)
        assert result["game_sets"][0]["theme"] == "Test Theme"
        assert result["game_sets"][0]["game_set_id"] == "gs001"

    def test_group_items_are_arrays(self):
        result = compact(make_game())
        row = result["game_sets"][0]["group_sets"][0][0]
        assert isinstance(row, list)

    def test_row_length_matches_schema(self):
        result = compact(make_game())
        row = result["game_sets"][0]["group_sets"][0][0]
        assert len(row) == len(SHARE_SCHEMA)

    def test_words_is_first_element(self):
        data = make_game()
        result = compact(data)
        row = result["game_sets"][0]["group_sets"][0][0]
        assert row[0] == data["game_sets"][0]["group_sets"][0][0]["words"]

    def test_strips_non_schema_keys(self):
        result = compact(make_game())
        row = result["game_sets"][0]["group_sets"][0][0]
        # row is a list so no key access, but we verify no extra elements
        assert len(row) == len(SHARE_SCHEMA)

    def test_multiple_group_sets(self):
        data = make_game(n_group_sets=3)
        result = compact(data)
        assert len(result["game_sets"][0]["group_sets"]) == 3

    def test_missing_optional_field_becomes_none(self):
        data = make_game()
        del data["game_sets"][0]["group_sets"][0][0]["group_item_id"]
        result = compact(data)
        row = result["game_sets"][0]["group_sets"][0][0]
        idx = SHARE_SCHEMA.index("group_item_id")
        assert row[idx] is None


# expand()

class TestExpand:
    def test_produces_game_sets_key(self):
        result = expand(compact(make_game()))
        assert "game_sets" in result

    def test_items_are_dicts(self):
        result = expand(compact(make_game()))
        item = result["game_sets"][0]["group_sets"][0][0]
        assert isinstance(item, dict)

    def test_all_schema_keys_present(self):
        result = expand(compact(make_game()))
        item = result["game_sets"][0]["group_sets"][0][0]
        for key in SHARE_SCHEMA:
            assert key in item

    def test_no_extra_keys_beyond_schema_and_game_set_fields(self):
        result = expand(compact(make_game()))
        item = result["game_sets"][0]["group_sets"][0][0]
        assert set(item.keys()) == set(SHARE_SCHEMA)


# Round-trip

class TestRoundTrip:
    def test_words_survive_round_trip(self):
        data = make_game()
        original = data["game_sets"][0]["group_sets"][0][0]["words"]
        recovered = decode_url_payload(encode_url_payload(data))
        assert recovered["game_sets"][0]["group_sets"][0][0]["words"] == original

    def test_category_survives_round_trip(self):
        data = make_game()
        original = data["game_sets"][0]["group_sets"][0][0]["category"]
        recovered = decode_url_payload(encode_url_payload(data))
        assert recovered["game_sets"][0]["group_sets"][0][0]["category"] == original

    def test_color_survives_round_trip(self):
        data = make_game()
        original = data["game_sets"][0]["group_sets"][0][0]["color"]
        recovered = decode_url_payload(encode_url_payload(data))
        assert recovered["game_sets"][0]["group_sets"][0][0]["color"] == original

    def test_ids_survive_round_trip(self):
        data = make_game()
        item = data["game_sets"][0]["group_sets"][0][0]
        recovered = decode_url_payload(encode_url_payload(data))
        rt_item = recovered["game_sets"][0]["group_sets"][0][0]
        assert rt_item["group_item_id"] == item["group_item_id"]
        assert rt_item["group_set_id"] == item["group_set_id"]

    def test_non_schema_fields_not_present_after_round_trip(self):
        data = make_game()
        recovered = decode_url_payload(encode_url_payload(data))
        item = recovered["game_sets"][0]["group_sets"][0][0]
        assert "url" not in item
        assert "description" not in item
        assert "skill_level" not in item
        assert "additional_sources" not in item

    def test_multiple_game_sets_round_trip(self):
        data = {
            "game_sets": [
                {
                    "theme": f"Theme {n}",
                    "game_set_id": f"gs00{n}",
                    "group_sets": [
                        [make_group_item(category=f"Cat {i}", color=c, group_item_id=f"i{n}{i}")
                         for i, c in enumerate(["red", "blue", "green", "yellow"])]
                    ],
                }
                for n in range(3)
            ]
        }
        recovered = decode_url_payload(encode_url_payload(data))
        assert len(recovered["game_sets"]) == 3
        for n in range(3):
            assert recovered["game_sets"][n]["theme"] == f"Theme {n}"

    def test_multiple_group_sets_round_trip(self):
        data = make_game(n_group_sets=4)
        recovered = decode_url_payload(encode_url_payload(data))
        assert len(recovered["game_sets"][0]["group_sets"]) == 4

    def test_words_with_spaces_round_trip(self):
        data = make_game()
        data["game_sets"][0]["group_sets"][0][0]["words"] = ["WAVE SPEED", "TOTAL INTERNAL REFLECTION", "OHM'S LAW", "HALF-LIFE"]
        recovered = decode_url_payload(encode_url_payload(data))
        assert recovered["game_sets"][0]["group_sets"][0][0]["words"] == ["WAVE SPEED", "TOTAL INTERNAL REFLECTION", "OHM'S LAW", "HALF-LIFE"]


# Payload size

class TestPayloadSize:
    def test_v2_smaller_than_v1_for_typical_game(self):
        data = make_game(n_group_sets=2)
        v1 = base64.urlsafe_b64encode(zlib.compress(json.dumps(data, separators=(",", ":")).encode())).decode()
        v2 = encode_url_payload(data)
        assert len(v2) < len(v1)

    def test_v2_marker_present_in_decoded_payload(self):
        data = make_game()
        b64 = encode_url_payload(data)
        raw = zlib.decompress(base64.urlsafe_b64decode(b64))
        parsed = json.loads(raw)
        assert parsed["v"] == 2
