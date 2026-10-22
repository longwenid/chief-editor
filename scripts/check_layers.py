#!/usr/bin/env python3
"""分层校验：禁止跨层泄漏。

规则
1. 只有 references/environment.md 允许出现绝对路径与平台专有路径写法。
2. flows/*.md 不得重新定义授权档位（只允许 "tier: 见 policy §2" 这种引用）。
3. engine-cli.md 不得出现档位列或"作者门槛"列。
4. 只有 references/policy.md 允许出现 T0/T1/T2 的小节标题。
5. SKILL.md 保持入口体量（≤ 130 行）。

用法：python3 scripts/check_layers.py [技能目录]
退出码 1 表示有违规。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]

ABS_PATH_PATTERNS = [
    (re.compile(r"[A-Za-z]:[\\/]Users"), "Windows 绝对路径"),
    (re.compile(r"%USERPROFILE%"), "Windows 环境变量路径"),
    (re.compile(r"(?<![\w.])/Users/"), "Unix 绝对路径"),
    (re.compile(r"~/\."), "home 简写路径"),
]
TIER_DEF = re.compile(r"T[012][^\n|]{0,12}(作者专属|预授权|上报即停)")
TIER_HEADING = re.compile(r"^#{2,4}\s*T[012]\b", re.MULTILINE)
TIER_COLUMN = re.compile(r"\|\s*T[012]\s*\|")
AUTHOR_GATE_COLUMN = re.compile(r"作者门槛")
MAX_SKILL_LINES = 130


def md_files() -> list[Path]:
    files = [SKILL_ROOT / "SKILL.md"]
    files += sorted((SKILL_ROOT / "references").rglob("*.md"))
    template = SKILL_ROOT / "memory" / "templates.md"
    if template.exists():
        files.append(template)
    return [f for f in files if f.exists()]


def main() -> int:
    problems: list[str] = []

    for path in md_files():
        rel = path.relative_to(SKILL_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        is_env = rel == "references/environment.md"

        if not is_env:
            for pattern, label in ABS_PATH_PATTERNS:
                for match in pattern.finditer(text):
                    line = text.count("\n", 0, match.start()) + 1
                    problems.append(f"{rel}:{line} 泄漏{label}：{match.group(0)}（应只写在 environment.md）")

        if rel.startswith("references/flows/"):
            for match in TIER_DEF.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                problems.append(f"{rel}:{line} 重复定义档位：{match.group(0)}（改为引用 policy.md §2）")

        if rel == "references/engine-cli.md":
            for pattern, label in ((TIER_COLUMN, "档位列"), (AUTHOR_GATE_COLUMN, "作者门槛列")):
                for match in pattern.finditer(text):
                    line = text.count("\n", 0, match.start()) + 1
                    problems.append(f"{rel}:{line} 出现{label}（档位归属只在 policy.md）")

        if rel != "references/policy.md":
            for match in TIER_HEADING.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                problems.append(f"{rel}:{line} 出现档位小节标题（档位定义只属于 policy.md）")

    skill = SKILL_ROOT / "SKILL.md"
    if skill.exists():
        lines = skill.read_text(encoding="utf-8").count("\n") + 1
        if lines > MAX_SKILL_LINES:
            problems.append(f"SKILL.md 有 {lines} 行，超过入口层上限 {MAX_SKILL_LINES} 行（细节应下沉到 references/）")

    if problems:
        print(f"[FAIL] 分层校验：{len(problems)} 处违规")
        for item in problems:
            print("  -", item)
        return 1

    print("[OK] 分层校验通过：绝对路径、档位定义、命令表列都待在各自的层里")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
