#!/usr/bin/env python3
"""只读验证精确文件及真实标题/AST 符号，不以正文或注释字符串冒充定义。

引用：references/red-lines.md#4（技能根相对路径），
$NOVEL_LEDGER/references/opening.md#标题（也接受 engine:references/...）。
旧 basename 引用只在技能与引擎范围内唯一时兼容；同名目标必须明确路径。
.md 支持完整标题（忽略空白/反引号）或唯一章节数字；.py 支持定义、赋值和导入绑定，
类方法可用 Class.method，未限定名字必须唯一。不会导入或执行引擎代码。

用法：python3 scripts/check_anchors.py [技能目录]
引擎按 NOVEL_LEDGER → 同级 novel-ledger → 用户安装目录解析。
"""
from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

REFERENCE = re.compile(
    r"(?<![\w/$:.\-])((?:\$NOVEL_LEDGER/|engine:)?(?:[\w.\-]+/)*[\w.\-]+\.(?:py|md))"
    r"#([^\s`|()\[\]、，。；<>]+)"
)
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", "node_modules", "validation", "tests", "docs", "assets"}


def visible_lines(text: str):
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


def normalize(text: str) -> str:
    return re.sub(r"[\s`]", "", text)


def engine_root(skill_root: Path) -> Path | None:
    explicit = os.environ.get("NOVEL_LEDGER")
    if explicit:
        candidate = Path(explicit).expanduser().resolve()
        if not (candidate / "scripts" / "novel.py").is_file():
            raise ValueError("NOVEL_LEDGER 指定目录缺少 scripts/novel.py；不静默回退")
        return candidate
    for candidate in (skill_root.parent / "novel-ledger", Path.home() / ".zcode" / "skills" / "novel-ledger"):
        if (candidate / "scripts" / "novel.py").is_file():
            return candidate.resolve()
    return None


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def index_files(roots: list[Path]) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".md"} or not inside(path, root):
                continue
            if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
                continue
            resolved = path.resolve()
            if resolved not in index.setdefault(path.name, []):
                index[path.name].append(resolved)
    return index


def resolve_target(target: str, skill_root: Path, engine: Path | None, index: dict[str, list[Path]]) -> Path:
    if target.startswith(("$NOVEL_LEDGER/", "engine:")):
        if engine is None:
            raise ValueError(f"{target}：未解析到引擎目录")
        relative = target.split("/", 1)[1] if target.startswith("$") else target[len("engine:"):]
        root = engine
    elif "/" in target:
        root, relative = skill_root, target
    else:
        candidates = index.get(target, [])
        if len(candidates) > 1:
            raise ValueError(f"{target}：同名目标歧义，请写精确路径：" + " / ".join(map(str, candidates)))
        if not candidates:
            raise ValueError(f"{target}：找不到文件")
        return candidates[0]
    path = (root / relative).resolve()
    if not inside(path, root):
        raise ValueError(f"{target}：目标越出声明根目录")
    if not path.is_file():
        raise ValueError(f"{target}：找不到精确文件")
    return path


def headings(text: str) -> list[str]:
    result = []
    previous = ""
    previous_number = 0
    for number, line in visible_lines(text):
        match = re.match(r"^[ ]{0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", line)
        if match:
            result.append(match.group(1))
        elif previous.strip() and number == previous_number + 1 and re.match(r"^[ ]{0,3}(?:=+|-+)\s*$", line):
            result.append(previous.strip())
        previous = line
        previous_number = number
    return result


def markdown_anchor(text: str, anchor: str) -> bool:
    titles = headings(text)
    matches = [title for title in titles if normalize(title) == normalize(anchor)]
    if not matches and re.fullmatch(r"\d+(?:\.\d+)*", anchor):
        matches = [title for title in titles if re.match(rf"^{re.escape(anchor)}(?=\s|$)", title)]
    return len(matches) == 1


def python_symbols(text: str) -> set[str]:
    """收集词法定义/模块及类绑定；不把字符串、注释和普通名称引用当定义。"""
    tree = ast.parse(text)
    symbols: set[str] = set()

    def bind(target, prefix):
        if isinstance(target, ast.Name):
            symbols.add(prefix + target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                bind(item, prefix)

    def walk(body, prefix="", bindings=True):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + node.name
                symbols.add(name)
                walk(node.body, name + ".", isinstance(node, ast.ClassDef))
            elif bindings and isinstance(node, (ast.Assign, ast.AnnAssign)):
                for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                    bind(target, prefix)
            elif bindings and isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name != "*":
                        symbols.add(prefix + (alias.asname or alias.name.split(".")[0]))
            else:
                for _, value in ast.iter_fields(node):
                    if isinstance(value, list) and value and all(isinstance(x, ast.stmt) for x in value):
                        walk(value, prefix, bindings)
                    elif isinstance(value, ast.ExceptHandler):
                        walk(value.body, prefix, bindings)
    walk(tree.body)
    return symbols


def python_anchor(text: str, anchor: str) -> bool:
    symbols = python_symbols(text)
    if "." in anchor:
        return anchor in symbols
    return sum(name.rsplit(".", 1)[-1] == anchor for name in symbols) == 1


def md_files(skill_root: Path) -> list[Path]:
    files = [skill_root / "SKILL.md"] + sorted((skill_root / "references").rglob("*.md"))
    template = skill_root / "memory" / "templates.md"
    if template.is_file():
        files.append(template)
    return files


def validate(skill_root: Path, engine: Path | None) -> tuple[list[str], int]:
    skill_root = skill_root.resolve()
    engine = engine.resolve() if engine is not None else None
    # 所有目标读取均被限制在上述两个可信根目录内。
    problems = []
    index = index_files([skill_root] + ([engine] if engine is not None else []))
    checked: set[tuple[Path, str]] = set()
    bodies: dict[Path, str] = {}
    for source in md_files(skill_root):
        if not source.is_file():
            problems.append(f"缺少文件：{source.relative_to(skill_root)}")
            continue
        if not inside(source, skill_root):
            problems.append(f"源文件越出技能根目录：{source}")
            continue
        for number, line in visible_lines(source.read_text(encoding="utf-8")):
            for target, anchor in REFERENCE.findall(line):
                where = f"{source.relative_to(skill_root)}:{number}"
                try:
                    candidate = resolve_target(target, skill_root, engine, index)
                    key = (candidate, anchor)
                    if key in checked:
                        continue
                    checked.add(key)
                    if candidate not in bodies:
                        bodies[candidate] = candidate.read_text(encoding="utf-8")
                    body = bodies[candidate]
                    matched = python_anchor(body, anchor) if candidate.suffix == ".py" else markdown_anchor(body, anchor)
                    if not matched:
                        problems.append(f"{where} 锚点失效或不唯一：{target}#{anchor}（要求真实定义/标题）")
                except (ValueError, OSError, UnicodeError, SyntaxError) as error:
                    problems.append(f"{where} {target}#{anchor}：{error}")
    return problems, len(checked)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0]).resolve() if argv else Path(__file__).resolve().parents[1]
    try:
        engine = engine_root(root)
        problems, count = validate(root, engine)
    except (ValueError, OSError, UnicodeError) as error:
        problems, count = [str(error)], 0
    if problems:
        print(f"[FAIL] 锚点校验：{len(problems)} 处问题")
        for item in problems:
            print("  -", item)
        return 1
    print(f"[OK] 锚点校验通过：{count} 个唯一精确目标的定义/标题有效")
    if engine is None:
        print("  ! 未配置引擎；仅验证技能内引用，引擎显式引用不会降级匹配")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
