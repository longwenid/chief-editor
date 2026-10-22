"""Evidence guardrails with synthetic observations; no real novel or account access."""
from __future__ import annotations

import copy
import importlib.util
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("editorial_evidence", ROOT / "scripts/check_editorial_evidence.py")
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


def source(identity, kind, origin="origin:synthetic-panel", at="2026-10-02T12:00:00Z"):
    return {"source_id": identity, "origin_id": origin, "ref": "synthetic://" + identity, "observed_at": at, "kind": kind}


def base(kind, identity, created="2026-10-02T13:00:00Z"):
    return {"schema_version": 1, "record_type": kind, "record_id": identity, "created_at": created, "synthetic": True, "sources": []}


def minimal_market():
    record = base("market_snapshot", "market-demo")
    record["sources"] = [source("panel", "official_market")]
    record["cohorts"] = [{"cohort_id": "paid-new", "platform": "示例平台", "business_model": "paid", "stage": "new", "audience": "示例类型读者", "metric": {"name": "active_readers", "unit": "people", "denominator": "同一固定入组作品，非全市场", "window": "daily"}}]
    record["observations"] = [
        {"observation_id": "day1", "cohort_id": "paid-new", "work_id": "work-X", "role": "head", "at": "2026-10-01T12:00:00Z", "value": 100, "source_ids": ["panel"], "exposure": {"state": "stable", "detail": "合成固定曝光样本"}},
        {"observation_id": "day2", "cohort_id": "paid-new", "work_id": "work-X", "role": "head", "at": "2026-10-02T12:00:00Z", "value": 120, "source_ids": ["panel"], "exposure": {"state": "stable", "detail": "同一合成曝光条件"}},
    ]
    record["missing_roles"] = {"rising": "未取得上升层样本", "ordinary": "未取得普通层样本", "dropout": "未取得掉队层样本；不做市场泛化"}
    record["claims"] = [{"claim_id": "local-change", "kind": "inference", "claim_type": "trend", "direction": "up", "scope": "sample", "status": "supported", "statement": "该固定样本的观测人数上升；不能据此断言全市场偏好。", "evidence_ids": ["day1", "day2"]}]
    return record


def finding(label, source_id, location, mechanism):
    return {"label": label, "source_id": source_id, "basis": "text", "location": location, "mechanism": mechanism, "experience": "选择代价可被读者感知", "cost": "解释稍慢", "boundary": "只适用于本次场景与目标读者，不外推全书"}


def minimal_taste():
    record = base("taste_comparison", "taste-demo")
    record["sources"] = [source("blind-report", "worker_report", "origin:isolated-review")]
    record["comparability"] = {"status": "comparable", "reason": "同类决定场景；长度范围足以保留行动后果，不要求固定句式", "length_band": {"min": 300, "max": 900, "unit": "han"}}
    record["pair"] = [
        {"label": "A", "source_id": "blind-report", "location": "匿名材料A，第1场景，行1-30", "genre": "现实幻想", "length": {"value": 500, "unit": "han"}},
        {"label": "B", "source_id": "blind-report", "location": "匿名材料B，第1场景，行1-35", "genre": "现实幻想", "length": {"value": 650, "unit": "han"}},
    ]
    record["review"] = {"identity_hidden": True, "popularity_hidden": True, "first_order": ["A", "B"], "repeat_order": ["B", "A"], "first_verdict": "B", "repeat_verdict": "B", "final_verdict": "B"}
    record["findings"] = [finding("A", "blind-report", "A，行18-25", "声称牺牲，但后续行动未承受损失"), finding("B", "blind-report", "B，行23-35", "人物用行动损失而非解释兑现选择")]
    record["counterexample"] = {**finding("B", "blind-report", "B，行1-6", "开头密集回顾削弱当下张力"), "status": "observed", "challenges": "B也有信息拥堵，不能把行动兑现当成通用质量保证"}
    record["context_after_review"] = "完成换序后揭盲：A为热榜头部，B无榜位；此背景不改变上述文本判断。"
    record["template_deviation"] = "B没有三段打脸或句末钩子，本次仍因具体行动与代价被偏好；不为模板合规加分。"
    return record


