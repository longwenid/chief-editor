#!/usr/bin/env python3
"""只读修订验收：运行三个检查，并为完整候选树和 HEAD 对照生成版本证据。

python3 scripts/check_revision_snapshot.py --content-root . --repository . --with-regressions
镜像可用 --repository 指向只读原仓库；不提供时仅做快照，不能批准修订。
本脚本不保存证据文件，不 stage/commit，不读取外置运行时记忆。
stdout 只有一个 JSON；调用方必须检查 ok、diff_complete 与 snapshot_stable。
证据证明本次进程读到的内容与退出码，不证明模型隔离或作者原话真实性。
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

CHECKS = ("check_layers.py", "check_policy_coverage.py", "check_anchors.py")
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def source_tree(root):
    files = {}
    def scan_error(error):
        raise error
    for folder, dirs, names in os.walk(root, followlinks=False, onerror=scan_error):
        dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS)
        names = sorted(name for name in names if name not in SKIP_DIRS and not name.endswith((".pyc", ".pyo")))
        for name in dirs + names:
            path = Path(folder) / name
            if path.is_symlink():
                raise ValueError(f"拒绝候选树中的符号链接：{path.relative_to(root)}")
        for name in names:
            path = Path(folder) / name
            if not path.is_file():
                raise ValueError(f"拒绝非普通文件：{path.relative_to(root)}")
            mode = "100755" if path.stat().st_mode & stat.S_IXUSR else "100644"
            files[path.relative_to(root).as_posix()] = (path.read_bytes(), mode)
    return files


def git_read(repository, *args):
    run = subprocess.run(["git", "--no-optional-locks", "-C", str(repository), *args],
                         capture_output=True, check=False, timeout=60)
    if run.returncode:
        raise ValueError(run.stderr.decode("utf-8", "replace").strip() or "无法读取 Git HEAD")
    return run.stdout


def load_baseline(repository):
    if repository is None:
        return None, {}
    head = git_read(repository, "rev-parse", "HEAD").decode().strip()
    entries = git_read(repository, "ls-tree", "-r", "-z", "--full-tree", head)
    files = {}
    for raw in entries.split(b"\0"):
        if not raw:
            continue
        info, raw_path = raw.split(b"\t", 1)
        mode, kind, oid = info.decode().split()
        path = raw_path.decode("utf-8")
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"HEAD 含不支持的链接/子模块：{path}")
        if any(part in SKIP_DIRS for part in Path(path).parts) or path.endswith((".pyc", ".pyo")):
            continue
        files[path] = (git_read(repository, "cat-file", "blob", oid), mode)
    return head, files


def file_diff(path, old, new):
    old_bytes, old_mode = old if old else (b"", None)
    new_bytes, new_mode = new if new else (b"", None)
    if old == new:
        return ""
    lines = [f"diff --git a/{path} b/{path}\n"]
    if old is None:
        lines.append(f"new file mode {new_mode}\n")
    elif new is None:
        lines.append(f"deleted file mode {old_mode}\n")
    elif old_mode != new_mode:
        lines += [f"old mode {old_mode}\n", f"new mode {new_mode}\n"]
    if b"\0" in old_bytes or b"\0" in new_bytes:
        lines.append(f"Binary content: {sha256(old_bytes)} -> {sha256(new_bytes)}\n")
    else:
        # Each source line has a separator in the patch, including files lacking a final newline.
        old_lines = old_bytes.decode("utf-8", "replace").splitlines(keepends=True)
        new_lines = new_bytes.decode("utf-8", "replace").splitlines(keepends=True)
        for line in difflib.unified_diff(old_lines, new_lines,
                                         fromfile=f"a/{path}" if old else "/dev/null",
                                         tofile=f"b/{path}" if new else "/dev/null"):
            lines.append(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n")
    return "".join(lines)


def describe(current, baseline, head):
    manifest, patches = [], []
    for path in sorted(set(current) | set(baseline)):
        old, new = baseline.get(path), current.get(path)
        patch = file_diff(path, old, new) if head else ""
        change = "unchanged" if old == new else "added" if old is None else "deleted" if new is None else "modified"
        manifest.append({"path": path, "sha256": sha256(new[0]) if new else None,
                         "mode": new[1] if new else None,
                         "baseline_sha256": sha256(old[0]) if old else None,
                         "baseline_mode": old[1] if old else None,
                         "change": change, "diff_sha256": sha256(patch.encode()) if patch else None})
        patches.append(patch)
    diff = "".join(patches)
    diff_hash = sha256(diff.encode())
    identity = {"schemaVersion": 1, "repository_head": head, "files": manifest, "diff_sha256": diff_hash}
    return {**identity, "snapshot_id": sha256(canonical(identity).encode()), "diff": diff}


def collect(root, repository=None, with_regressions=False):
    head, baseline = load_baseline(repository)
    before = source_tree(root)
    if "SKILL.md" not in before:
        raise ValueError("内容根缺少 SKILL.md")
    checks = []
    for script in CHECKS:
        path = root / "scripts" / script
        argv = [sys.executable, str(path), str(root)]
        try:
            result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                    timeout=120, check=False,
                                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"})
            checks.append({"script": script, "argv": argv, "exit_code": result.returncode,
                           "stdout": result.stdout, "stderr": result.stderr})
        except (OSError, subprocess.TimeoutExpired) as exc:
            checks.append({"script": script, "argv": argv, "exit_code": None,
                           "stdout": "", "stderr": str(exc)})
    regression = None
    if with_regressions:
        argv = [sys.executable, "-m", "unittest", "discover", "-s", str(root / "tests")]
        try:
            result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                    timeout=180, check=False, cwd=root,
                                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"})
            regression = {"name": "unittest", "argv": argv, "exit_code": result.returncode,
                          "stdout": result.stdout, "stderr": result.stderr}
        except (OSError, subprocess.TimeoutExpired) as exc:
            regression = {"name": "unittest", "argv": argv, "exit_code": None, "stdout": "", "stderr": str(exc)}
    after = source_tree(root)
    # Read HEAD again without reloading all blobs; a changed base invalidates this run too.
    final_head = git_read(repository, "rev-parse", "HEAD").decode().strip() if repository else None
    stable = before == after and head == final_head
    described = describe(after, baseline, head)
    return {**described, "content_root": str(root),
            "repository": str(repository) if repository else None,
            "diff_complete": head is not None, "snapshot_stable": stable, "checks": checks, "regression": regression,
            "skill_text": after["SKILL.md"][0].decode("utf-8"),
            "ok": stable and all(item["exit_code"] == 0 and item["stdout"].strip() for item in checks)
                  and (not with_regressions or regression["exit_code"] == 0 and bool((regression["stdout"] + regression["stderr"]).strip())),
            "scope": "候选目录全部普通文件（含未跟踪新增）；排除 .git、缓存、依赖目录；不读外置记忆",
            "unverified": ["独立 agent 是否忠实转交 stdout", "模型隔离", "作者原话真实性", "真实 DWF 宿主能力"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--with-regressions", action="store_true", help="额外运行标准库 unittest（包含 Node mock 回归）")
    args = parser.parse_args(argv)
    try:
        result = collect(args.content_root.resolve(), args.repository.resolve() if args.repository else None, args.with_regressions)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result = {"schemaVersion": 1, "ok": False, "diff_complete": False,
                  "snapshot_stable": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
