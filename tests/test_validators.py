"""Validator regressions: missing authority and stale references must fail closed."""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


coverage = load("check_policy_coverage")
anchors = load("check_anchors")

ENGINE = """# Engine
## 1 命令表
### 1.1 常规命令
| 命令 | 用途 |
|---|---|
| `run --source 'text'` | run |
| `--owner ID promote \\| discard` | revision |
| `--owner ID export [--format md\\|html]` | preview |
### 1.4 门任务自执时的 Worker 面（唯一例外）
`opening_options` 门任务主干可自执：`read --task ID` / `recall --task ID` / `check --file result.json` / `submit --file result.json`。
不在总编操作面的命令：`patch`、`worker-next`（Worker-only）；`preflight`（总编走 `check`）；`host-step` / `host-loop`（外部宿主）。
## 2 禁止清单
"""
POLICY = """# Policy
## 2 命令 × 档位权威表
### T0 作者专属
| 命令 | 范围 | 要点 |
|---|---|---|
| `run` | 首次授权 | |
### T1 授权内自主
| 命令 | 范围 | 要点 |
|---|---|---|
| `promote` / `discard` | 当前目标 | |
| `export` | 预览 | |
| `read` / `recall` / `check` / `submit` | 仅 `opening_options` 门任务自执 | |
### T2 上报即停
### 命令索引
`run` `promote` `discard` `export` `read` `recall` `check` `submit`
## 3 其他
"""


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "skill"
        self.engine = self.base / "engine"
        self.root.mkdir()
        self.engine.mkdir()
        self.put(self.root, "SKILL.md", "# Fixture\n")
        self.put(self.engine, "scripts/novel.py", "# trusted engine marker\n")

    def put(self, root, name, text):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


class PolicyCoverageTests(Fixture):
    def setUp(self):
        super().setUp()
        self.put(self.root, "references/engine-cli.md", ENGINE)
        self.policy = self.put(self.root, "references/policy.md", POLICY)

    def check(self, text=None):
        if text is not None:
            self.policy.write_text(text, encoding="utf-8")
        return coverage.validate(self.root)

    def test_real_rows_cover_all_eight_commands(self):
        self.assertEqual(([], 8), self.check())

    def test_index_does_not_replace_missing_authority_rows(self):
        text = POLICY.replace("| `promote` / `discard` | 当前目标 | |\n", "")
        problems, _ = self.check(text)
        self.assertTrue(any("promote 没有真实" in p for p in problems))
        self.assertTrue(any("discard 没有真实" in p for p in problems))

    def test_combined_engine_cell_checks_discard_too(self):
        text = POLICY.replace("`promote` / `discard`", "`promote`")
        problems, _ = self.check(text)
        self.assertEqual(1, len(problems))
        self.assertIn("discard 没有真实", problems[0])

    def test_argument_alternatives_do_not_become_commands(self):
        declared, exceptions, excluded = coverage.engine_commands(ENGINE)
        self.assertNotIn("html", declared)
        self.assertNotIn("check", excluded)
        self.assertEqual({"read", "recall", "check", "submit"}, exceptions)

    def test_prose_mentions_cannot_replace_authority(self):
        text = POLICY.replace("| `export` | 预览 | |", "正文举例：`export`")
        self.assertTrue(any("export 没有真实" in p for p in self.check(text)[0]))

    def test_comments_and_code_examples_cannot_replace_authority(self):
        row = "| `export` | 预览 | |"
        for replacement in ("<!-- " + row + " -->", "```md\n" + row + "\n```"):
            with self.subTest(replacement=replacement):
                self.assertTrue(any("export 没有真实" in p for p in self.check(POLICY.replace(row, replacement))[0]))

    def test_standalone_pipe_line_is_not_a_command_table(self):
        text = POLICY.replace("| `export` | 预览 | |\n", "")
        text = text.replace("### T1 授权内自主", "### T1 授权内自主\n\n| `export` | 伪表格 | |\n")
        self.assertTrue(any("export 没有真实" in p for p in self.check(text)[0]))

    def test_unclosed_comment_cannot_grant_authority(self):
        text = POLICY.replace("### T1 授权内自主", "### T1 授权内自主\n<!-- unclosed")
        self.assertTrue(any("export 没有真实" in p for p in self.check(text)[0]))

    def test_indented_code_table_is_not_authority(self):
        text = POLICY.replace("| `export` | 预览 | |\n", "")
        text = text.replace("### T1 授权内自主", "### T1 授权内自主\n\n    | 命令 | 范围 |\n    |---|---|\n    | `export` | preview |\n")
        self.assertTrue(any("export 没有真实" in p for p in self.check(text)[0]))

    def test_worker_exception_requires_scope_in_range_column(self):
        text = POLICY.replace("仅 `opening_options` 门任务自执", "随时自主")
        self.assertTrue(any("Worker 面例外" in p for p in self.check(text)[0]))

    def test_worker_scope_in_notes_does_not_grant_permission(self):
        text = POLICY.replace("| 仅 `opening_options` 门任务自执 | |", "| 主干常规操作 | 仅 `opening_options` 门任务 |")
        self.assertTrue(any("Worker 面例外" in p for p in self.check(text)[0]))

    def test_worker_exception_cannot_move_to_t0(self):
        text = POLICY.replace("### T1 授权内自主", "### T0 错误分类")
        self.assertTrue(any("Worker 面例外" in p for p in self.check(text)[0]))

    def test_excluded_command_cannot_gain_regular_tier(self):
        text = POLICY.replace("| `export` | 预览 | |", "| `export` / `patch` | 预览 | |")
        self.assertTrue(any("patch 被引擎契约排除" in p for p in self.check(text)[0]))

    def test_undeclared_command_fails(self):
        text = POLICY.replace("| `export` | 预览 | |", "| `export` / `invented-command` | 预览 | |")
        self.assertTrue(any("invented-command 未在" in p for p in self.check(text)[0]))

    def test_missing_file_is_reported(self):
        self.policy.unlink()
        self.assertIn("缺少文件", self.check()[0][0])

    def test_missing_section_does_not_fall_back_to_all_tokens(self):
        text = POLICY.replace("## 2 命令 × 档位权威表", "## Renamed")
        self.assertIn("缺少小节", self.check(text)[0][0])