def minimal_selection():
    record = base("selection_decision", "selection-demo", "2026-10-03T12:00:00Z")
    record["sources"] = [source("author", "author_message", "origin:conversation-message")]
    record.update({"decision_status": "chosen", "control": {"project_path": "/synthetic/books/editorial-demo", "status": "active", "selection_mode": "B", "direction_fingerprint": "现实幻想×承诺的行动代价", "authorization_index": "authorization.md#合成委托条目", "decision_kind": "delegated", "author_quote": "这次请你定方向，先作受控试验。", "author_source_id": "author", "delegated_reason": "在委托范围内选择B；理由不冒充作者原话"}, "candidates": [{"candidate_id": "B", "proposal": "候选B，先作受控试验", "increment": "用行动代价而非标签堆叠展开冲突"}], "chosen": "B", "basis": {
        "commercial_fit": {"status": "unverified", "conclusion": "暂无读者或充分市场证据，商业适配未验证", "market_record_ids": []},
        "work_value": {"status": "unverified", "conclusion": "尚未取得可比匿名细读，不冒充文学认可", "taste_record_ids": []},
        "author_preference": {"status": "not_expressed", "alignment": "unknown"}},
        "predictions": [{"prediction_id": "retention", "statement": "指定试读窗口内读者留存率达到0.2；这只测该受众的商业适配", "metric": {"name": "reader_retention", "unit": "ratio", "denominator": "完成相同曝光流程的100名试读者"}, "window": {"start": "2026-10-04T00:00:00Z", "end": "2026-10-10T23:59:59Z"}, "falsifier": {"kind": "numeric", "operator": "lt", "threshold": 0.2}, "minimum_observations": 100, "source_plan": {"kind": "reader_data", "ref": "经授权的同受众试读汇总；未试读则不评市场成败"}}], "long_form_refs": []})
    return record


def minimal_postmortem():
    record = base("postmortem", "postmortem-demo", "2026-10-11T12:00:00Z")
    record.update({"selection_record_id": "selection-demo", "results": [{"prediction_id": "retention", "outcome": "unobserved", "attribution": ["insufficient_observation"], "explanation": "作品尚未发布，也未开展授权试读；不能用引擎通过代替市场反馈", "observation": {"value": None, "sample_size": 0, "source_ids": [], "at": None}}], "market_fit": "unverified", "lesson": "市场适配未验证；等待真实同口径读者观察，不回填阈值。", "long_form_refs": []})
    return record


