#!/usr/bin/env -S uv run python3
"""Publish a find4 game JSON file to S3 with a short-code redirect."""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import boto3
from aiobotocore.session import get_session
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

SHORT_CODE_LENGTH = 8
BUCKET = "find4-webapp"
REGION = "us-east-1"
GAMES_PREFIX = "games"
REDIRECT_PREFIX = "g"
BASE_URL = os.getenv("FIND4_BASE_URL", "https://find4.org")


def gen_short_code(data: str, length: int = SHORT_CODE_LENGTH) -> str:
    """Generate a deterministic URL-safe short code from input data.

    Uses SHA-256 + base62 encoding, truncated to 'length' characters.
    Deterministic: same input always produces the same code.

    Args:
        data: The string to derive the short code from.
        length: Number of characters to return.

    Returns:
        A URL-safe alphanumeric string of exactly 'length' characters.
    """
    ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    digest = hashlib.sha256(data.encode("utf-8")).digest()
    number = int.from_bytes(digest, "big")
    encoded = ""
    base = len(ALPHABET)
    while number and len(encoded) < length:
        number, remainder = divmod(number, base)
        encoded = ALPHABET[remainder] + encoded
    return encoded.ljust(length, "0")[:length]


def _redirect_metadata(target_url: str) -> dict[str, Any]:
    """Build S3 put_object kwargs for an HTTP redirect object.

    Args:
        target_url: The redirect destination URL.

    Returns:
        Dict with WebsiteRedirectLocation key suitable for put_object.

    Raises:
        ValueError: If target_url does not start with http:// or https://.
    """
    if not target_url.lower().startswith(("http://", "https://")):
        raise ValueError(f"target_url must be http/https, got: {target_url!r}")
    return {"WebsiteRedirectLocation": target_url}


async def _put_object(
    client: Any,
    bucket: str,
    key: str,
    body: bytes,
    content_type: str,
    extra: dict[str, Any] | None = None,
) -> None:
    """Upload a single object to S3.

    Args:
        client: aiobotocore S3 client.
        bucket: Target bucket name.
        key: Destination key.
        body: Object body bytes.
        content_type: MIME type string.
        extra: Additional kwargs merged into put_object call.
    """
    kwargs: dict[str, Any] = {
        "Bucket": bucket,
        "Key": key,
        "Body": body,
        "ContentType": content_type,
    }
    if extra:
        kwargs.update(extra)
    await client.put_object(**kwargs)
    logger.info("  put s3://%s/%s", bucket, key)


async def publish(game_path: Path, dry_run: bool = False) -> dict[str, str]:
    """Read a game JSON file and publish it plus a short-code redirect to S3.

    Writes two objects to S3:
    - games/<short_code>.json   - the game payload
    - g/<short_code>            - empty redirect object -> game URL on find4.org

    Args:
        game_path: Path to the game JSON file.
        dry_run: When True, log what would be uploaded without hitting S3.

    Returns:
        Dict with keys: short_code, game_key, redirect_key, game_url, redirect_url.

    Raises:
        ValueError: If the JSON file is invalid or missing required fields.
        ClientError: On S3 errors.
    """
    raw = game_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {game_path}: {exc}") from exc

    metadata = payload.get("metadata") or {}
    game_id: str | None = metadata.get("id")
    if not game_id:
        raise ValueError(f"{game_path} must contain a 'metadata.id' field")

    short_code = gen_short_code(game_id)
    game_key = f"{GAMES_PREFIX}/{short_code}.json"
    redirect_key = f"{REDIRECT_PREFIX}/{short_code}"
    game_url = f"{BASE_URL}/{game_key}"
    redirect_url = f"{BASE_URL}/{redirect_key}"

    logger.info("game_id:      %s", game_id)
    logger.info("short_code:   %s", short_code)
    logger.info("game_key:     s3://%s/%s", BUCKET, game_key)
    logger.info("redirect_key: s3://%s/%s -> %s", BUCKET, redirect_key, game_url)

    if dry_run:
        logger.info("dry-run: skipping S3 uploads")
        return {
            "short_code": short_code,
            "game_key": game_key,
            "redirect_key": redirect_key,
            "game_url": game_url,
            "redirect_url": redirect_url,
        }

    region = os.getenv("AWS_DEFAULT_REGION", REGION)
    session = get_session()
    async with session.create_client("s3", region_name=region) as client:
        await _put_object(
            client, BUCKET, game_key,
            body=raw.encode("utf-8"),
            content_type="application/json",
        )
        await _put_object(
            client, BUCKET, redirect_key,
            body=b"",
            content_type="application/octet-stream",
            extra=_redirect_metadata(game_url),
        )

    return {
        "short_code": short_code,
        "game_key": game_key,
        "redirect_key": redirect_key,
        "game_url": game_url,
        "redirect_url": redirect_url,
    }


def main() -> None:
    """Entry point for publishing find4 game JSON files to S3."""
    global BUCKET, BASE_URL
    parser = argparse.ArgumentParser(
        description="Publish a find4 game JSON file to S3 with a short-code redirect.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("game_file", type=Path, help="path to the game JSON file")
    parser.add_argument(
        "--bucket", default=BUCKET,
        help="target S3 bucket",
    )
    parser.add_argument(
        "--base-url", default=BASE_URL,
        help="base URL for the game site (also settable via FIND4_BASE_URL env var)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="log what would be uploaded without writing to S3",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
    )

    if not args.game_file.is_file():
        print(f"error: file not found: {args.game_file}", file=sys.stderr)
        sys.exit(1)

    BUCKET = args.bucket
    BASE_URL = args.base_url

    try:
        result = asyncio.run(publish(args.game_file, dry_run=args.dry_run))
    except (ValueError, ClientError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
