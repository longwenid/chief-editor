#!/usr/bin/env python3
"""只读核验真实 T0/T1 表格归属；命令索引、正文和注释不构成授权。

操作面、Worker 门任务例外和排除面均从 engine-cli.md 声明取得，不复制引擎常量。
用法：python3 scripts/check_policy_coverage.py [技能目录]
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandRow:
    commands: frozenset[str]
    tier: str
    scope: str
    line: int


def visible_lines(text: str):
    """忽略 fenced code 与 HTML 注释，保留原行号。"""
    text = re.sub(r"<!--.*?(?:-->|$)", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        marker = re.match(r"^[ ]{0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1] and not marker.group(2).strip():
                fence = None
            continue
        if fence is None:
            yield number, line


def cells(line: str) -> list[str]:
    """分表格单元：代码跨度中的管道和转义管道不切列。"""
    if not re.match(r"^[ ]{0,3}\|", line):
        return []
    result, current = [], []
    in_code = escaped = False
    for char in line.strip()[1:]:
        if char == "|" and not in_code and not escaped:
            result.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        if char == "`" and not escaped:
            in_code = not in_code
        escaped = char == "\\" and not escaped
    if current:
        result.append("".join(current).strip())
    return result


def command_heads(cell: str) -> set[str]:
    """支持多个代码跨度与顶层 promote | discard，不误读参数里的 md|html。"""
    commands: set[str] = set()
    for span in re.findall(r"`([^`]+)`", cell):
        parts, current, depth = [], [], 0
        for char in span.replace("\\|", "|"):
            if char in "([":
                depth += 1
            elif char in ")]":
                depth = max(0, depth - 1)
            if char == "|" and depth == 0:
                parts.append("".join(current))
                current = []
            else:
                current.append(char)
        parts.append("".join(current))
        for part in parts:
            part = re.sub(r"^\s*--owner\s+\S+\s+", "", part.strip())
            match = re.match(r"^([a-z][a-z0-9-]*)(?=\s|$)", part)
            if match:
                commands.add(match.group(1))
    return commands


def section_lines(text: str, heading: str):
    active = found = False
    for number, line in visible_lines(text):
        if re.match(r"^##\s+", line):
            if line.strip() == heading:
                active = found = True
                continue
            if active:
                break
        if active:
            yield number, line
    if not found:
        raise ValueError(f"缺少小节：{heading}")


def table_rows(lines):
    """只有带「命令」表头及 Markdown 分隔行的连续表格才构成命令表。"""
    previous = None
    active = False
    for number, line in lines:
        row = cells(line)
        if not row:
            previous, active = None, False
            continue
        separator = len(row) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in row)
        if separator and previous is not None:
            active = previous[0] == "命令"
            previous = None
        elif active:
            yield number, row
        else:
            previous = row


def engine_commands(text: str) -> tuple[set[str], set[str], set[str]]:
    declared, exceptions, excluded = set(), set(), set()
    lines = list(section_lines(text, "## 1 命令表"))
    for _, row in table_rows(lines):
        declared.update(command_heads(row[0]))
    exception_section = False
    for _, line in lines:
        if re.match(r"^###\s+", line):
            exception_section = "Worker 面" in line and "唯一例外" in line
        if exception_section and "门任务主干可自执" in line and "`opening_options`" in line:
            for span in re.findall(r"`([^`]+)`", line):
                if re.match(r"^[a-z][a-z0-9-]*\s+--", span):
                    exceptions.update(command_heads(f"`{span}`"))
        if "不在总编操作面的命令：" in line:
            names = re.sub(r"（[^）]*）", "", line.split("不在总编操作面的命令：", 1)[1])
            excluded.update(command_heads(names))
    if not declared:
        raise ValueError("engine-cli.md 命令表没有可解析命令")
    if not exceptions:
        raise ValueError("engine-cli.md 缺少可解析的 opening_options 主干例外声明")
    if not excluded:
        raise ValueError("engine-cli.md 缺少可解析的操作面排除声明")
    if (declared | exceptions) & excluded:
        raise ValueError("engine-cli.md 的操作面与排除面互相冲突")
    return declared | exceptions, exceptions, excluded


def policy_rows(text: str) -> list[CommandRow]:
    result = []
    tier = ""
    tiers = {}
    lines = list(section_lines(text, "## 2 命令 × 档位权威表"))
    for number, line in lines:
        heading = re.match(r"^###\s+(.*)", line)
        if heading:
            match = re.match(r"(T[01])\b", heading.group(1))
            tier = match.group(1) if match else ""
        tiers[number] = tier
    for number, row in table_rows(lines):
        if tiers[number] and len(row) >= 2:
            commands = command_heads(row[0])
            if commands:
                result.append(CommandRow(frozenset(commands), tiers[number], row[1], number))
    return result


def validate(skill_root: Path) -> tuple[list[str], int]:
    paths = [skill_root / "references" / name for name in ("engine-cli.md", "policy.md")]
    missing = [f"缺少文件：{path.relative_to(skill_root)}" for path in paths if not path.is_file()]
    if missing:
        return missing, 0
    try:
        declared, exceptions, excluded = engine_commands(paths[0].read_text(encoding="utf-8"))
        rows = policy_rows(paths[1].read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError) as error:
        return [str(error)], 0
    problems = []
    covered: set[str] = set()
    for row in rows:
        covered.update(row.commands)
        for command in sorted(row.commands & excluded):
            problems.append(f"policy.md:{row.line} {command} 被引擎契约排除，不得获得主干档位")
        for command in sorted(row.commands - declared - excluded):
            problems.append(f"policy.md:{row.line} {command} 未在 engine-cli.md 操作面声明")
        if row.commands & exceptions:
            limited = row.tier == "T1" and all(token in row.scope for token in ("仅", "`opening_options`", "门任务"))
            if not limited:
                problems.append(f"policy.md:{row.line} Worker 面例外必须在 T1 范围列限定为仅 opening_options 门任务")
    for command in sorted(declared - covered):
        problems.append(f"{command} 没有真实 T0/T1 表格归属（命令索引与正文不算覆盖）")
    return problems, len(declared)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0]).resolve() if argv else Path(__file__).resolve().parents[1]
    problems, count = validate(root)
    if problems:
        print(f"[FAIL] 档位覆盖校验：{len(problems)} 处问题")
        for item in problems:
            print("  -", item)
        return 1
    print(f"[OK] 覆盖校验通过：{count} 条命令均有真实 T0/T1 表格归属，Worker 例外范围有效")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
