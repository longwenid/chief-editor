#!/usr/bin/env python3
"""Plan one custom opening regroup from caller-verified declarations; never execute it.

Read a JSON object from stdin (or the optional JSON file), print a JSON plan to stdout.
This validates input shape and applies the skill's two-round limit. It cannot establish
real authorization, the current board, prior counts, or semantic consistency. No engine
imports, subprocesses, project reads, or project writes are performed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

GATES = frozenset((
    "genre", "premise", "voice", "scale", "world", "ladder", "origin", "edge",
    "protagonist", "relationships", "opposition", "payoff", "title",
))
CONFIRMED_FIELDS = frozenset(("mainline", "style", "target", "scope"))
REQUIRED = frozenset((
    "project", "gate", "board_hash", "decision_kind", "source_quote",
    "authority_covers_refinement", "changes_confirmed", "rejection_reasons", "retain",
    "requirements", "prior_custom_regroups",
))
OPTIONAL = frozenset(("self_proposed", "owner"))
MAX_CUSTOM_REGROUPS = 2
LIMITATIONS = [
    "仅校验输入与技能治理条件，不证明授权原话真实性、授权范围、当前 board 或历史次数。",
    "调用方须核对当前项目/门/展示哈希及同一门历次台账；换会话或换 board 不清零。",
    "owner 若提供必须由调用方核对真实身份、项目与租约；规划器不生成 owner，也不 claim/run。",
    "两轮是总编技能的治理上限，不是引擎机械强制；具体要求与旧决定是否冲突仍须人工核对。",
]


def _result(status: str, message: str, **extra: object) -> dict:
    return {"status": status, "message": message, "verification_scope": "input_validation_only",
            "authorization_verified": False, "board_verified": False, "history_verified": False,
            "owner_verified": False,
            "limitations": list(LIMITATIONS), **extra}


def _text(value: object, label: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or "\0" in value or (not empty and not value.strip()):
        raise ValueError(label + " 必须是非空字符串（不可含 NUL）。")
    return value


def _strings(value: object, label: str, *, empty: bool = True) -> list[str]:
    if not isinstance(value, list) or (not empty and not value):
        raise ValueError(label + " 必须是字符串数组。")
    for item in value:
        _text(item, label + "[]")
    return value


def _absolute(value: object, label: str) -> str:
    text = _text(value, label)
    if not (PurePosixPath(text).is_absolute() or PureWindowsPath(text).is_absolute()):
        raise ValueError(label + " 必须是绝对路径。")
    return text


def _engine(root: object = None) -> list[str]:
    root = root if root is not None else os.environ.get("NOVEL_LEDGER")
    if root is None:
        raise ValueError("用 --engine 目录或 NOVEL_LEDGER 指明可信引擎；不从 JSON 接受命令。")
    root = Path(_absolute(str(root), "engine_root")).resolve()
    script = root / "scripts" / "novel.py"
    if not script.is_file():
        raise ValueError("引擎入口不存在：" + str(script))
    return [sys.executable, str(script)]


def plan(request: object, *, engine_root: object = None) -> dict:
    """Return a data-only regroup plan, or a no-command stop outcome."""
    try:
        if not isinstance(request, dict):
            raise ValueError("输入必须是 JSON 对象。")
        missing = REQUIRED - request.keys()
        unknown = request.keys() - REQUIRED - OPTIONAL
        if missing or unknown:
            raise ValueError("字段不匹配：缺少=" + ",".join(sorted(missing)) +
                             "；未知=" + ",".join(sorted(unknown)))
        project = _absolute(request["project"], "project")
        gate = _text(request["gate"], "gate")
        if gate not in GATES:
            raise ValueError("gate 必须是当前十三门的门 ID。")
        board = _text(request["board_hash"], "board_hash")
        if not re.fullmatch(r"[0-9a-f]{64}", board):
            raise ValueError("board_hash 必须是引擎返回的 64 位小写十六进制哈希；不得自行生成。")
        if request["decision_kind"] not in ("author", "delegated"):
            raise ValueError("decision_kind 必须是 author 或 delegated。")
        source = _text(request["source_quote"], "source_quote", empty=True)
        if type(request["authority_covers_refinement"]) is not bool:
            raise ValueError("authority_covers_refinement 必须是布尔值。")
        changed = _strings(request["changes_confirmed"], "changes_confirmed")
        if not set(changed) <= CONFIRMED_FIELDS:
            raise ValueError("changes_confirmed 仅接受 mainline/style/target/scope。")
        rejected = _strings(request["rejection_reasons"], "rejection_reasons", empty=False)
        retained = _strings(request["retain"], "retain")
        requirements = _strings(request["requirements"], "requirements")
        proposed = _text(request["self_proposed"], "self_proposed") if "self_proposed" in request else None
        owner = _text(request["owner"], "owner") if "owner" in request else None
        if not requirements and proposed is None:
            raise ValueError("requirements 与 self_proposed 至少有一项提供具体新要求。")
        count = request["prior_custom_regroups"]
        if type(count) is not int or count < 0:
            raise ValueError("prior_custom_regroups 必须是非负整数（不是布尔值）。")
        for item in retained:
            if re.fullmatch(r"\s*(?:保留)?(?:旧组|原案|方案)?[A-Za-z0-9]+(?:号|案|方案)?(?:的)?(?:优点|优势|设定|全部|其他|其余)?\s*[。！!]?", item):
                raise ValueError("retain 必须具体写出保留的机制/字段，不能只说“保留 B 的优点”。")
    except (ValueError, TypeError) as exc:
        return _result("invalid", str(exc))

    if not source.strip() or not request["authority_covers_refinement"] or changed:
        return _result("needs_author", "授权缺失/不覆盖本次细化，或将改变已确认主线、风格、目标、范围；保留当前板面并先取明确决定。")
    if gate == "scale":
        return _result("unsupported", "scale 是系统档位门，不接受自拟方案回执或按自由要求生成新档位；核对现有 t0～t5，获授权后使用现有 choose --tier 路径。",
                       next_steps=["读取引擎当前档位板与 t0～t5 的实际范围，不根据自由输入编造档位或数字。",
                                   "授权不足或需求超出现有档位能力时保留板面，说明限制并报告用户。",
                                   "需求可由真实已有档位满足且已获准确授权时，交回现有 choose --tier 路径；regroup 仅滑动档位窗口，不生成自定义档位。"])
    if count >= MAX_CUSTOM_REGROUPS:
        return _result("stopped", "本门自定义换组累计已达两轮上限；保留当前板面、历次要求与不满意原因并报告，不换会话/换 board 清零。")
    try:
        prefix = _engine(engine_root)
    except (OSError, ValueError) as exc:
        return _result("invalid", str(exc))

    sections = ["【决定来源】\n类型：" + request["decision_kind"] + "\n原话（逐字保留）：\n" + source,
                "【本组拒绝原因】\n" + "\n".join("- " + item for item in rejected),
                "【必须保留】\n" + ("\n".join("- " + item for item in retained) if retained else "- 无额外保留项；此前已确认选择不变。"),
                "【新要求】\n" + ("\n".join("- " + item for item in requirements) if requirements else "- 见下列自拟候选要求。")]
    if proposed is not None:
        sections.append("【自拟候选要求（不是已选项）】\n" + proposed)
    sections.append("【执行边界】\n只细化当前门，不推翻已确认选择；按本门合法字段生成2～3个有实质差异的候选。\n"
                    "自拟文本也是候选要求，仍须 check/submit、展示新板面后 choose 真实选项ID；不能直接 choose 自由文本。\n"
                    "本门要求不会自动成为跨门或全书持久约束，须落实进合法 value 并核对后续一致性。")
    reason = "\n\n".join(sections)
    return _result("planned", "已生成只读规划；尚未执行 regroup，也未证明输入声明属实。",
                   argv=[*prefix, "--project", project, *(["--owner", owner] if owner is not None else []),
                         "regroup", "--board", board, "--reason", reason],
                   reason=reason, custom_regroup_number=count + 1,
                   next_steps=["调用方核对输入声明后，按 argv 数组执行 regroup（不拼 shell 字符串）。",
                               "advance --compact 取真实 opening_options 任务，重新 read 必读记录并按模板生成候选。",
                               "check 后 submit；成功后读取并原样展示新 board/question。",
                               "在有效授权内 choose 新板面真实 ID 并留痕；旧哈希和自拟自由文本不能当选项。",
                               "如仍不满意累计本门次数；两轮后保留现场报告用户。"])


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 字段重复：" + key)
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", help="请求 JSON 文件；省略则读 stdin。")
    parser.add_argument("--engine", help="可信 novel-ledger 引擎目录；缺省用 NOVEL_LEDGER。")
    args = parser.parse_args()
    try:
        raw = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
        request = json.loads(raw, object_pairs_hook=_unique_object)
        result = plan(request, engine_root=args.engine)
    except (OSError, UnicodeError, ValueError) as exc:
        result = _result("invalid", str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "invalid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
