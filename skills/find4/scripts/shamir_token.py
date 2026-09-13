#!/usr/bin/env -S uv run python3
"""Split and reconstruct a secret using Shamir 2-of-3 secret sharing.

Each share is encoded as a numbered 12-word BIP-39 mnemonic phrase.
The secret itself is AES-128-EAX encrypted; only the key is split.
"""

import argparse
import base64
import getpass
import json
import os
import sys
from typing import Any

try:
    from mnemonic import Mnemonic
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    from Crypto.Protocol.SecretSharing import Shamir
except ImportError as exc:
    print(f"Missing dependency: {exc}. Run: pip install mnemonic pycryptodome", file=sys.stderr)
    sys.exit(1)

# ANSI colour codes
_RED = "\033[0;31m"
_GREEN = "\033[0;32m"
_YELLOW = "\033[0;33m"
_CYAN = "\033[0;36m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _init_colours() -> None:
    global _RED, _GREEN, _YELLOW, _CYAN, _BOLD, _RESET
    if os.environ.get("NO_COLOR") or not sys.stderr.isatty():
        _RED = _GREEN = _YELLOW = _CYAN = _BOLD = _RESET = ""


_init_colours()

_MN = Mnemonic("english")

SHARE_COUNT = 3
THRESHOLD = 2
KEY_BYTES = 16


# Helpers

def _ok(msg: str) -> None:
    print(f"{_GREEN}ok{_RESET}  {msg}", file=sys.stderr)


def _warn(msg: str) -> None:
    print(f"{_YELLOW}warn{_RESET} {msg}", file=sys.stderr)


def _fail(msg: str) -> None:
    print(f"{_RED}fail{_RESET} {msg}", file=sys.stderr)


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s.encode())


def _share_to_words(idx: int, share_bytes: bytes) -> str:
    """Encode a Shamir share as a prefixed 12-word mnemonic.

    Args:
        idx: 1-based share index (1-3).
        share_bytes: raw share bytes (16 bytes).

    Returns:
        String of the form "<idx> word1 word2 ... word12".
    """
    payload = bytearray(share_bytes)
    payload[0] ^= idx
    payload[-1] ^= (idx << 4)
    return f"{idx} " + _MN.to_mnemonic(bytes(payload))


def _words_to_share(wordline: str) -> tuple[int, bytes]:
    """Decode a prefixed mnemonic back to (index, share_bytes).

    Args:
        wordline: string of the form "<idx> word1 ... word12".

    Returns:
        Tuple of (share index, raw share bytes).

    Raises:
        ValueError: if the format or entropy length is invalid.
    """
    parts = wordline.strip().split(" ", 1)
    if len(parts) != 2:
        raise ValueError("expected format: <index> word1 word2 ... word12")
    idx = int(parts[0])
    if idx < 1 or idx > SHARE_COUNT:
        raise ValueError(f"share index must be 1-{SHARE_COUNT}, got {idx}")
    raw = bytearray(_MN.to_entropy(parts[1]))
    if len(raw) != KEY_BYTES:
        raise ValueError(f"decoded entropy is {len(raw)} bytes, expected {KEY_BYTES}")
    raw[0] ^= idx
    raw[-1] ^= (idx << 4)
    return idx, bytes(raw)


def _encrypt_secret(secret: str) -> tuple[bytes, dict[str, Any]]:
    """Encrypt a secret with a fresh AES-128-EAX key.

    Args:
        secret: plaintext secret string.

    Returns:
        Tuple of (aes_key, payload_dict) where payload_dict holds
        base64-encoded nonce, tag, and ciphertext.
    """
    aes_key = get_random_bytes(KEY_BYTES)
    cipher = AES.new(aes_key, AES.MODE_EAX)
    ct = cipher.encrypt(secret.encode("utf-8"))
    tag = cipher.digest()
    payload: dict[str, Any] = {
        "nonce": _b64(cipher.nonce),
        "tag": _b64(tag),
        "ct": _b64(ct),
    }
    return aes_key, payload


def _decrypt_payload(aes_key: bytes, payload: dict[str, Any]) -> str:
    """Decrypt an AES-128-EAX payload.

    Args:
        aes_key: the reconstructed 16-byte AES key.
        payload: dict with base64-encoded nonce, tag, and ct fields.

    Returns:
        The original plaintext secret.

    Raises:
        ValueError: if authentication fails (wrong key or tampered payload).
    """
    nonce = _unb64(payload["nonce"])
    tag = _unb64(payload["tag"])
    ct = _unb64(payload["ct"])
    cipher = AES.new(aes_key, AES.MODE_EAX, nonce=nonce)
    plaintext = cipher.decrypt(ct)
    cipher.verify(tag)
    return plaintext.decode("utf-8")


# Commands

