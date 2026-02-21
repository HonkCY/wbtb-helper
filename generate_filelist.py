#!/usr/bin/env python3
"""
generate_filelist.py — Scan /audio for MP3s, rename to SHA-256 hashes, emit filelist.json.

Usage:
    cd /path/to/wbtb
    python3 generate_filelist.py

This script:
  1. Reads every .mp3 in ./audio/
  2. Renames each file to the first 12 hex chars of its SHA-256 content hash
     (idempotent — already-hashed names are left untouched)
  3. Writes filelist.json to the project root
"""

import hashlib
import json
import os
import sys
from pathlib import Path

AUDIO_DIR = Path(__file__).resolve().parent / "audio"
OUTPUT_FILE = Path(__file__).resolve().parent / "filelist.json"
HASH_LEN = 12  # hex chars → 6 bytes → 16^12 ≈ 281 trillion combinations


def sha256_of_file(path: Path) -> str:
    """Return the hex SHA-256 digest of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_already_hashed(name: str) -> bool:
    """Check if a filename already looks like a hash (hex chars + .mp3)."""
    stem = Path(name).stem
    return len(stem) == HASH_LEN and all(c in "0123456789abcdef" for c in stem)


def main():
    if not AUDIO_DIR.is_dir():
        print(f"❌ Audio directory not found: {AUDIO_DIR}", file=sys.stderr)
        sys.exit(1)

    mp3_files = sorted(AUDIO_DIR.glob("*.mp3"))
    if not mp3_files:
        print("⚠️  No .mp3 files found in audio/", file=sys.stderr)
        sys.exit(1)

    print(f"📂 Found {len(mp3_files)} MP3 file(s) in {AUDIO_DIR}")

    filenames = []
    renamed_count = 0

    for mp3 in mp3_files:
        if is_already_hashed(mp3.name):
            # Already processed — keep as-is
            filenames.append(mp3.name)
            continue

        content_hash = sha256_of_file(mp3)[:HASH_LEN]
        new_name = f"{content_hash}.mp3"
        new_path = AUDIO_DIR / new_name

        # Handle (extremely rare) hash collision
        if new_path.exists() and new_path != mp3:
            # Extend hash to disambiguate
            full_hash = sha256_of_file(mp3)
            new_name = f"{full_hash[:HASH_LEN + 4]}.mp3"
            new_path = AUDIO_DIR / new_name

        mp3.rename(new_path)
        renamed_count += 1
        filenames.append(new_name)

    # Sort for deterministic output
    filenames.sort()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(filenames, f, indent=2)

    print(f"✅ Renamed {renamed_count} file(s)")
    print(f"✅ Wrote {len(filenames)} entries to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