class AnchorTests(Fixture):
    def check(self, ref, engine=True):
        self.put(self.root, "SKILL.md", "# Fixture\n" + ref + "\n")
        return anchors.validate(self.root, self.engine if engine else None)[0]

    def test_exact_target_does_not_fall_back_to_other_same_name(self):
        self.put(self.root, "references/opening.md", "# Local\n")
        self.put(self.engine, "references/opening.md", "# Engine heading\n")
        problems = self.check("`references/opening.md#Engineheading`")
        self.assertTrue(problems)
        self.assertIn("真实定义/标题", problems[0])

    def test_ambiguous_basename_requires_explicit_path(self):
        self.put(self.root, "references/opening.md", "# Shared\n")
        self.put(self.engine, "references/opening.md", "# Shared\n")
        self.assertIn("同名目标歧义", self.check("`opening.md#Shared`")[0])
        self.assertEqual([], self.check("`$NOVEL_LEDGER/references/opening.md#Shared`"))

    def test_unique_legacy_basename_remains_compatible(self):
        self.put(self.root, "references/unique.md", "# Unique\n")
        self.assertEqual([], self.check("`unique.md#Unique`"))

    def test_missing_exact_file_fails(self):
        self.assertIn("找不到精确文件", self.check("`references/missing.md#Title`")[0])

    def test_prose_comment_and_fenced_heading_cannot_match(self):
        self.put(self.root, "references/target.md", "Title in prose\n<!-- # Title -->\n```md\n# Title\n```\n")
        self.assertTrue(self.check("`references/target.md#Title`"))

    def test_heading_must_be_complete(self):
        self.put(self.root, "references/target.md", "# Fast mode: five chapters\n")
        self.assertTrue(self.check("`references/target.md#Fastmode`"))
        self.assertEqual([], self.check("`references/target.md#Fastmode:fivechapters`"))

    def test_numeric_section_prefix_and_backtick_heading(self):
        self.put(self.root, "references/target.md", "## 12 Project boundary\n### Proxy (`style.py`)\n")
        self.assertEqual([], self.check("`references/target.md#12`"))
        self.assertTrue(anchors.markdown_anchor("### 五条代理判据（`style.py`）\n", "五条代理判据（style.py）"))

    def test_duplicate_headings_fail_closed(self):
        self.put(self.root, "references/target.md", "# Title\n## Title\n")
        self.assertTrue(self.check("`references/target.md#Title`"))

    def test_setext_headings_are_supported(self):
        self.put(self.root, "references/target.md", "Setext Title\n============\n")
        self.assertEqual([], self.check("`references/target.md#SetextTitle`"))

    def test_setext_cannot_cross_code_block_boundary(self):
        self.put(self.root, "references/target.md", "Missing\n```\ntext\n```\n---\n")
        self.assertTrue(self.check("`references/target.md#Missing`"))

    def test_unclosed_comment_and_invalid_fence_close_hide_fake_heading(self):
        for body in ("<!-- unclosed\n# Missing\n", "```md\n```not-a-close\n# Missing\n```\n"):
            with self.subTest(body=body):
                self.put(self.root, "references/target.md", body)
                self.assertTrue(self.check("`references/target.md#Missing`"))

    def test_python_comment_string_and_reference_are_not_definition(self):
        self.put(self.engine, "scripts/target.py", '# gone\nMESSAGE = "gone"\nprint(gone)\n')
        self.assertTrue(self.check("`$NOVEL_LEDGER/scripts/target.py#gone`"))

    def test_python_definitions_and_bindings_are_valid(self):
        self.put(self.engine, "scripts/target.py", "from os import path as local_path\nLIMIT = 3\nasync def worker():\n    pass\nclass App:\n    def controller_guard(self):\n        pass\n")
        for symbol in ("local_path", "LIMIT", "worker", "App.controller_guard", "controller_guard"):
            with self.subTest(symbol=symbol):
                self.assertEqual([], self.check("`$NOVEL_LEDGER/scripts/target.py#" + symbol + "`"))

    def test_duplicate_python_method_names_require_qualification(self):
        self.put(self.engine, "scripts/target.py", "class A:\n    def run(self): pass\nclass B:\n    def run(self): pass\n")
        self.assertTrue(self.check("`engine:scripts/target.py#run`"))
        self.assertEqual([], self.check("`engine:scripts/target.py#A.run`"))

    def test_python_is_parsed_never_executed(self):
        marker = self.base / "must-not-exist"
        self.put(self.engine, "scripts/target.py", f"from pathlib import Path\nPath({str(marker)!r}).touch()\nSYMBOL = 1\n")
        self.assertEqual([], self.check("`engine:scripts/target.py#SYMBOL`"))
        self.assertFalse(marker.exists())

    def test_python_invalid_syntax_is_reported(self):
        self.put(self.engine, "scripts/target.py", "def broken(:\n")
        self.assertTrue(self.check("`engine:scripts/target.py#broken`"))

    def test_traversal_and_symlink_cannot_escape_trusted_roots(self):
        self.put(self.base, "outside.md", "# Outside\n")
        self.assertIn("越出声明根目录", self.check("`../outside.md#Outside`")[0])
        (self.root / "references").mkdir()
        (self.root / "references" / "escape.md").symlink_to(self.base / "outside.md")
        self.assertIn("越出声明根目录", self.check("`references/escape.md#Outside`")[0])

    def test_explicit_engine_reference_requires_engine(self):
        self.assertIn("未解析到引擎目录", self.check("`engine:references/target.md#Title`", engine=False)[0])

    def test_invalid_explicit_engine_path_does_not_fall_back(self):
        with patch.dict(os.environ, {"NOVEL_LEDGER": str(self.base / "missing")}):
            with self.assertRaisesRegex(ValueError, "不静默回退"):
                anchors.engine_root(self.root)

    def test_missing_skill_entry_fails(self):
        (self.root / "SKILL.md").unlink()
        self.assertIn("缺少文件", anchors.validate(self.root, self.engine)[0][0])


if __name__ == "__main__":
    unittest.main()
