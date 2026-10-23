#!/usr/bin/env python3
"""Plan one opening regroup or back from caller-verified declarations; never execute it.

Read a JSON object from stdin (or the optional JSON file), print a JSON plan to stdout.
This validates input shape and the declared finite regroup limit. It cannot establish
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

GATE_ORDER = (
    "genre", "premise", "voice", "scale", "world", "ladder", "origin", "edge",
    "protagonist", "relationships", "opposition", "payoff", "title",
)
GATES = frozenset(GATE_ORDER)
CONFIRMED_FIELDS = frozenset(("mainline", "style", "target", "scope"))
REQUIRED = frozenset((
    "project", "gate", "board_hash", "decision_kind", "source_quote",
    "authority_covers_refinement", "changes_confirmed", "rejection_reasons", "retain",
    "requirements", "prior_custom_regroups",
))
OPTIONAL = frozenset(("self_proposed", "owner", "confirmed_change_context",
                      "change_authorization", "regroup_extension"))
MAX_CUSTOM_REGROUPS = 2
LIMITATIONS = [
    "仅校验输入与技能治理条件，不证明授权原话真实性、授权范围、当前 board 或历史次数。",
    "调用方须核对当前项目/门/展示哈希及同一门历次台账；换会话或换 board 不清零。",
    "owner 若提供必须由调用方核对真实身份、项目与租约；规划器不生成 owner，也不 claim/run。",
    "两轮是默认治理上限；追加上限须核对本次用户原话及定位，历史次数不清零。",
    "已选门、决定来源和变更授权须由调用方对照引擎与原台账核实；声明不证明允许覆盖作者锁定项。",
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


def _object(value: object, label: str, keys: set[str], optional: set[str] | None = None) -> dict:
    if not isinstance(value, dict) or not keys <= value.keys() or value.keys() - keys - (optional or set()):
        raise ValueError(label + " 必须包含：" + ",".join(sorted(keys)) +
                         ("；可选：" + ",".join(sorted(optional)) if optional else "；不得有其他字段") + "。")
    return value


def _unique_fields(value: object, label: str) -> list[str]:
    fields = _strings(value, label)
    if len(fields) != len(set(fields)) or not set(fields) <= CONFIRMED_FIELDS:
        raise ValueError(label + " 只接受不重复的 mainline/style/target/scope。")
    return fields


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
    """Return one data-only command plan, or a no-command stop outcome."""
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
        changed = _unique_fields(request["changes_confirmed"], "changes_confirmed")
        context = request.get("confirmed_change_context")
        if context is not None:
            if not isinstance(context, list) or not changed:
                raise ValueError("confirmed_change_context 须为非空变更对应的数组。")
            context_fields = []
            for item in context:
                _object(item, "confirmed_change_context[]", {"field", "gate", "origin", "decision_ref"}, {"selection_method"})
                context_fields.append(_text(item["field"], "confirmed_change_context[].field"))
                previous_gate = _text(item["gate"], "confirmed_change_context[].gate")
                selection_method = item.get("selection_method", "choose")
                if selection_method not in ("choose", "intake"):
                    raise ValueError("selection_method 只接受 choose 或 intake，须与 decision_ref 的真实已选记录一致。")
                if previous_gate not in GATES or previous_gate == gate:
                    raise ValueError("变更对应的 gate 必须是真实已选门；当前待选门不能同时声明已选。")
                if GATE_ORDER.index(previous_gate) > GATE_ORDER.index(gate) and selection_method != "intake":
                    raise ValueError("后门不能仅凭门名声明已选；须明确 intake 来源并由 decision_ref 核对真实预填选择。")
                if item["origin"] not in ("author_locked", "editor_selected"):
                    raise ValueError("origin 只接受 author_locked 或 editor_selected。")
                _text(item["decision_ref"], "confirmed_change_context[].decision_ref")
            if len(context_fields) != len(set(context_fields)) or set(context_fields) != set(changed):
                raise ValueError("confirmed_change_context 必须逐项且完整匹配 changes_confirmed，不得重复。")
        change_auth = request.get("change_authorization")
        if change_auth is not None:
            _object(change_auth, "change_authorization", {"kind", "quote", "source_ref", "fields"})
            if not changed:
                raise ValueError("change_authorization 仅用于 changes_confirmed 非空的请求。")
            if change_auth["kind"] not in ("current_author_decision", "delegated_backtrack"):
                raise ValueError("change_authorization.kind 必须是 current_author_decision 或 delegated_backtrack。")
            _text(change_auth["quote"], "change_authorization.quote")
            _text(change_auth["source_ref"], "change_authorization.source_ref")
            if set(_unique_fields(change_auth["fields"], "change_authorization.fields")) != set(changed):
                raise ValueError("change_authorization.fields 必须精确覆盖本次 changes_confirmed。")
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
        extension = request.get("regroup_extension")
        limit = MAX_CUSTOM_REGROUPS
        if extension is not None:
            _object(extension, "regroup_extension", {"limit", "quote", "source_ref"})
            if changed:
                raise ValueError("回退请求不同时追加当前门换组额度；回退后按实际门与原累计次数另行规划 regroup。")
            limit = extension["limit"]
            if type(limit) is not int or limit <= MAX_CUSTOM_REGROUPS:
                raise ValueError("regroup_extension.limit 必须是大于默认两轮的有限整数总上限。")
            _text(extension["quote"], "regroup_extension.quote")
            _text(extension["source_ref"], "regroup_extension.source_ref")
        for item in retained:
            if re.fullmatch(r"\s*(?:保留)?(?:旧组|原案|方案)?[A-Za-z0-9]+(?:号|案|方案)?(?:的)?(?:优点|优势|设定|全部|其他|其余)?\s*[。！!]?", item):
                raise ValueError("retain 必须具体写出保留的机制/字段，不能只说“保留 B 的优点”。")
    except (ValueError, TypeError) as exc:
        return _result("invalid", str(exc))

    if changed:
        if not context or not change_auth:
            return _result("needs_author", "缺少已选门来源或覆盖准确变更的授权；先核对已有原话与台账，只有真实缺口才询问。")
        if change_auth["kind"] == "delegated_backtrack" and any(item["origin"] == "author_locked" for item in context):
            return _result("needs_author", "委托回退只覆盖总编受托选定项；本次涉及作者锁定项，须有作者明确变更决定。")
    elif not source.strip() or not request["authority_covers_refinement"]:
        return _result("needs_author", "授权缺失或不覆盖本次细化；先核对已有原话，仅就真实缺口取明确决定。")
    if not changed and gate == "scale":
        return _result("unsupported", "scale 是系统档位门，不接受自拟方案回执或按自由要求生成新档位；核对现有 t0～t5，获授权后使用现有 choose --tier 路径。",
                       next_steps=["读取引擎当前档位板与 t0～t5 的实际范围，不根据自由输入编造档位或数字。",
                                   "授权不足或需求超出现有档位能力时保留板面，说明限制并报告用户。",
                                   "需求可由真实已有档位满足且已获准确授权时，交回现有 choose --tier 路径；regroup 仅滑动档位窗口，不生成自定义档位。"])
    if not changed and count >= limit:
        return _result("stopped", "本门自定义换组累计已达有效上限；保留当前板面、历次要求与不满意原因并报告，不换会话/换 board 清零。",
                       custom_regroup_limit=limit, prior_custom_regroups=count)
    try:
        prefix = _engine(engine_root)
    except (OSError, ValueError) as exc:
        return _result("invalid", str(exc))

    command_kind = ("author" if change_auth["kind"] == "current_author_decision" else "delegated") if changed else request["decision_kind"]
    command_source = change_auth["quote"] if changed else source
    sections = ["【决定来源】\n类型：" + command_kind + "\n原话（逐字保留）：\n" + command_source,
                "【本组拒绝原因】\n" + "\n".join("- " + item for item in rejected),
                "【必须保留】\n" + ("\n".join("- " + item for item in retained) if retained else "- 无额外保留项；未获变更授权的已定内容不变。"),
                "【新要求】\n" + ("\n".join("- " + item for item in requirements) if requirements else "- 见下列自拟候选要求。")]
    if proposed is not None:
        sections.append("【自拟候选要求（不是已选项）】\n" + proposed)
    if changed:
        back_gate = min((item["gate"] for item in context), key=GATE_ORDER.index)
        if source.strip() and source != command_source:
            sections.append("【原请求来源（不替代本次变更授权）】\n" + source)
        sections.append("【准确变更与来源】\n" + "\n".join(
            "- " + item["field"] + "：" + item["gate"] + "；" + item["origin"] +
            "；选择入口=" + item.get("selection_method", "choose") + "；原决定=" + item["decision_ref"]
            for item in context))
        sections.append("【变更授权】\n类型：" + command_kind + "\n定位：" + change_auth["source_ref"] +
                        "\n覆盖字段：" + ", ".join(change_auth["fields"]) + "\n原话（逐字保留）：\n" + change_auth["quote"])
        sections.append("【执行边界】\n回退到最早受影响门 " + back_gate + "，由真实 back 归档该门及后续依赖选择；不能用当前门 regroup 偷改前门。\n"
                        "回退后 advance 返回最早未选门，可能早于 back_gate；按实际返回取任务/板面并按门序生成、核验候选，只用新哈希和真实选项。\n"
                        "不在获授权变更范围内的原决定仍须保留；各门历次自定义换组次数不因 back 清零。")
        reason = "\n\n".join(sections)
        return _result("planned", "已生成只读回退规划；核对原决定、授权覆盖与当前状态后执行，不需重复索取已有决定。",
                       action="back", back_gate=back_gate, command_decision_kind=command_kind,
                       argv=[*prefix, "--project", project, *(["--owner", owner] if owner is not None else []),
                             "back", "--gate", back_gate, "--reason", reason],
                       reason=reason, prior_custom_regroups=count,
                       next_steps=["核对每个 decision_ref 的当前有效已选记录、选择入口及变更授权；intake 预填可核对 author:<gate> 与空 board_hash。约定已激活须转 recontract。",
                                   "按 argv 执行 back 并记录实际返回；此前当前板面与受影响后门选择不再可用。",
                                   "advance 返回最早未选门，可能仍是 genre 而非 back_gate；按实际返回取任务或系统板。back 原因不自动成为 opening_rejections，须从现有台账带入变更与保留要求，逐门继续。",
                                   "从原台账恢复各门累计次数；回退不新增换组次数，也不清零历史；后续 regroup 重新规划。"])
    if extension is not None:
        sections.append("【追加换组上限】\n累计总上限：" + str(limit) + "；此前累计：" + str(count) +
                        "\n本次作者消息定位：" + extension["source_ref"] + "\n原话（逐字保留）：\n" + extension["quote"])
    sections.append("【执行边界】\n只细化当前门，不推翻已确认选择；按本门合法字段生成2～3个有实质差异的候选。\n"
                    "自拟文本也是候选要求，仍须 check/submit、展示新板面后 choose 真实选项ID；不能直接 choose 自由文本。\n"
                    "本门要求不会自动成为跨门或全书持久约束，须落实进合法 value 并核对后续一致性。")
    reason = "\n\n".join(sections)
    return _result("planned", "已生成只读规划；尚未执行 regroup，也未证明输入声明属实。",
                   action="regroup", command_decision_kind=request["decision_kind"],
                   argv=[*prefix, "--project", project, *(["--owner", owner] if owner is not None else []),
                         "regroup", "--board", board, "--reason", reason],
                   reason=reason, custom_regroup_number=count + 1, custom_regroup_limit=limit,
                   next_steps=["调用方核对输入声明后，按 argv 数组执行 regroup（不拼 shell 字符串）。",
                               "advance --compact 取真实 opening_options 任务，重新 read 必读记录并按模板生成候选。",
                               "check 后 submit；成功后核对新 board/question。亲选原样展示等待；委托在有效范围内自行决定并继续。",
                               "在有效授权内 choose 新板面真实 ID 并留痕；旧哈希和自拟自由文本不能当选项。",
                               "如仍不满意累计本门次数；达到有效有限上限后保留现场报告用户。"])


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
