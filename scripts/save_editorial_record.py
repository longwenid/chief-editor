#!/usr/bin/env python3
"""Validate then append one Markdown/JSON editorial record to an explicit memory root.

No default memory, engine access, authorization edits, or old-status updates. Related
evidence is read only when explicitly supplied. Existing legacy Markdown without a
JSON fence is left untouched. Requires POSIX dir_fd, O_NOFOLLOW, and flock (tested
on the current Mac); unsupported platforms fail closed, and cross-platform use is
unverified. Every memory-root component must be a physical directory, not a symlink.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
from datetime import datetime, timezone

try:
    import fcntl
except ImportError:
    fcntl = None

TYPES = {"market_snapshot": "market", "taste_comparison": "teardowns",
         "selection_decision": "decisions", "postmortem": "postmortems"}
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}\Z")
JSON_FENCE = re.compile(r"^[ ]{0,3}```json(?:[ \t]|$)", re.M | re.I)
MAX_BYTES = 1024 * 1024


def _validator():
    path = Path(__file__).with_name("check_editorial_evidence.py")
    spec = importlib.util.spec_from_file_location("_editorial_save_validator", path)
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


evidence = _validator()


def _backend():
    if (fcntl is None or not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY")
            or not {os.open, os.mkdir, os.unlink} <= os.supports_dir_fd
            or os.listdir not in os.supports_fd):
        raise ValueError("unsupported: safe saving requires POSIX dir_fd/O_NOFOLLOW/flock")


def _directory(parent, name, *, create=False):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        return os.open(name, flags, dir_fd=parent)
    except FileNotFoundError:
        if not create:
            raise
        try:
            os.mkdir(name, 0o700, dir_fd=parent)
        except FileExistsError:
            pass
        return os.open(name, flags, dir_fd=parent)


def _root_fd(path):
    descriptor = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in path.parts[1:]:
            child = _directory(descriptor, component, create=True)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _existing_identity(parent, name):
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
            raise ValueError("not a bounded regular memory record: " + name)
        chunks, remaining = [], MAX_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(remaining, 65536))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > MAX_BYTES:
            raise ValueError("memory record exceeds 1 MiB: " + name)
        content = raw.decode("utf-8")
        if not JSON_FENCE.search(content):
            return None  # Legacy Markdown is neither migrated nor given an invented ID.
        record = evidence.parse_record(content, markdown=True)
        identity = record.get("record_id")
        if not isinstance(identity, str) or not identity:
            raise ValueError("corrupt JSON evidence record_id: " + name)
        return identity
    finally:
        os.close(descriptor)


def _reject_duplicate(root, identity):
    for folder in TYPES.values():
        try:
            descriptor = _directory(root, folder)
        except FileNotFoundError:
            continue
        try:
            for name in os.listdir(descriptor):
                if name.lower().endswith(".md"):
                    existing = _existing_identity(descriptor, name)
                    if existing is not None and existing.casefold() == identity.casefold():
                        raise FileExistsError("record_id already exists: " + identity)
        finally:
            os.close(descriptor)


def save_record(record, memory_root, *, evidence_records=(), now=None):
    """Save only this new record; explicit dependency records are validated, never saved."""
    # Freeze caller-owned objects and reject non-JSON/NaN before any mkdir or open-for-write.
    snapshot = json.loads(json.dumps(record, ensure_ascii=False, allow_nan=False))
    related = json.loads(json.dumps(list(evidence_records), ensure_ascii=False, allow_nan=False))
    problems = evidence.validate_records([*related, snapshot])
    if problems:
        raise ValueError("invalid editorial evidence: " + "; ".join(problems))
    identity, kind = snapshot["record_id"], snapshot["record_type"]
    if not SAFE_ID.fullmatch(identity):
        raise ValueError("record_id must be 1-96 ASCII letters/digits/_/-; no paths or dots")
    root = Path(memory_root)
    if not root.is_absolute() or ".." in root.parts or "\0" in str(root) or root == Path(root.anchor):
        raise ValueError("memory-root must be an explicit absolute non-root path without '..'")
    moment = now if now is not None else datetime.now(timezone.utc)
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("save time must include a timezone")
    moment = moment.astimezone(timezone.utc)
    prefix = moment.strftime("%Y-%m-%d-%H%M%S%f-") if kind == "market_snapshot" else (
        "" if kind == "taste_comparison" else moment.strftime("%Y-%m-%d-"))
    name = prefix + identity + ".md"
    payload = ("```json\n" + json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n```\n").encode("utf-8")
    if len(payload) > MAX_BYTES:
        raise ValueError("record exceeds 1 MiB; do not save prose")
    _backend()
    root_descriptor = _root_fd(root)
    folder_descriptor = None
    try:
        # All invocations of this helper use the same directory inode lock; no extra index/view.
        fcntl.flock(root_descriptor, fcntl.LOCK_EX)
        _reject_duplicate(root_descriptor, identity)
        folder_descriptor = _directory(root_descriptor, TYPES[kind], create=True)
        descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=folder_descriptor)
        try:
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("short write")
                view = view[written:]
            os.fsync(descriptor)
        except BaseException:
            current = os.stat(name, dir_fd=folder_descriptor, follow_symlinks=False)
            if (current.st_dev, current.st_ino) == (os.fstat(descriptor).st_dev, os.fstat(descriptor).st_ino):
                os.unlink(name, dir_fd=folder_descriptor)
            raise
        finally:
            os.close(descriptor)
    finally:
        if folder_descriptor is not None:
            os.close(folder_descriptor)
        os.close(root_descriptor)
    return root / TYPES[kind] / name


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory-root", required=True, type=Path)
    parser.add_argument("--file", required=True, type=Path, help="one JSON evidence record to save")
    parser.add_argument("--evidence", action="append", default=[], type=Path, help="explicit related JSON/Markdown record; read only")
    args = parser.parse_args(argv)
    try:
        if args.file.suffix.lower() != ".json":
            raise ValueError("--file must be a single JSON input file")
        record = evidence.load_record(args.file)
        related = [evidence.load_record(path) for path in args.evidence]
        print(save_record(record, args.memory_root, evidence_records=related))
        return 0
    except (OSError, ValueError, UnicodeError) as error:
        print("[FAIL] " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
