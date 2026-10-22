"""Only temporary directories and synthetic records; never touch real editor memory."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


writer = load("memory_record_writer", ROOT / "scripts/save_editorial_record.py")
fixtures = load("memory_record_fixtures", ROOT / "tests/test_editorial_evidence.py")
NOW = datetime(2026, 10, 22, 12, 34, 56, 123456, timezone.utc)


class MemoryRecords(unittest.TestCase):
    def setUp(self):
        # macOS /var and /tmp can be system symlinks; use a physical temporary path.
        temp = tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.memory = self.base / "memory"

    def save(self, record=None, **kwargs):
        return writer.save_record(record or fixtures.minimal_market(), self.memory, now=NOW, **kwargs)

    def test_same_month_snapshots_coexist_and_old_bytes_do_not_change(self):
        first = self.save()
        old = first.read_bytes()
        next_record = fixtures.minimal_market()
        next_record["record_id"] = "market-second"
        second = writer.save_record(next_record, self.memory, now=NOW.replace(day=23))
        self.assertNotEqual(first, second)
        self.assertEqual(old, first.read_bytes())
        self.assertEqual(["2026-10-22", "2026-10-23"], sorted(p.name[:10] for p in first.parent.iterdir()))
        self.assertEqual(next_record, writer.evidence.load_record(second))
        self.assertEqual(1, second.read_text().count("```json"))

    def test_saved_market_without_scan_date_exposes_real_observation_times(self):
        loaded = writer.evidence.load_record(self.save())
        self.assertNotIn("scan_date", loaded)
        observed = max(writer.evidence.timestamp(row["at"], "observation.at") for row in loaded["observations"])
        self.assertEqual(datetime(2026, 10, 2, 12, tzinfo=timezone.utc), observed)
        # Legacy Markdown uses its explicit scan_date, never its newer filename.
        legacy = self.memory / "market" / "2026-10-22-legacy.md"
        legacy.write_text("# 旧快照\n- scan_date: 2026-09-30\n")
        scan_date = next(line.partition(": ")[2] for line in legacy.read_text().splitlines() if line.startswith("- scan_date: "))
        self.assertEqual("2026-09-30", scan_date)
        self.assertNotEqual(legacy.name[:10], scan_date)

    def test_late_created_and_saved_times_or_unrelated_data_do_not_refresh_claim(self):
        record = fixtures.minimal_market()
        record["created_at"] = "2026-11-20T12:00:00Z"
        record["sources"][0]["observed_at"] = "2026-11-10T12:00:00Z"
        record["observations"].append({**record["observations"][1], "observation_id": "unrelated-new", "work_id": "another-work", "at": "2026-11-10T12:00:00Z"})
        saved = writer.save_record(record, self.memory, now=NOW.replace(month=12))
        loaded = writer.evidence.load_record(saved)
        claim_ids = set(loaded["claims"][0]["evidence_ids"])
        claim_at = max(writer.evidence.timestamp(row["at"], "observation.at") for row in loaded["observations"] if row["observation_id"] in claim_ids)
        archive_at = max(writer.evidence.timestamp(row["at"], "observation.at") for row in loaded["observations"])
        self.assertEqual((2026, 10), (claim_at.year, claim_at.month))
        self.assertEqual((2026, 11), (archive_at.year, archive_at.month))
        self.assertEqual(11, writer.evidence.timestamp(loaded["created_at"], "created_at").month)
        self.assertTrue(saved.name.startswith("2026-12-"))

    def test_empty_observations_have_no_market_freshness_date(self):
        record = fixtures.minimal_market()
        record["observations"] = []
        record["claims"] = []
        record["missing_roles"]["head"] = "尚未取得任何实际榜单观察"
        loaded = writer.evidence.load_record(self.save(record))
        observed = max((writer.evidence.timestamp(row["at"], "observation.at") for row in loaded["observations"]), default=None)
        self.assertIsNone(observed)
        self.assertIsNotNone(loaded["created_at"])

    def test_same_month_cards_sort_by_observation_not_save_or_creation_time(self):
        recent = fixtures.minimal_market()
        recent["record_id"] = "market-recent-data"
        recent["created_at"] = "2026-10-12T12:00:00Z"
        recent["sources"][0]["observed_at"] = "2026-10-11T12:00:00Z"
        for row, day in zip(recent["observations"], (10, 11)):
            row["at"] = f"2026-10-{day:02d}T12:00:00Z"
        first = writer.save_record(recent, self.memory, now=NOW.replace(day=20))
        stale = fixtures.minimal_market()
        stale["record_id"] = "market-late-archive"
        stale["created_at"] = "2026-10-22T12:00:00Z"
        second = writer.save_record(stale, self.memory, now=NOW.replace(day=23))
        cards = [writer.evidence.load_record(path) for path in (first, second)]
        ordered = sorted(cards, key=lambda card: max(writer.evidence.timestamp(row["at"], "observation.at") for row in card["observations"]))
        self.assertEqual(["market-late-archive", "market-recent-data"], [card["record_id"] for card in ordered])
        self.assertGreater(second.name, first.name)
        self.assertGreater(cards[1]["created_at"], cards[0]["created_at"])

    def test_duplicate_id_is_rejected_even_on_a_different_day(self):
        first = self.save()
        old = first.read_bytes()
        changed = fixtures.minimal_market()
        changed["claims"][0]["statement"] = "不能用同一ID静默替换新的结论"
        with self.assertRaisesRegex(FileExistsError, "record_id already exists"):
            writer.save_record(changed, self.memory, now=NOW.replace(day=24))
        self.assertEqual(old, first.read_bytes())
        self.assertEqual([first], list(first.parent.iterdir()))

    def test_duplicate_id_is_global_across_record_types(self):
        self.save()
        taste = fixtures.minimal_taste()
        taste["record_id"] = "market-demo"
        with self.assertRaises(FileExistsError):
            self.save(taste)
        self.assertFalse((self.memory / "teardowns").exists())

    def test_missing_source_fails_before_memory_directory_is_created(self):
        record = fixtures.minimal_market()
        record["sources"] = []
        with self.assertRaisesRegex(ValueError, "证据|source|来源"):
            self.save(record)
        self.assertFalse(self.memory.exists())

    def test_unsupported_trend_fails_before_memory_directory_is_created(self):
        record = fixtures.minimal_market()
        record["claims"][0]["evidence_ids"] = ["day1"]
        with self.assertRaisesRegex(ValueError, "两个实际不同时点"):
            self.save(record)
        self.assertFalse(self.memory.exists())

    def test_record_id_cannot_be_a_path_or_hidden_filename(self):
        for identity in ("/absolute", "../escape", "..", "x/y", "x\\y", "a..b", "C:\\escape", "中文", "x" * 97):
            with self.subTest(identity=identity):
                record = fixtures.minimal_market()
                record["record_id"] = identity
                with self.assertRaises(ValueError):
                    self.save(record)
                self.assertFalse(self.memory.exists())

    def test_memory_root_must_be_explicit_absolute_without_traversal(self):
        for path in (Path("relative-memory"), self.base / "nested" / ".." / "other", Path("/")):
            with self.subTest(path=path), patch.object(writer, "_root_fd") as open_root:
                with self.assertRaisesRegex(ValueError, "memory-root"):
                    writer.save_record(fixtures.minimal_market(), path, now=NOW)
                open_root.assert_not_called()
        self.assertFalse((self.base / "nested").exists())

    def test_root_symlink_cannot_escape(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.memory.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            self.save()
        self.assertEqual([], list(outside.iterdir()))

    def test_parent_symlink_cannot_escape(self):
        outside = self.base / "outside"
        outside.mkdir()
        alias = self.base / "alias"
        alias.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            writer.save_record(fixtures.minimal_market(), alias / "memory", now=NOW)
        self.assertEqual([], list(outside.iterdir()))

    def test_record_directory_symlink_cannot_escape(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.memory.mkdir()
        (self.memory / "market").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            self.save()
        self.assertEqual([], list(outside.iterdir()))

    def test_existing_record_symlink_is_not_followed(self):
        outside = self.base / "outside.md"
        outside.write_text("private outside bytes")
        folder = self.memory / "market"
        folder.mkdir(parents=True)
        (folder / "redirect.md").symlink_to(outside)
        with self.assertRaises(OSError):
            self.save()
        self.assertEqual("private outside bytes", outside.read_text())
        self.assertEqual([folder / "redirect.md"], list(folder.iterdir()))

    def test_non_regular_record_does_not_block_reading(self):
        folder = self.memory / "market"
        folder.mkdir(parents=True)
        os.mkfifo(folder / "pipe.md")
        source = self.base / "input.json"
        source.write_text(json.dumps(fixtures.minimal_market()))
        command = [sys.executable, "-B", str(ROOT / "scripts/save_editorial_record.py"), "--memory-root", str(self.memory), "--file", str(source)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=3)
        self.assertEqual(1, result.returncode)
        self.assertIn("regular memory record", result.stderr)
        self.assertEqual([folder / "pipe.md"], list(folder.iterdir()))

    def test_exclusive_creation_does_not_overwrite_legacy_filename_collision(self):
        folder = self.memory / "market"
        folder.mkdir(parents=True)
        existing = folder / "2026-10-22-123456123456-market-demo.md"
        existing.write_bytes(b"legacy record without JSON\n")
        with self.assertRaises(FileExistsError):
            self.save()
        self.assertEqual(b"legacy record without JSON\n", existing.read_bytes())

    def test_existing_target_hardlink_does_not_change_outside_bytes(self):
        folder = self.memory / "market"
        folder.mkdir(parents=True)
        outside = self.base / "outside.md"
        outside.write_bytes(b"outside legacy bytes\n")
        existing = folder / "2026-10-22-123456123456-market-demo.md"
        os.link(outside, existing)
        with self.assertRaises(FileExistsError):
            self.save()
        self.assertEqual(b"outside legacy bytes\n", outside.read_bytes())
        self.assertEqual(outside.stat().st_ino, existing.stat().st_ino)

    def test_partial_write_failure_removes_only_its_created_file(self):
        original_write = writer.os.write

        def fail_after_partial_write(descriptor, data):
            original_write(descriptor, data[:7])
            raise OSError("simulated partial write failure")

        with patch.object(writer.os, "write", side_effect=fail_after_partial_write):
            with self.assertRaisesRegex(OSError, "simulated partial"):
                self.save()
        self.assertEqual([], list((self.memory / "market").iterdir()))

    def test_failure_cleanup_preserves_a_replacement_inode(self):
        filename = "2026-10-22-123456123456-market-demo.md"

        def replace_then_fail(_descriptor, _data):
            path = self.memory / "market" / filename
            path.rename(path.with_suffix(".moved"))
            path.write_bytes(b"unrelated replacement inode\n")
            raise OSError("simulated external replacement")

        with patch.object(writer.os, "write", side_effect=replace_then_fail):
            with self.assertRaisesRegex(OSError, "simulated external"):
                self.save()
        replacement = self.memory / "market" / filename
        self.assertEqual(b"unrelated replacement inode\n", replacement.read_bytes())

    def test_legacy_markdown_is_left_unchanged_and_does_not_block_new_records(self):
        folder = self.memory / "decisions"
        folder.mkdir(parents=True)
        legacy = folder / "2026-10-01-old-project.md"
        content = b"# Legacy\n- status: active\n"
        legacy.write_bytes(content)
        self.save()
        self.assertEqual(content, legacy.read_bytes())

    def test_malformed_json_evidence_is_reported_and_not_ignored(self):
        folder = self.memory / "decisions"
        folder.mkdir(parents=True)
        corrupt = folder / "corrupt.md"
        corrupt.write_text('```json\n{"record_id": }\n```\n')
        before = corrupt.read_bytes()
        with self.assertRaises(ValueError):
            self.save()
        self.assertEqual(before, corrupt.read_bytes())
        self.assertFalse((self.memory / "market").exists())

    def test_all_four_types_route_to_their_single_canonical_markdown_record(self):
        market = self.save()
        taste = self.save(fixtures.minimal_taste())
        selection_record = fixtures.minimal_selection()
        selection = self.save(selection_record)
        postmortem = self.save(fixtures.minimal_postmortem(), evidence_records=[selection_record])
        self.assertEqual(["market", "teardowns", "decisions", "postmortems"], [p.parent.name for p in (market, taste, selection, postmortem)])
        self.assertEqual("taste-demo.md", taste.name)
        self.assertEqual("2026-10-22-selection-demo.md", selection.name)
        self.assertEqual("2026-10-22-postmortem-demo.md", postmortem.name)
        self.assertEqual(selection_record, writer.evidence.load_record(selection))

    def test_related_evidence_is_explicit_validated_and_not_saved_implicitly(self):
        market = fixtures.minimal_market()
        selection = fixtures.minimal_selection()
        selection["basis"]["commercial_fit"].update(status="supported", market_record_ids=[market["record_id"]])
        with self.assertRaises(ValueError):
            self.save(selection)
        self.assertFalse(self.memory.exists())
        saved = self.save(selection, evidence_records=[market])
        self.assertTrue(saved.is_file())
        self.assertFalse((self.memory / "market").exists())

    def test_unsupported_backend_fails_before_creating_memory(self):
        with patch.object(writer, "fcntl", None):
            with self.assertRaisesRegex(ValueError, "unsupported"):
                self.save()
        self.assertFalse(self.memory.exists())

    def test_large_payload_is_rejected_before_creating_memory(self):
        record = fixtures.minimal_market()
        record["claims"][0]["statement"] = "x" * writer.MAX_BYTES
        with self.assertRaisesRegex(ValueError, "1 MiB"):
            self.save(record)
        self.assertFalse(self.memory.exists())

    def test_cli_requires_root_and_prints_only_the_saved_path(self):
        source = self.base / "input.json"
        source.write_text(json.dumps(fixtures.minimal_market()))
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            writer.main(["--file", str(source)])
        self.assertEqual(2, error.exception.code)
        output = io.StringIO()
        with redirect_stdout(output):
            result = writer.main(["--memory-root", str(self.memory), "--file", str(source)])
        self.assertEqual(0, result)
        self.assertTrue(Path(output.getvalue().strip()).is_file())

    def test_cli_saves_postmortem_with_explicit_read_only_dependency(self):
        dependency = self.base / "selection.md"
        dependency.write_text("```json\n" + json.dumps(fixtures.minimal_selection()) + "\n```\n")
        before = dependency.read_bytes()
        source = self.base / "postmortem.json"
        source.write_text(json.dumps(fixtures.minimal_postmortem()))
        with redirect_stdout(io.StringIO()):
            result = writer.main(["--memory-root", str(self.memory), "--file", str(source), "--evidence", str(dependency)])
        self.assertEqual(0, result)
        self.assertEqual(before, dependency.read_bytes())
        self.assertEqual(["postmortems"], [p.name for p in self.memory.iterdir()])

    def test_concurrent_duplicate_writers_leave_one_unchanged_record(self):
        source = self.base / "input.json"
        record = fixtures.minimal_market()
        source.write_text(json.dumps(record))
        command = [sys.executable, "-B", str(ROOT / "scripts/save_editorial_record.py"), "--memory-root", str(self.memory), "--file", str(source)]
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        statuses = []
        for process in processes:
            process.communicate(timeout=10)
            statuses.append(process.returncode)
        self.assertEqual([0, 1], sorted(statuses))
        files = list((self.memory / "market").iterdir())
        self.assertEqual(1, len(files))
        self.assertEqual(record, writer.evidence.load_record(files[0]))


if __name__ == "__main__":
    unittest.main()