def cmd_split(args: argparse.Namespace) -> int:
    """Run the split command.

    Args:
        args: parsed CLI arguments.

    Returns:
        Exit code (0 on success, 1 on failure).
    """
    if args.secret:
        secret = args.secret
        _warn("secret passed via --secret flag is visible in process lists and shell history")
    else:
        secret = getpass.getpass("Secret (hidden input): ").strip()

    if not secret:
        _fail("no secret provided")
        return 1

    aes_key, payload = _encrypt_secret(secret)
    payload_b64 = _b64(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    shares = Shamir.split(THRESHOLD, SHARE_COUNT, aes_key)

    _ok(f"secret encrypted and split into {SHARE_COUNT} shares (any {THRESHOLD} reconstruct it)")
    print()

    names = ["Person A", "Person B", "Person C"]
    for i, (idx, share_bytes) in enumerate(shares):
        words = _share_to_words(idx, share_bytes)
        word_list = words.split(" ")
        index_num = word_list[0]
        phrase = word_list[1:]

        print(f"{_BOLD}Share {index_num} — {names[i]} (keep secret, do not share){_RESET}")
        for n, word in enumerate(phrase, 1):
            print(f"  {_CYAN}{n:2}.{_RESET} {word}")
        print()

    print(f"{_BOLD}Payload{_RESET} (safe to store anywhere; useless without {THRESHOLD} shares)")
    print(f"  {payload_b64}")
    print()
    _warn("the original secret is not stored anywhere — save the shares and payload now")
    return 0


def cmd_combine(args: argparse.Namespace) -> int:
    """Run the combine command.

    Args:
        args: parsed CLI arguments.

    Returns:
        Exit code (0 on success, 1 on failure).
    """
    collected: list[tuple[int, bytes]] = []

    if args.shares:
        for raw in args.shares:
            try:
                collected.append(_words_to_share(raw))
            except (ValueError, KeyError) as e:
                _fail(f"could not parse share: {e}")
                return 1
    else:
        print(f"Enter {THRESHOLD} of {SHARE_COUNT} share phrases.")
        print(f"Format: {_YELLOW}<share#>{_RESET} word1 word2 ... word12")
        print()
        for i in range(1, SHARE_COUNT + 1):
            raw = input(f"  Phrase {i} (Enter to skip): ").strip()
            if raw:
                try:
                    collected.append(_words_to_share(raw))
                except (ValueError, KeyError) as e:
                    _fail(f"could not parse phrase: {e}")
                    return 1
            if len(collected) == THRESHOLD:
                if i < SHARE_COUNT:
                    print(f"  ({THRESHOLD} phrases collected, skipping rest)")
                break

    if len(collected) < THRESHOLD:
        _fail(f"need at least {THRESHOLD} shares, got {len(collected)}")
        return 1

    payload_b64 = args.payload or input("\n  Payload: ").strip()
    if not payload_b64:
        _fail("no payload provided")
        return 1

    try:
        payload: dict[str, Any] = json.loads(_unb64(payload_b64).decode("utf-8"))
    except (ValueError, KeyError) as e:
        _fail(f"invalid payload: {e}")
        return 1

    try:
        aes_key = Shamir.combine(collected)
    except (ValueError, KeyError) as e:
        _fail(f"share combination failed: {e}")
        return 1

    try:
        secret = _decrypt_payload(aes_key, payload)
    except ValueError:
        _fail("authentication failed — wrong shares or tampered payload")
        return 1
    except (KeyError, UnicodeDecodeError) as e:
        _fail(f"decryption error: {e}")
        return 1

    _ok("secret reconstructed successfully")
    print()
    print(f"{_BOLD}Secret:{_RESET} {secret}")
    print()
    return 0


# CLI

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shamir_token.py",
        description="Split or reconstruct a secret using Shamir 2-of-3 secret sharing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  shamir_token.py split\n"
            "  shamir_token.py split --secret ghp_abc123\n"
            "  shamir_token.py combine\n"
            "  shamir_token.py combine \\\n"
            '    --share "1 word1 word2 ... word12" \\\n'
            '    --share "3 word1 word2 ... word12" \\\n'
            "    --payload eyJub25jZSI6...\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    sp = sub.add_parser("split", help=f"encrypt a secret and split it into {SHARE_COUNT} mnemonic shares")
    sp.add_argument(
        "--secret",
        metavar="TEXT",
        help="secret to split (omit for secure hidden-input prompt)",
    )

    cp = sub.add_parser(
        "combine",
        help=f"reconstruct the secret from any {THRESHOLD} of {SHARE_COUNT} mnemonic shares",
    )
    cp.add_argument(
        "--share",
        dest="shares",
        metavar="PHRASE",
        action="append",
        help=f'share phrase, format: "<index> word1 ... word12" (repeat up to {THRESHOLD} times)',
    )
    cp.add_argument(
        "--payload",
        metavar="B64",
        help="base64-encoded payload blob printed during split",
    )

    return parser


def main() -> None:
    """Entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "split":
        sys.exit(cmd_split(args))
    else:
        sys.exit(cmd_combine(args))


if __name__ == "__main__":
    main()