class EditorialEvidenceTests(unittest.TestCase):
    def good(self, *records):
        self.assertEqual([], evidence.validate_records(list(records)))

    def bad(self, message, *records):
        problems = evidence.validate_records(list(records))
        self.assertTrue(problems)
        self.assertTrue(any(message in problem for problem in problems), problems)

    def test_minimal_examples_are_valid(self):
        self.good(minimal_market(), minimal_taste(), minimal_selection(), minimal_postmortem())

    def test_documentation_examples_match_complete_synthetic_fixtures(self):
        content = (ROOT / "references/editorial-judgment.md").read_text(encoding="utf-8")
        blocks = re.findall(r"^```json\n(.*?)^```$", content, flags=re.M | re.S)
        records = [evidence.parse_record(block) for block in blocks]
        self.assertEqual([minimal_market(), minimal_taste(), minimal_selection(), minimal_postmortem()], records)
        self.good(*records)

    def test_unsupported_trend_is_rejected(self):
        record = minimal_market(); record["claims"][0]["evidence_ids"] = []
        self.bad("无证据", record)

    def test_one_snapshot_is_not_trend(self):
        record = minimal_market(); record["claims"][0]["evidence_ids"] = ["day1"]
        self.bad("两个实际不同时点", record)

    def test_equivalent_timezone_strings_are_same_instant(self):
        record = minimal_market(); record["observations"][1]["at"] = "2026-10-01T12:00:00+00:00"
        self.bad("两个实际不同时点", record)

    def test_observed_trend_direction_must_match_values(self):
        record = minimal_market(); record["claims"][0]["direction"] = "down"
        self.bad("方向与实际观测", record)

    def test_different_cohorts_cannot_be_forced_into_comparison(self):
        record = minimal_market(); second = copy.deepcopy(record["cohorts"][0]); second.update(cohort_id="free-mature", business_model="free", stage="mature")
        record["cohorts"].append(second); record["observations"][1]["cohort_id"] = "free-mature"
        self.bad("不可比队列", record)
        record["claims"][0]["status"] = "tentative"
        self.good(record)

    def test_different_books_cannot_replace_time_series(self):
        record = minimal_market(); record["observations"][1]["work_id"] = "another-book"
        self.bad("同一作品", record)

    def test_reposts_of_one_origin_are_not_independent_sources(self):
        record = minimal_market(); record["sources"].append(source("repost", "repost"))
        record["observations"][1]["source_ids"] = ["panel", "repost"]; record["claims"][0]["independent_support"] = True
        self.bad("同源转载", record)
        record["sources"][1]["origin_id"] = "origin:independent-reader-panel"
        self.good(record)

    def test_unknown_origin_is_explicit_and_not_counted_as_independent(self):
        record = minimal_market(); record["sources"].append(source("unknown", "repost", None))
        record["sources"][1]["origin_missing_reason"] = "转载未披露上游"
        record["observations"][1]["source_ids"] = ["panel", "unknown"]; record["claims"][0]["independent_support"] = True
        self.bad("同源转载", record)

    def test_missing_sample_roles_are_explicit(self):
        record = minimal_market(); del record["missing_roles"]["dropout"]
        self.bad("缺失样本须明确原因", record)

    def test_head_samples_cannot_be_generalized_to_market(self):
        record = minimal_market(); record["claims"][0]["scope"] = "market"
        self.bad("市场级趋势须 tentative", record)

    def test_unrelated_observations_cannot_pad_market_claim_coverage(self):
        record = minimal_market()
        for role in ("rising", "ordinary", "dropout"):
            point = copy.deepcopy(record["observations"][1])
            point.update(observation_id=role, role=role, work_id="unrelated-" + role)
            record["observations"].append(point)
        record["missing_roles"] = {}
        record["claims"][0]["scope"] = "market"
        self.bad("市场级趋势须 tentative", record)
        record["claims"][0]["claim_type"] = "observation"
        self.bad("证据自身须覆盖四类", record)

    def test_exposure_change_and_unknown_denominator_require_downgrade(self):
        for field in ("exposure", "denominator"):
            record = minimal_market()
            if field == "exposure": record["observations"][1]["exposure"]["state"] = "changed"
            else: record["cohorts"][0]["metric"].update(denominator=None, denominator_missing_reason="平台未披露分母")
            self.bad("trend", record)
            record["claims"][0]["status"] = "tentative"; self.good(record)

    def test_hypothesis_cannot_be_promoted_to_fact(self):
        record = minimal_market(); record["claims"][0]["kind"] = "hypothesis"
        self.bad("待验假设", record)

    def test_popularity_can_conflict_with_text_and_non_template_work_can_win(self):
        self.good(minimal_taste())

    def test_popularity_is_not_text_evidence(self):
        record = minimal_taste(); record["findings"][0]["basis"] = "popularity"
        self.bad("热度/名气", record)
        record = minimal_taste(); record["sources"][0]["kind"] = "official_market"
        self.bad("来源类型错误", record)

    def test_blinding_and_reverse_order_are_required(self):
        for field, value in (("identity_hidden", False), ("repeat_order", ["A", "B"])):
            record = minimal_taste(); record["review"][field] = value
            self.bad("匿名" if field == "identity_hidden" else "换序复评", record)

    def test_identity_cannot_leak_into_pair_metadata(self):
        record = minimal_taste(); record["pair"][0]["rank"] = 1
        self.bad("不能携带身份", record)

    def test_each_judgment_needs_location_mechanism_experience_cost_and_boundary(self):
        for field in ("location", "mechanism", "experience", "cost", "boundary"):
            record = minimal_taste(); del record["findings"][0][field]
            self.bad("finding." + field, record)

    def test_pair_winner_needs_evidence_for_both_sides(self):
        record = minimal_taste(); record["findings"] = record["findings"][:1]
        self.bad("A/B 两侧文本依据", record)

    def test_no_pseudo_total_or_template_compliance_bonus(self):
        for key in ("overall_score", "total_score", "template_compliance"):
            record = minimal_taste(); record[key] = 95
            self.bad("禁止伪总分", record)

    def test_incomparable_is_allowed_to_stop_judgment(self):
        record = minimal_taste(); record["comparability"].update(status="incomparable", reason="取样来自不同叙述任务，不能强比")
        record["pair"][1]["genre"] = "另一个类型"
        record["review"].update(first_verdict="incomparable", repeat_verdict="incomparable", final_verdict="incomparable")
        self.good(record)
        record["review"]["final_verdict"] = "A"; record["review"]["recheck_note"] = "仍强选A"
        self.bad("必须停判", record)

    def test_length_band_does_not_require_near_identical_length(self):
        record = minimal_taste(); record["pair"][1]["length"]["value"] = 850
        self.good(record)
        record["pair"][1]["length"]["value"] = 1200
        self.bad("长度范围", record)

    def test_missing_counterexample_allows_only_insufficient_judgment(self):
        record = minimal_taste(); record["counterexample"] = {"status": "missing", "reason": "反例材料未取得"}
        self.bad("反例未取得", record)
        record["review"].update(first_verdict="insufficient", repeat_verdict="insufficient", final_verdict="insufficient")
        self.good(record)

    def test_unexpressed_preference_is_unknown_not_inferred(self):
        record = minimal_selection(); record["basis"]["author_preference"]["quote"] = "作者应该偏好榜首"
        self.bad("未表达偏好", record)

    def test_expressed_preference_needs_user_quote_and_message_source(self):
        record = minimal_selection(); record["basis"]["author_preference"] = {"status": "expressed", "quote": "我想慢热，不要开局打脸", "source_id": "message", "alignment": "aligned"}
        self.bad("不存在的 source_id", record)
        record["sources"].append(source("message", "author_message"))
        self.good(record)

    def test_preference_conflict_cannot_be_overridden_by_market_or_taste(self):
        record = minimal_selection(); record["sources"].append(source("message", "author_message"))
        record["basis"]["author_preference"] = {"status": "expressed", "quote": "我想慢热，不要开局打脸", "source_id": "message", "alignment": "conflict"}
        self.bad("处置原话", record)
        record["decision_status"] = "pending_author"; record["control"]["status"] = "draft"; self.good(record)
        record["decision_status"] = "chosen"; record["control"]["status"] = "active"; record["resolution"] = {"quote": "这次按你提的快节奏试验，但只试三章", "source_id": "message"}
        self.good(record)

    def test_supporting_records_must_be_loaded_and_correct_type(self):
        record = minimal_selection(); record["basis"]["commercial_fit"].update(status="supported", market_record_ids=["market-demo"])
        self.bad("须同时提供有效", record)
        self.good(minimal_market(), record)
        record["basis"]["work_value"].update(status="supported", taste_record_ids=["market-demo"])
        self.bad("有效 taste_comparison", minimal_market(), record)

    def test_prediction_is_registered_before_window_and_falsifiable(self):
        record = minimal_selection(); record["predictions"][0]["window"]["start"] = "2026-10-01T00:00:00Z"
        self.bad("先登记", record)
        record = minimal_selection(); del record["predictions"][0]["falsifier"]
        self.bad("falsifier", record)

    def test_unpublished_postmortem_does_not_claim_market_validation(self):
        self.good(minimal_selection(), minimal_postmortem())
        record = minimal_postmortem(); record["market_fit"] = "observed"
        self.bad("市场适配未验证", minimal_selection(), record)

    def test_postmortem_requires_original_preregistration(self):
        self.bad("须同时提供有效 selection_decision", minimal_postmortem())

    def test_postmortem_cannot_cherry_pick_successful_predictions(self):
        selection = minimal_selection(); prediction = copy.deepcopy(selection["predictions"][0]); prediction["prediction_id"] = "another"
        selection["predictions"].append(prediction)
        self.bad("逐条复盘全部", selection, minimal_postmortem())

    def observed_postmortem(self, value=0.4, n=100):
        record = minimal_postmortem(); record["sources"] = [source("readers", "reader_data", at="2026-10-10T22:00:00Z")]
        record["market_fit"] = "observed"
        record["results"][0].update(outcome="confirmed", attribution=["judgment_error"], explanation="合成试读数据仅覆盖该受众；本项未被反证")
        record["results"][0]["observation"] = {"value": value, "sample_size": n, "source_ids": ["readers"], "at": "2026-10-10T21:00:00Z"}
        return record

    def test_actual_outcome_must_match_preregistered_falsifier(self):
        self.good(minimal_selection(), self.observed_postmortem())
        record = self.observed_postmortem(0.1); self.bad("反证阈值矛盾", minimal_selection(), record)
        record["results"][0]["outcome"] = "refuted"; self.good(minimal_selection(), record)

    def test_partial_observation_is_preserved_without_claiming_success(self):
        record = self.observed_postmortem(n=20); self.bad("观察不足", minimal_selection(), record)
        record["market_fit"] = "unverified"; record["results"][0].update(outcome="unobserved", attribution=["insufficient_observation"])
        self.good(minimal_selection(), record)

    def test_qualitative_narrative_promise_uses_worker_positions_without_scores(self):
        selection = minimal_selection()
        selection["predictions"][0] = {"prediction_id": "retention", "statement": "前30章的人物承诺应以行动代价兑现；不据此宣称文学质量", "window": {"start": "2026-10-04T00:00:00Z", "end": "2026-10-10T23:59:59Z"}, "falsifier": {"kind": "qualitative", "condition": "Worker审读前30章后，人物承诺仍只有口头声明，找不到承担行动代价的位置"}, "minimum_observations": 1, "source_plan": {"kind": "worker_report", "ref": "引擎已有审读任务的Worker报告，不由主干读正文"}}
        post = minimal_postmortem()
        post["sources"] = [source("promise-report", "worker_report", "origin:existing-engine-task", at="2026-10-10T22:00:00Z")]
        post["results"][0].update(outcome="refuted", attribution=["execution_deviation"], explanation="Worker定位到口头承诺，未定位行动代价；只反证此叙事承诺，未证明全书质量")
        post["results"][0]["observation"] = {"value": None, "condition_met": True, "assessment": "隔离Worker根据已有任务审读报告判断，仍需作者审美复核", "sample_size": 1, "source_ids": ["promise-report"], "at": "2026-10-10T21:00:00Z", "locations": [{"source_id": "promise-report", "location": "既有任务审读报告#前30章承诺兑现检查，第2项"}]}
        post["long_form_refs"] = ["promise-report"]
        self.good(selection, post)
        post["results"][0]["observation"]["locations"] = []
        self.bad("qualitative.locations", selection, post)

    def test_qualitative_condition_cannot_smuggle_numeric_quality_score(self):
        selection = minimal_selection()
        selection["predictions"][0]["falsifier"] = {"kind": "qualitative", "condition": "作品差", "threshold": 95}
        self.bad("伪数值阈值", selection)

    def test_engine_pass_cannot_replace_reader_data(self):
        record = self.observed_postmortem(); record["sources"][0]["kind"] = "engine_state"
        self.bad("不能用引擎通过替代", minimal_selection(), record)

    def test_no_new_novel_fact_ledger_and_no_main_thread_prose(self):
        for key in ("novel_facts", "world_model", "prose"):
            record = minimal_selection(); record[key] = "不允许的新正文/事实"
            self.bad("不新增正文或小说事实账本", record)

    def test_synthetic_evidence_cannot_support_real_selection(self):
        record = minimal_selection(); record["synthetic"] = False
        record["sources"][0]["ref"] = "conversation://message/author"
        record["basis"]["commercial_fit"].update(status="supported", market_record_ids=["market-demo"])
        self.bad("合成记录不能支撑真实", minimal_market(), record)

    def test_control_metadata_recovers_project_and_scope_without_duplicate_fields(self):
        record = minimal_selection(); self.good(record)
        record["control"]["project_path"] = "relative/project"
        self.bad("绝对路径", record)
        record["control"]["project_path"] = None
        self.bad("已立项项目", record)

    def test_pending_draft_cannot_enter_active_project_list(self):
        record = minimal_selection(); record["decision_status"] = "pending_author"
        self.bad("必须 draft", record)
        record["control"].update(status="draft", project_path=None, project_path_reason="等用户落定目录")
        self.good(record)

    def test_chosen_id_must_be_recorded_candidate(self):
        record = minimal_selection(); record["chosen"] = "never-shown"
        self.bad("candidate_id", record)

    def test_strict_parser_rejects_duplicate_fields_nan_and_infinity(self):
        for content in ('{"record_id":"first","record_id":"second"}', '{"v": NaN}', '{"v": Infinity}', '{"v": 1e99999}'):
            with self.subTest(content=content), self.assertRaises(evidence.EvidenceError):
                evidence.parse_record(content)

    def test_api_bad_keys_and_large_integers_return_friendly_errors(self):
        record = minimal_market(); record[1] = "bad key"
        self.bad("字段名必须是字符串", record)
        record = minimal_market(); record["observations"][0]["value"] = 10 ** 10000
        self.bad("方向与实际观测", record)
        self.assertTrue(evidence.validate_records(None))

    def test_unknown_top_level_fields_are_not_a_second_truth_channel(self):
        record = minimal_market(); record["trend"] = "无证据宣称增长"
        self.bad("未定义顶层字段", record)

    def test_cli_without_instances_is_not_checked_nonzero(self):
        output = io.StringIO()
        with redirect_stdout(output): code = evidence.main([])
        self.assertEqual(2, code); self.assertIn("NOT_CHECKED", output.getvalue())

    def test_markdown_has_one_evidence_block_and_directories_are_not_scanned(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "record.md"
            block = "```json\n" + json.dumps(minimal_market(), ensure_ascii=False) + "\n```\n"
            path.write_text("# 摘要仅展示，不另存字段\n" + block, encoding="utf-8")
            self.good(evidence.load_record(path))
            path.write_text(block + block, encoding="utf-8")
            with self.assertRaisesRegex(evidence.EvidenceError, "一个 JSON"):
                evidence.load_record(path)
            with self.assertRaisesRegex(evidence.EvidenceError, "明确的"):
                evidence.load_record(Path(temp))

    def test_reference_pointers_are_never_opened_or_executed(self):
        record = minimal_taste(); record["sources"][0]["ref"] = "file:///must-not-open-or-execute.py"
        self.good(record)


if __name__ == "__main__":
    unittest.main()
