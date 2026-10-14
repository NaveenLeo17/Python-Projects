"""Duplicate file detection via content hashing (SHA-256)."""

import hashlib
import os
from typing import Dict, List


def _hash_file(path: str, chunk_size: int = 65536) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _iter_files(directory: str, recursive: bool):
    if recursive:
        for root, _dirs, files in os.walk(directory):
            for name in files:
                yield os.path.join(root, name)
    else:
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                yield path


def find_duplicates(directory: str, recursive: bool = True) -> Dict[str, List[str]]:
    """Group files by content hash. Only groups with 2+ files (real duplicates)
    are returned, keyed by the shared hash."""
    by_size: Dict[int, List[str]] = {}
    for path in _iter_files(directory, recursive):
        try:
            size = os.path.getsize(path)
        except OSError:
            continue
        by_size.setdefault(size, []).append(path)

    # Only hash files that share a size with at least one other file —
    # avoids hashing every file when most sizes are unique.
    by_hash: Dict[str, List[str]] = {}
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        for path in paths:
            try:
                file_hash = _hash_file(path)
            except OSError:
                continue
            by_hash.setdefault(file_hash, []).append(path)

    return {h: paths for h, paths in by_hash.items() if len(paths) > 1}
