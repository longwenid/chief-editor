"""标准库入口同时运行快照 helper 与 Node 工作流回归；不提交 Git fixture。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("revision_snapshot", ROOT / "scripts/check_revision_snapshot.py")
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        (self.root / "SKILL.md").write_text("品位\n", encoding="utf-8")
        for name in snapshot.CHECKS:
            (self.root / "scripts" / name).write_text("print('[OK]')\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_real_stub_subprocesses_and_snapshot_only_is_not_complete_diff(self):
        result = snapshot.collect(self.root)
        self.assertTrue(result["ok"])
        self.assertFalse(result["diff_complete"])
        self.assertEqual([item["exit_code"] for item in result["checks"]], [0, 0, 0])

    def test_manifest_and_diff_cover_modified_added_deleted_and_file_modes(self):
        current = {"SKILL.md": ("新版\n".encode(), "100644"), "new.py": (b"new\n", "100755")}
        baseline = {"SKILL.md": ("旧版\n".encode(), "100644"), "removed.md": (b"old\n", "100644")}
        result = snapshot.describe(current, baseline, "a" * 40)
        self.assertEqual({f["path"]: f["change"] for f in result["files"]}, {"SKILL.md": "modified", "new.py": "added", "removed.md": "deleted"})
        for file in result["files"]:
            patch_text = snapshot.file_diff(file["path"], baseline.get(file["path"]), current.get(file["path"]))
            self.assertEqual(file["diff_sha256"], hashlib.sha256(patch_text.encode()).hexdigest())
            self.assertIn(patch_text, result["diff"])
        identity = {k: result[k] for k in ("schemaVersion", "repository_head", "files", "diff_sha256")}
        self.assertEqual(result["snapshot_id"], snapshot.sha256(snapshot.canonical(identity).encode()))

    def test_optional_regression_runs_real_unittest_and_binds_skill_text(self):
        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_sample.py").write_text("import unittest\nclass Sample(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n")
        result = snapshot.collect(self.root, with_regressions=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["regression"]["exit_code"], 0)
        self.assertIn("Ran 1 test", result["regression"]["stderr"])
        self.assertEqual(result["skill_text"], (self.root / "SKILL.md").read_text())

    def test_regression_failure_cannot_be_masked_by_three_passing_checks(self):
        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_sample.py").write_text("import unittest\nclass Sample(unittest.TestCase):\n def test_bad(self): self.assertTrue(False)\n")
        result = snapshot.collect(self.root, with_regressions=True)
        self.assertFalse(result["ok"])
        self.assertEqual([c["exit_code"] for c in result["checks"]], [0, 0, 0])
        self.assertNotEqual(result["regression"]["exit_code"], 0)

    def test_source_change_during_checks_fails(self):
        changed = "from pathlib import Path\np=Path(__file__).parent.parent/'SKILL.md'\np.write_text('changed')\nprint('[OK]')\n"
        (self.root / "scripts" / snapshot.CHECKS[0]).write_text(changed)
        result = snapshot.collect(self.root)
        self.assertFalse(result["snapshot_stable"])
        self.assertFalse(result["ok"])

    def test_failed_check_keeps_exact_failure_evidence(self):
        (self.root / "scripts" / snapshot.CHECKS[1]).write_text("import sys\nprint('broken')\nsys.exit(7)\n")
        result = snapshot.collect(self.root)
        self.assertFalse(result["ok"])
        self.assertEqual(result["checks"][1]["exit_code"], 7)
        self.assertIn("broken", result["checks"][1]["stdout"])

    def test_untracked_files_participate_and_no_receipt_directory_is_hidden(self):
        first = snapshot.describe(snapshot.source_tree(self.root), {}, None)
        (self.root / ".revision-evidence").mkdir()
        (self.root / ".revision-evidence" / "new.py").write_text("not hidden")
        second = snapshot.describe(snapshot.source_tree(self.root), {}, None)
        self.assertNotEqual(first["snapshot_id"], second["snapshot_id"])
        self.assertIn(".revision-evidence/new.py", [f["path"] for f in second["files"]])

    def test_symlink_source_is_rejected(self):
        (self.root / "outside.py").symlink_to(ROOT / "SKILL.md")
        with self.assertRaisesRegex(ValueError, "符号链接"):
            snapshot.source_tree(self.root)

    def test_git_worktree_administration_file_is_excluded(self):
        (self.root / ".git").write_text("gitdir: /private/worktree/admin")
        self.assertNotIn(".git", snapshot.source_tree(self.root))

    def test_directory_scan_errors_fail_closed(self):
        def failed_walk(root, followlinks, onerror):
            onerror(PermissionError("cannot scan a candidate directory"))
        with patch.object(snapshot.os, "walk", side_effect=failed_walk):
            with self.assertRaisesRegex(PermissionError, "cannot scan"):
                snapshot.source_tree(self.root)

    def test_repository_head_read_is_only_and_failure_not_success(self):
        completed = subprocess.CompletedProcess([], 1, b"", b"missing HEAD")
        with patch.object(snapshot.subprocess, "run", return_value=completed) as runner:
            with self.assertRaisesRegex(ValueError, "missing HEAD"):
                snapshot.load_baseline(self.root)
        argv = runner.call_args.args[0]
        self.assertEqual(argv[:3], ["git", "--no-optional-locks", "-C"])
        self.assertNotIn("commit", argv)

    def test_complete_repository_baseline_with_no_git_fixture_commit(self):
        baseline = {"SKILL.md": (b"old\n", "100644"), "old.md": (b"removed\n", "100644")}
        with patch.object(snapshot, "load_baseline", return_value=("a" * 40, baseline)), patch.object(snapshot, "git_read", return_value=("a" * 40 + "\n").encode()):
            result = snapshot.collect(self.root, self.root)
        self.assertTrue(result["ok"])
        self.assertTrue(result["diff_complete"])
        self.assertIn("deleted file mode", result["diff"])
        self.assertIn("new file mode", result["diff"])


class WorkflowNodeTests(unittest.TestCase):
    def test_node_workflow_regressions(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "需已有 Node 23+（内置 stripTypeScriptTypes），不自动安装")
        result = subprocess.run([node, "--test", str(ROOT / "tests/test_revision_workflow.cjs")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
