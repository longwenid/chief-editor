#!/usr/bin/env python3
"""只读检查总编证据记录；不执行引擎、联网、取正文或证明文学质量。"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath

TYPES = {"market_snapshot", "taste_comparison", "selection_decision", "postmortem"}
KINDS = {"official_market", "repost", "public_text", "worker_report", "engine_state", "author_message", "reader_data"}
ROLES = {"head", "rising", "ordinary", "dropout"}
VERDICTS = {"A", "B", "tie", "insufficient", "incomparable"}
COMMON = {"schema_version", "record_type", "record_id", "created_at", "sources", "synthetic"}
EXTRA = {
    "market_snapshot": {"cohorts", "observations", "missing_roles", "claims"},
    "taste_comparison": {"comparability", "pair", "review", "findings", "counterexample", "context_after_review", "template_deviation"},
    "selection_decision": {"decision_status", "control", "candidates", "chosen", "basis", "resolution", "predictions", "long_form_refs"},
    "postmortem": {"selection_record_id", "results", "market_fit", "lesson", "long_form_refs"},
}


class EvidenceError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise EvidenceError(message)


def text(value, label):
    need(isinstance(value, str) and bool(value.strip()), f"{label} 必须是非空文字")
    return value


def obj(value, label):
    need(isinstance(value, dict), f"{label} 必须是对象")
    return value


def array(value, label, nonempty=False):
    need(isinstance(value, list) and (bool(value) or not nonempty), f"{label} 必须是{'非空' if nonempty else ''}数组")
    return value


def choice(value, values, label):
    need(value in values if isinstance(value, str) else False, f"{label} 须为 {','.join(sorted(values))}")
    return value


def number(value, label):
    need(type(value) in (int, float) and (isinstance(value, int) or math.isfinite(value)), f"{label} 必须是有限数字")
    return value


def integer(value, label, minimum=0):
    need(isinstance(value, int) and not isinstance(value, bool) and value >= minimum, f"{label} 必须是至少 {minimum} 的整数")
    return value


def timestamp(value, label):
    text(value, label)
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise EvidenceError(f"{label} 不是 ISO 时间") from None
    need(result.tzinfo is not None and result.utcoffset() is not None, f"{label} 必须含时区")
    return result


def no_false_authority(value, path="record"):
    if isinstance(value, dict):
        for key, item in value.items():
            need(isinstance(key, str), f"{path} 的字段名必须是字符串")
            need(not (key in {"score", "rating", "total_score", "template_compliance"} or key.endswith(("_score", "_rating"))), f"{path}.{key}：禁止伪总分或模板合规评分")
            need(key not in {"text", "prose", "chapter_text", "story_facts", "novel_facts", "world_model", "fact_ledger"}, f"{path}.{key}：只存位置/报告引用，不新增正文或小说事实账本")
            no_false_authority(item, path + "." + key)
    elif isinstance(value, list):
        for item in value:
            no_false_authority(item, path)
    elif isinstance(value, float):
        need(math.isfinite(value), f"{path}：禁止 NaN/Infinity")


def unique(items, key, label):
    result = {}
    for item in items:
        obj(item, label)
        identity = text(item.get(key), label + "." + key)
        need(identity not in result, f"{label} 的 {identity} 重复")
        result[identity] = item
    return result


def common(record):
    obj(record, "record")
    no_false_authority(record)
    need(type(record.get("schema_version")) is int and record["schema_version"] == 1, "schema_version 必须为 1")
    kind = choice(record.get("record_type"), TYPES, "record_type")
    need(not (set(record) - COMMON - EXTRA[kind]), "含未定义顶层字段：" + ",".join(sorted(set(record) - COMMON - EXTRA[kind])))
    text(record.get("record_id"), "record_id")
    created = timestamp(record.get("created_at"), "created_at")
    need(isinstance(record.get("synthetic", False), bool), "synthetic 必须为布尔值")
    sources = unique(array(record.get("sources"), "sources"), "source_id", "sources")
    for source in sources.values():
        if source.get("origin_id") is None:
            text(source.get("origin_missing_reason"), "source.origin_missing_reason")
        else:
            origin = text(source.get("origin_id"), "source.origin_id（真实上游而非转载页）")
            need(origin.strip().lower() not in {"unknown", "none", "null", "tbd", "未记录", "未知"}, "未知上游用 null 并写缺失原因，不伪造 origin_id")
        ref = text(source.get("ref"), "source.ref")
        choice(source.get("kind"), KINDS, "source.kind")
        need(timestamp(source.get("observed_at"), "source.observed_at") <= created, "来源观察时间不能晚于记录生成时间")
        need(record.get("synthetic", False) or not ref.startswith("synthetic:"), "合成来源不能冒充真实观察")
    return sources


def source_refs(ids, sources, label, allowed=None, nonempty=True):
    values = array(ids, label, nonempty)
    for identity in values:
        text(identity, label)
        need(identity in sources, f"{label} 引用了不存在的 source_id：{identity}")
        if allowed:
            need(sources[identity]["kind"] in allowed, f"{label} 来源类型错误，不能用热度/名气冒充文本或读者数据")
    return values


def metric(value, label):
    value = obj(value, label)
    for key in ("name", "unit"):
        text(value.get(key), label + "." + key)
    if value.get("denominator") is None:
        text(value.get("denominator_missing_reason"), label + ".denominator_missing_reason")
    else:
        text(value.get("denominator"), label + ".denominator")
    return value


def market(record, sources):
    cohorts = unique(array(record.get("cohorts"), "cohorts"), "cohort_id", "cohorts")
    for cohort in cohorts.values():
        for key in ("platform", "business_model", "stage", "audience"):
            text(cohort.get(key), "cohort." + key)
        metric(cohort.get("metric"), "cohort.metric")
        text(cohort["metric"].get("window"), "cohort.metric.window")
    observations = unique(array(record.get("observations"), "observations"), "observation_id", "observations")
    present = set()
    for observation in observations.values():
        need(observation.get("cohort_id") in cohorts, "observation.cohort_id 不存在")
        text(observation.get("work_id"), "observation.work_id（作品或固定聚合序列）")
        present.add(choice(observation.get("role"), ROLES, "observation.role"))
        at = timestamp(observation.get("at"), "observation.at")
        need(at <= timestamp(record["created_at"], "created_at"), "观察时点不能晚于记录")
        number(observation.get("value"), "observation.value")
        for identity in source_refs(observation.get("source_ids"), sources, "observation.source_ids", {"official_market", "repost", "reader_data"}):
            need(at <= timestamp(sources[identity]["observed_at"], "source.observed_at"), "来源不能提供尚未发生的观察")
        exposure = obj(observation.get("exposure"), "observation.exposure")
        choice(exposure.get("state"), {"stable", "changed", "unknown"}, "exposure.state")
        text(exposure.get("detail"), "exposure.detail")
    missing = obj(record.get("missing_roles"), "missing_roles")
    need(not (set(missing) - ROLES), "missing_roles 含未知样本角色")
    for role in ROLES - present:
        text(missing.get(role), "缺失样本须明确原因：" + role)
    need(not (set(missing) & present), "已有样本角色不能同时声明缺失")
    for claim in unique(array(record.get("claims"), "claims"), "claim_id", "claims").values():
        obj(claim, "claim")
        text(claim.get("claim_id"), "claim.claim_id")
        kind = choice(claim.get("kind"), {"fact", "inference", "hypothesis"}, "claim.kind")
        claim_type = choice(claim.get("claim_type"), {"observation", "trend"}, "claim.claim_type")
        scope = choice(claim.get("scope"), {"sample", "market"}, "claim.scope")
        status = choice(claim.get("status"), {"supported", "tentative", "unverified"}, "claim.status")
        text(claim.get("statement"), "claim.statement")
        ids = array(claim.get("evidence_ids"), "claim.evidence_ids")
        need(all(isinstance(i, str) and i in observations for i in ids), "claim 引用不存在的 observation_id")
        need(kind != "hypothesis" or status != "supported", "待验假设不能写成 supported")
        need(kind not in {"fact", "inference"} or bool(ids), "事实/推断不能无证据；纯设想须标 hypothesis")
        need(status != "supported" or bool(ids), "supported 断言不能无证据")
        if claim_type == "trend":
            choice(claim.get("direction"), {"up", "down", "stable"}, "trend.direction")
        if status == "supported" and (claim_type == "trend" or len(ids) > 1):
            points = [observations[i] for i in ids]
            need(len({p["cohort_id"] for p in points}) == 1, "不可比队列不能硬比较；降为 tentative/unverified")
            if claim_type == "trend":
                times = {timestamp(p["at"], "observation.at") for p in points}
                need(len(times) >= 2, "trend 须有两个实际不同时点")
                need(len({p["work_id"] for p in points}) == 1, "trend 须为同一作品或固定聚合序列，不能拿不同作品顶替纵向变化")
                cohort = cohorts[points[0]["cohort_id"]]
                need(cohort["metric"].get("denominator") is not None, "分母未知，trend 不能 supported")
                need(all(p["exposure"]["state"] == "stable" for p in points), "曝光改变/未知，trend 须降级而不能硬推市场变化")
                values = {}
                for point in points:
                    at = timestamp(point["at"], "observation.at")
                    need(at not in values or values[at] == point["value"], "同一序列同一时点出现冲突数值，不能 supported")
                    values[at] = point["value"]
                first, last = values[min(values)], values[max(values)]
                direction = "up" if last > first else "down" if last < first else "stable"
                need(claim["direction"] == direction, "trend 方向与实际观测首尾相反")
        if status == "supported" and scope == "market":
            need(claim_type != "trend", "市场级趋势须 tentative；本模块只支持明确口径内的样本/固定聚合观测，不证明市场代表性")
            roles = {observations[i]["role"] for i in ids}
            need(roles == ROLES, "市场结论的证据自身须覆盖四类样本，不能用无关观察凑覆盖")
        if status == "supported" and (scope == "market" or claim.get("independent_support") is True):
            origins = {sources[s]["origin_id"] for i in ids for s in observations[i]["source_ids"] if sources[s].get("origin_id")}
            need(len(origins) >= 2, "同源转载不构成独立双源支持")


def text_finding(finding, sources, label):
    obj(finding, label)
    source_refs([finding.get("source_id")], sources, label + ".source_id", {"public_text", "worker_report"})
    need(finding.get("basis") == "text", "审美依据只能是文本，热度/名气不能充当审美证据")
    for key in ("location", "mechanism", "experience", "cost", "boundary"):
        text(finding.get(key), label + "." + key)


def taste(record, sources):
    comparability = obj(record.get("comparability"), "comparability")
    status = choice(comparability.get("status"), {"comparable", "incomparable", "insufficient"}, "comparability.status")
    text(comparability.get("reason"), "comparability.reason")
    pair = unique(array(record.get("pair"), "pair", True), "label", "pair")
    need(set(pair) == {"A", "B"}, "pair 必须匿名标为 A/B，不带作者或榜位")
    for sample in pair.values():
        need(not (set(sample) - {"label", "source_id", "location", "genre", "length"}), "匿名样本不能携带身份/名气/榜位字段")
        source_refs([sample.get("source_id")], sources, "pair.source_id", {"public_text", "worker_report"})
        text(sample.get("location"), "pair.location")
        text(sample.get("genre"), "pair.genre")
        length = obj(sample.get("length"), "pair.length")
        number(length.get("value"), "pair.length.value")
        need(length["value"] > 0, "样本长度须为正")
        text(length.get("unit"), "pair.length.unit")
    review = obj(record.get("review"), "review")
    need(review.get("identity_hidden") is True and review.get("popularity_hidden") is True, "须声明匿名且隐藏热度后细读")
    first, repeat = review.get("first_order"), review.get("repeat_order")
    need(first in (["A", "B"], ["B", "A"]) and repeat == list(reversed(first)), "必须换序复评，不能原序抄结论")
    for key in ("first_verdict", "repeat_verdict", "final_verdict"):
        choice(review.get(key), VERDICTS, "review." + key)
    if review["first_verdict"] != review["repeat_verdict"] or review["final_verdict"] != review["repeat_verdict"]:
        text(review.get("recheck_note"), "换序结论变化须说明，不能掩盖不稳定")
    final = review["final_verdict"]
    if status != "comparable":
        need(final in {"insufficient", "incomparable"}, "不可比/观察不足时必须停判")
    else:
        band = obj(comparability.get("length_band"), "comparability.length_band")
        low, high = number(band.get("min"), "length_band.min"), number(band.get("max"), "length_band.max")
        need(0 < low <= high, "长度范围无效")
        unit = text(band.get("unit"), "length_band.unit")
        need(len({sample["genre"] for sample in pair.values()}) == 1, "类别不同应声明不可比")
        need(all(sample["length"]["unit"] == unit and low <= sample["length"]["value"] <= high for sample in pair.values()), "样本须在声明的同单位长度范围；否则不可比")
    findings = array(record.get("findings"), "findings")
    need(bool(findings) or final in {"insufficient", "incomparable"}, "明确审美结论须有逐条文本依据")
    for finding in findings:
        text_finding(finding, sources, "finding")
        label = choice(finding.get("label"), {"A", "B"}, "finding.label")
        need(finding["source_id"] == pair[label]["source_id"], "判断须指向对应匿名样本，而不是旁支热度来源")
    if final in {"A", "B", "tie"}:
        need({finding["label"] for finding in findings} == {"A", "B"}, "明确成对审美判断须有 A/B 两侧文本依据，不能只写一侧")
    counterexample = obj(record.get("counterexample"), "counterexample")
    counter_status = choice(counterexample.get("status"), {"observed", "missing"}, "counterexample.status")
    if counter_status == "observed":
        text_finding(counterexample, sources, "counterexample")
        text(counterexample.get("challenges"), "counterexample.challenges")
    else:
        text(counterexample.get("reason"), "counterexample.reason")
        need(final in {"insufficient", "incomparable"}, "反例未取得时不作确定审美判定")


def linked(record, ids, index, valid, expected, label):
    ids = array(ids, label)
    for identity in ids:
        need(isinstance(identity, str) and identity in valid and index[identity]["record_type"] == expected, f"{label} 须同时提供有效 {expected}：{identity}")
        need(record.get("synthetic", False) or not index[identity].get("synthetic", False), "合成记录不能支撑真实决策")
        need(timestamp(index[identity]["created_at"], "引用.created_at") <= timestamp(record["created_at"], "created_at"), "决策/复盘不能引用未来才产生的证据")
    return ids


def long_form(record, sources):
    source_refs(record.get("long_form_refs", []), sources, "long_form_refs", {"engine_state", "worker_report"}, False)


def selection(record, sources, index, valid):
    status = choice(record.get("decision_status"), {"chosen", "proposed", "pending_author"}, "decision_status")
    control = obj(record.get("control"), "selection.control（项目恢复元数据唯一源）")
    project_path = control.get("project_path")
    if project_path is None:
        need(status != "chosen", "已立项项目必须有绝对 project_path")
        text(control.get("project_path_reason"), "control.project_path_reason")
    else:
        text(project_path, "control.project_path")
        need(PurePosixPath(project_path).is_absolute() or PureWindowsPath(project_path).is_absolute(), "control.project_path 必须为绝对路径，不实际访问或创建")
    control_status = choice(control.get("status"), {"draft", "active", "delivered", "shelved"}, "control.status")
    need((status == "chosen") == (control_status != "draft"), "仅 chosen 的绝对路径项目可 active/delivered/shelved；proposed/pending_author 必须 draft")
    choice(control.get("selection_mode"), {"A", "B", "C"}, "control.selection_mode")
    for key in ("direction_fingerprint", "authorization_index", "author_quote"):
        text(control.get(key), "control." + key)
    decision_kind = choice(control.get("decision_kind"), {"author", "delegated"}, "control.decision_kind")
    source_refs([control.get("author_source_id")], sources, "control.author_source_id", {"author_message"})
    if decision_kind == "delegated":
        text(control.get("delegated_reason"), "control.delegated_reason（不混入作者原话）")
    candidates = unique(array(record.get("candidates"), "candidates", True), "candidate_id", "candidates")
    for candidate in candidates.values():
        text(candidate.get("proposal"), "candidate.proposal")
        text(candidate.get("increment"), "candidate.increment")
    if status == "chosen":
        chosen = text(record.get("chosen"), "chosen")
        need(chosen in candidates, "chosen 必须是已记录的 candidate_id")
    basis = obj(record.get("basis"), "basis")
    need(set(basis) == {"commercial_fit", "work_value", "author_preference"}, "商业适配、作品价值、作者偏好须分三栏")
    for key, record_type, ref_key in (("commercial_fit", "market_snapshot", "market_record_ids"), ("work_value", "taste_comparison", "taste_record_ids")):
        item = obj(basis.get(key), "basis." + key)
        validation = choice(item.get("status"), {"supported", "tentative", "unverified"}, key + ".status")
        text(item.get("conclusion"), key + ".conclusion")
        ids = linked(record, item.get(ref_key), index, valid, record_type, key + "." + ref_key)
        if validation == "supported":
            need(bool(ids), key + " supported 必须有相应证据记录")
            if key == "commercial_fit":
                need(any(c["status"] == "supported" for identity in ids for c in index[identity]["claims"]), "商业适配不能把待验市场假设升级为证据")
            else:
                need(any(index[identity]["review"]["final_verdict"] in {"A", "B", "tie"} for identity in ids), "作品价值不能把不足以判断升级为证据")
    preference = obj(basis.get("author_preference"), "author_preference")
    need(not (set(preference) - {"status", "quote", "source_id", "alignment"}), "作者偏好只记录已表达原话，不接受推定字段")
    expressed = choice(preference.get("status"), {"expressed", "not_expressed"}, "author_preference.status")
    if expressed == "not_expressed":
        need(not preference.get("quote") and not preference.get("source_id") and preference.get("alignment", "unknown") == "unknown", "未表达偏好不能推定或伪造原话")
    else:
        text(preference.get("quote"), "author_preference.quote（逐字）")
        source_refs([preference.get("source_id")], sources, "author_preference.source_id", {"author_message"})
        alignment = choice(preference.get("alignment"), {"aligned", "conflict", "unknown"}, "author_preference.alignment")
        if alignment == "conflict":
            if status == "chosen":
                resolution = obj(record.get("resolution"), "偏好冲突须有作者处置原话 resolution")
                text(resolution.get("quote"), "resolution.quote")
                source_refs([resolution.get("source_id")], sources, "resolution.source_id", {"author_message"})
            else:
                need(status == "pending_author", "偏好冲突须 pending_author，不能由热度或总编品味自动覆盖")
    predictions = unique(array(record.get("predictions"), "predictions", status == "chosen"), "prediction_id", "predictions")
    for prediction in predictions.values():
        text(prediction.get("statement"), "prediction.statement")
        window = obj(prediction.get("window"), "prediction.window")
        start, end = timestamp(window.get("start"), "prediction.window.start"), timestamp(window.get("end"), "prediction.window.end")
        need(timestamp(record["created_at"], "created_at") <= start < end, "预测必须先登记，观察窗在登记之后且起止有效")
        falsifier = obj(prediction.get("falsifier"), "prediction.falsifier")
        falsifier_kind = choice(falsifier.get("kind"), {"numeric", "qualitative"}, "falsifier.kind")
        if falsifier_kind == "numeric":
            metric(prediction.get("metric"), "prediction.metric")
            choice(falsifier.get("operator"), {"lt", "lte", "gt", "gte", "ne"}, "falsifier.operator")
            number(falsifier.get("threshold"), "falsifier.threshold")
        else:
            text(falsifier.get("condition"), "qualitative.condition（可观察的反证条件，不是质量总分）")
            need(not {"operator", "threshold"} & set(falsifier), "定性条件不夹带伪数值阈值")
        integer(prediction.get("minimum_observations"), "prediction.minimum_observations", 1)
        plan = obj(prediction.get("source_plan"), "prediction.source_plan")
        choice(plan.get("kind"), {"reader_data", "worker_report", "engine_state"}, "source_plan.kind")
        text(plan.get("ref"), "source_plan.ref")
    long_form(record, sources)


def postmortem(record, sources, index, valid):
    identity = record.get("selection_record_id")
    linked(record, [identity], index, valid, "selection_decision", "selection_record_id")
    predictions = {p["prediction_id"]: p for p in index[identity]["predictions"]}
    results = unique(array(record.get("results"), "results", True), "prediction_id", "results")
    need(set(results) == set(predictions), "须逐条复盘全部预登记预测，不能只挑成功项")
    reader_observed = False
    operators = {"lt": lambda a,b: a < b, "lte": lambda a,b: a <= b, "gt": lambda a,b: a > b, "gte": lambda a,b: a >= b, "ne": lambda a,b: a != b}
    for result in results.values():
        prediction = predictions[result["prediction_id"]]
        outcome = choice(result.get("outcome"), {"confirmed", "refuted", "unobserved", "pending"}, "result.outcome")
        attributions = array(result.get("attribution"), "result.attribution", True)
        need(all(a in {"judgment_error", "execution_deviation", "exposure_change", "insufficient_observation"} for a in attributions), "须区分判断错误/执行偏离/曝光变化/观察不足")
        text(result.get("explanation"), "result.explanation（归因证据与限度）")
        observation = obj(result.get("observation"), "result.observation")
        n = integer(observation.get("sample_size"), "observation.sample_size")
        refs = source_refs(observation.get("source_ids"), sources, "result.observation.source_ids", {"reader_data", "engine_state", "worker_report"}, False)
        if outcome in {"confirmed", "refuted"}:
            need(n >= prediction["minimum_observations"] and bool(refs), "观察不足不能确认/反证预测")
            at = timestamp(observation.get("at"), "observation.at")
            start, end = timestamp(prediction["window"]["start"], "window.start"), timestamp(prediction["window"]["end"], "window.end")
            need(start <= at <= end and timestamp(record["created_at"], "created_at") >= end, "结果须在预登记窗口观察且窗末后校准")
            expected_kind = prediction["source_plan"]["kind"]
            need(all(sources[s]["kind"] == expected_kind for s in refs), "不能用引擎通过替代原预测的读者数据")
            need(all(at <= timestamp(sources[s]["observed_at"], "source.observed_at") <= timestamp(record["created_at"], "created_at") for s in refs), "结果来源时间不成立")
            falsifier = prediction["falsifier"]
            if falsifier["kind"] == "numeric":
                value = number(observation.get("value"), "observation.value")
                refuted = operators[falsifier["operator"]](value, falsifier["threshold"])
            else:
                qualitative_observation(observation, refs, known=True)
                refuted = observation["condition_met"]
            need((outcome == "refuted") == refuted, "结果与预登记反证阈值矛盾，不能复盘时改判据")
            reader_observed |= expected_kind == "reader_data"
        else:
            need("insufficient_observation" in attributions, "未观察/待观察须标明观察不足")
            end = timestamp(prediction["window"]["end"], "window.end")
            need((outcome == "pending") == (timestamp(record["created_at"], "created_at") < end), "未到窗末用 pending；窗末后无数据用 unobserved")
            if n == 0:
                need(observation.get("value") is None and not refs, "零观察不能夹带数据结论")
            else:
                if prediction["falsifier"]["kind"] == "numeric":
                    number(observation.get("value"), "不充分观察.value")
                else:
                    qualitative_observation(observation, refs, known=False)
                need(bool(refs) and all(sources[s]["kind"] == prediction["source_plan"]["kind"] for s in refs), "不充分观察也须保留正确来源")
                at = timestamp(observation.get("at"), "不充分观察.at")
                need(timestamp(prediction["window"]["start"], "window.start") <= at <= min(end, timestamp(record["created_at"], "created_at")), "不充分观察须在登记窗口内")
                need(outcome == "pending" or n < prediction["minimum_observations"], "已到窗末且观察量足够，不能回避登记的反证条件")
    market_fit = choice(record.get("market_fit"), {"unverified", "observed"}, "market_fit")
    need(market_fit != "observed" or reader_observed, "没有真实读者数据，市场适配未验证")
    text(record.get("lesson"), "lesson")
    long_form(record, sources)


def qualitative_observation(observation, refs, *, known):
    need(observation.get("value") is None, "定性复盘不能折成伪精确数值")
    condition = observation.get("condition_met")
    need(isinstance(condition, bool) if known else condition is None, "定性反证须明确是否满足；观察不足时保留未知")
    text(observation.get("assessment"), "qualitative.assessment（人工/模型有据解释，不是机械证明）")
    for position in array(observation.get("locations"), "qualitative.locations", True):
        obj(position, "qualitative.location")
        need(position.get("source_id") in refs, "定性判断位置必须引用本次观察的报告/事实源")
        text(position.get("location"), "qualitative.location")


def validate_records(records):
    if not isinstance(records, (list, tuple)):
        return ["records 必须是记录数组"]
    errors, index, sources_by_id = [], {}, {}
    for position, record in enumerate(records, 1):
        try:
            sources = common(record)
            identity = record["record_id"]
            need(identity not in index, "record_id 重复：" + identity)
            index[identity], sources_by_id[identity] = record, sources
        except (EvidenceError, TypeError) as error:
            errors.append(f"记录 {position}：{error}")
    valid = set()
    for kind in ("market_snapshot", "taste_comparison", "selection_decision", "postmortem"):
        for identity, record in index.items():
            if record["record_type"] != kind:
                continue
            try:
                sources = sources_by_id[identity]
                if kind == "market_snapshot": market(record, sources)
                elif kind == "taste_comparison": taste(record, sources)
                elif kind == "selection_decision": selection(record, sources, index, valid)
                else: postmortem(record, sources, index, valid)
                valid.add(identity)
            except (EvidenceError, TypeError, KeyError) as error:
                errors.append(f"{identity}：{error}")
    return errors


def parse_record(content: str, *, markdown: bool = False) -> dict:
    """严格解析单一真源；供只读 CLI 及安全 fd writer 共用，不访问路径。"""
    text(content, "记录内容")
    need(len(content.encode("utf-8")) <= 1024 * 1024, "记录超过 1 MiB；不要传正文")
    if markdown:
        blocks = re.findall(r"^[ ]{0,3}```json[ \t]*\n(.*?)^[ ]{0,3}```[ \t]*$", content, flags=re.M | re.S)
        need(len(blocks) == 1, "Markdown 必须只有一个 JSON 证据块")
        content = blocks[0]

    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "JSON 重复字段：" + key)
            result[key] = value
        return result

    def finite(value):
        result = float(value)
        need(math.isfinite(result), "JSON 不接受 NaN/Infinity 或溢出浮点数")
        return result

    def constant(value):
        raise EvidenceError("JSON 不接受 " + value)

    try:
        record = json.loads(content, object_pairs_hook=pairs, parse_float=finite, parse_constant=constant)
    except (ValueError, OverflowError) as error:
        raise EvidenceError("JSON 无效：" + str(error)) from None
    obj(record, "record")
    return record


def load_record(path):
    path = Path(path)
    need(path.is_file() and path.suffix.lower() in {".json", ".md"}, f"只接受明确的 .json/.md 记录文件：{path}")
    need(path.stat().st_size <= 1024 * 1024, f"记录超过 1 MiB；不要传正文：{path}")
    return parse_record(path.read_text(encoding="utf-8"), markdown=path.suffix.lower() == ".md")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", nargs="*", help="明确传入相互引用的 JSON/Markdown 证据文件；不扫目录")
    args = parser.parse_args(argv)
    if not args.records:
        print("[NOT_CHECKED] 未提供证据实例；结构测试不能冒充实例或文学质量验收")
        return 2
    records, errors = [], []
    for path in args.records:
        try:
            records.append(load_record(path))
        except (EvidenceError, OSError, UnicodeError, json.JSONDecodeError) as error:
            errors.append(f"{path}：{error}")
    errors.extend(validate_records(records))
    if errors:
        print(f"[FAIL] 证据校验：{len(errors)} 处问题")
        for error in errors:
            print("  -", error)
        return 1
    synthetic = sum(record.get("synthetic", False) for record in records)
    print(f"[OK] {len(records)} 条证据记录结构/引用/可比性有效（其中 {synthetic} 条合成记录）；未证明原话真实性、文学质量或市场效果")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
