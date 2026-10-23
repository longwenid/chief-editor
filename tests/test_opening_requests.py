"""The custom-request planner produces data only, never an engine invocation."""
from __future__ import annotations

import copy
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "plan_opening_request", Path(__file__).resolve().parents[1] / "scripts" / "plan_opening_request.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def request():
    return {
        "project": "/books/测试 项目", "gate": "premise", "board_hash": "a" * 64,
        "decision_kind": "delegated", "source_quote": "这些门由总编帮我选，保持已定方向。",
        "authority_covers_refinement": True, "changes_confirmed": [],
        "rejection_reasons": ["三案都靠提升战力解决规则争议。"], "retain": [],
        "requirements": ["改用公开可争辩的制度规则推动博弈，保留已有题材。"],
        "prior_custom_regroups": 0,
    }


def back_request(*, origin="editor_selected", kind="delegated_backtrack"):
    data = request()
    data.update(gate="world", changes_confirmed=["style"],
                confirmed_change_context=[{"field": "style", "gate": "voice", "origin": origin,
                                           "decision_ref": "authorization.md#voice-choice"}],
                change_authorization={"kind": kind, "quote": "本书由总编决定，包括回退修改自己此前代选的讲述方式。",
                                      "source_ref": "conversation:message-7", "fields": ["style"]})
    return data


class OpeningRequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.engine = Path(cls.temp.name) / "engine"
        (cls.engine / "scripts").mkdir(parents=True)
        (cls.engine / "scripts" / "novel.py").write_text("# never executed\n", encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def plan(self, data):
        return MODULE.plan(data, engine_root=self.engine)

    def assertNoCommand(self, result, status):
        self.assertEqual(result["status"], status, result)
        self.assertNotIn("argv", result)

    def test_all_unsatisfied_produces_regroup_bound_to_exact_board(self):
        data = request()
        result = self.plan(data)
        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["argv"][:8], [sys.executable, str(self.engine.resolve() / "scripts" / "novel.py"), "--project",
                                              data["project"], "regroup", "--board", "a" * 64, "--reason"])
        self.assertEqual(result["argv"][8], result["reason"])
        self.assertIn(data["source_quote"], result["reason"])
        self.assertEqual(result["verification_scope"], "input_validation_only")

    def test_partial_retain_spells_out_content_not_only_old_option(self):
        data = request()
        data["retain"] = ["资源按使用风险计税，公开账本允许当事人质证。"]
        result = self.plan(data)
        self.assertEqual(result["status"], "planned")
        self.assertIn(data["retain"][0], result["reason"])
        data["retain"] = ["保留B的优点"]
        self.assertNoCommand(self.plan(data), "invalid")

    def test_self_proposed_is_only_a_next_round_candidate_requirement(self):
        data = request()
        data["self_proposed"] = "登记权能公开转让，但登记者必须承担旧债。"
        data["requirements"] = []
        result = self.plan(data)
        self.assertEqual(result["status"], "planned")
        self.assertIn(data["self_proposed"], result["reason"])
        self.assertIn("不是已选项", result["reason"])
        self.assertEqual(result["argv"][4], "regroup")
        self.assertNotIn("--option", result["argv"])
        self.assertNotIn("--text", result["argv"])
        self.assertIn("check/submit", result["reason"])

    def test_insufficient_authority_has_no_command(self):
        for update in ({"authority_covers_refinement": False}, {"source_quote": "  "}):
            data = request()
            data.update(update)
            self.assertNoCommand(self.plan(data), "needs_author")

    def test_legacy_changes_without_provenance_remain_conservative(self):
        for field in ("mainline", "style", "target", "scope"):
            data = request()
            data["changes_confirmed"] = [field]
            self.assertNoCommand(self.plan(data), "needs_author")

    def test_delegated_reconsideration_backs_to_original_gate_not_regroup(self):
        data = back_request()
        data["owner"] = "real-owner-from-current-project"
        result = self.plan(data)
        self.assertEqual((result["status"], result["action"], result["back_gate"]), ("planned", "back", "voice"))
        self.assertEqual(result["argv"][4:11], ["--owner", data["owner"], "back", "--gate", "voice", "--reason", result["reason"]])
        self.assertNotIn("--board", result["argv"])
        self.assertNotIn("regroup", result["argv"])
        self.assertEqual(result["command_decision_kind"], "delegated")
        self.assertIn(data["change_authorization"]["quote"], result["reason"])
        self.assertIn(data["confirmed_change_context"][0]["decision_ref"], result["reason"])
        self.assertFalse(result["authorization_verified"])
        self.assertFalse(result["history_verified"])

    def test_delegated_reconsideration_cannot_override_author_lock(self):
        self.assertNoCommand(self.plan(back_request(origin="author_locked")), "needs_author")

    def test_current_author_can_change_intake_voice_while_genre_is_unselected(self):
        data = back_request(origin="author_locked", kind="current_author_decision")
        data["gate"] = "genre"
        data["confirmed_change_context"][0].update(selection_method="intake", decision_ref="engine:selections/author:voice")
        data["change_authorization"]["quote"] = "把我预填的第一人称改成第三人称限知，其余继续。"
        result = self.plan(data)
        self.assertEqual((result["status"], result["action"], result["back_gate"]), ("planned", "back", "voice"))
        self.assertEqual(result["argv"][4:8], ["back", "--gate", "voice", "--reason"])
        self.assertIn("选择入口=intake", result["reason"])
        self.assertTrue(any("最早未选门" in step and "genre" in step for step in result["next_steps"]))
        data["change_authorization"]["kind"] = "delegated_backtrack"
        self.assertNoCommand(self.plan(data), "needs_author")

    def test_unselected_future_or_current_gate_cannot_masquerade_as_intake_choice(self):
        data = back_request(kind="current_author_decision")
        data["gate"] = "genre"
        self.assertNoCommand(self.plan(data), "invalid")
        data["confirmed_change_context"][0]["selection_method"] = "intake"
        data["confirmed_change_context"][0]["decision_ref"] = ""
        self.assertNoCommand(self.plan(data), "invalid")
        data["confirmed_change_context"][0].update(gate="genre", decision_ref="engine:selections/author:genre")
        self.assertNoCommand(self.plan(data), "invalid")
        data["confirmed_change_context"][0].update(gate="voice", selection_method="automatic")
        self.assertNoCommand(self.plan(data), "invalid")

    def test_current_author_change_supplies_missing_change_authority_without_reasking(self):
        data = back_request(origin="author_locked", kind="current_author_decision")
        data["authority_covers_refinement"] = False
        data["source_quote"] = ""
        data["change_authorization"]["quote"] = "把我此前确定的第一人称改成第三人称限知，按这个决定重做视角门。"
        result = self.plan(data)
        self.assertEqual((result["status"], result["action"]), ("planned", "back"))
        self.assertEqual(result["command_decision_kind"], "author")
        self.assertIn(data["change_authorization"]["source_ref"], result["reason"])
        self.assertTrue(result["reason"].startswith("【决定来源】\n类型：author\n原话（逐字保留）：\n" + data["change_authorization"]["quote"]))

    def test_multiple_changes_back_to_earliest_gate_preserving_history(self):
        data = back_request()
        data["prior_custom_regroups"] = 2
        data["changes_confirmed"].append("mainline")
        data["confirmed_change_context"].append({"field": "mainline", "gate": "premise", "origin": "editor_selected",
                                                "decision_ref": "authorization.md#premise-choice"})
        data["change_authorization"]["fields"].append("mainline")
        result = self.plan(data)
        self.assertEqual(result["back_gate"], "premise")
        self.assertEqual(result["prior_custom_regroups"], 2)
        self.assertNotIn("custom_regroup_number", result)
        self.assertNotIn("--option", result["argv"])

    def test_missing_or_mismatched_backtrack_evidence_never_plans(self):
        for key in ("confirmed_change_context", "change_authorization"):
            data = back_request()
            del data[key]
            self.assertNoCommand(self.plan(data), "needs_author")
        for update in ({"fields": []}, {"fields": ["style", "style"]}, {"fields": ["mainline"]},
                       {"quote": " "}, {"source_ref": ""}, {"kind": "automatic"}):
            data = back_request()
            data["change_authorization"].update(update)
            self.assertNoCommand(self.plan(data), "invalid")
        for update in ({"gate": "world"}, {"gate": "title"}, {"gate": "unknown"},
                       {"origin": "unknown"}, {"decision_ref": ""}, {"field": "mainline"}):
            data = back_request()
            data["confirmed_change_context"][0].update(update)
            self.assertNoCommand(self.plan(data), "invalid")
        data = back_request()
        data["confirmed_change_context"].append(copy.deepcopy(data["confirmed_change_context"][0]))
        self.assertNoCommand(self.plan(data), "invalid")

    def test_changed_scale_gate_routes_back_but_scale_itself_stays_system_owned(self):
        data = back_request(kind="current_author_decision")
        data.update(changes_confirmed=["target"], confirmed_change_context=[
            {"field": "target", "gate": "scale", "origin": "author_locked", "decision_ref": "authorization.md#scale-choice"}])
        data["change_authorization"].update(fields=["target"], quote="改成短篇，请重新选真实体量档。")
        result = self.plan(data)
        self.assertEqual((result["action"], result["back_gate"]), ("back", "scale"))
        data = request()
        data.update(gate="scale", regroup_extension={"limit": 4, "quote": "再给两轮。", "source_ref": "conversation:message-8"})
        self.assertNoCommand(self.plan(data), "unsupported")

    def test_explicit_finite_extension_continues_count_and_stops_at_new_limit(self):
        data = request()
        data.update(prior_custom_regroups=2, regroup_extension={
            "limit": 4, "quote": "本门再给总编两轮换组额度，累计最多四轮。", "source_ref": "conversation:message-8"})
        result = self.plan(data)
        self.assertEqual((result["status"], result["action"]), ("planned", "regroup"))
        self.assertEqual((result["custom_regroup_number"], result["custom_regroup_limit"]), (3, 4))
        self.assertIn(data["regroup_extension"]["quote"], result["reason"])
        self.assertIn(data["regroup_extension"]["source_ref"], result["reason"])
        data["prior_custom_regroups"] = 3
        data["board_hash"] = "b" * 64
        self.assertEqual(self.plan(data)["custom_regroup_number"], 4)
        data["prior_custom_regroups"] = 4
        self.assertNoCommand(self.plan(data), "stopped")

    def test_extension_without_exact_finite_limit_and_source_is_invalid(self):
        for extension in ({"limit": True, "quote": "加两轮", "source_ref": "message-8"},
                          {"limit": 2, "quote": "加两轮", "source_ref": "message-8"},
                          {"limit": 4.0, "quote": "加两轮", "source_ref": "message-8"},
                          {"limit": 4, "quote": "", "source_ref": "message-8"},
                          {"limit": 4, "quote": "加两轮", "source_ref": ""},
                          {"limit": 4, "quote": "加两轮"}):
            data = request()
            data["regroup_extension"] = extension
            self.assertNoCommand(self.plan(data), "invalid")
        data = back_request()
        data["regroup_extension"] = {"limit": 4, "quote": "加两轮", "source_ref": "message-8"}
        self.assertNoCommand(self.plan(data), "invalid")

    def test_repeated_unsatisfied_stops_third_attempt_regardless_of_new_board(self):
        data = request()
        data["prior_custom_regroups"] = 1
        self.assertEqual(self.plan(data)["custom_regroup_number"], 2)
        for count in (2, 3, 100):
            data["prior_custom_regroups"] = count
            data["board_hash"] = "b" * 64
            self.assertNoCommand(self.plan(data), "stopped")

    def test_scale_cannot_accept_self_proposed_tier(self):
        data = request()
        data.update(gate="scale", self_proposed="自造t9档，每章十万字")
        result = self.plan(data)
        self.assertNoCommand(result, "unsupported")
        self.assertIn("t0～t5", result["message"])

    def test_free_text_choose_bypass_and_shell_command_inputs_are_rejected(self):
        data = request()
        data.update(command="choose --option custom --text 自拟方案")
        self.assertNoCommand(self.plan(data), "invalid")
        for engine in ("python3 /engine/scripts/novel.py", ["sh", "-c", "touch /tmp/wrong"],
                       ["sh", "/engine/scripts/novel.py"]):
            data = request()
            data["engine_argv"] = engine
            self.assertNoCommand(self.plan(data), "invalid")

    def test_shell_metacharacters_remain_data_in_one_reason_argument(self):
        data = request()
        data["requirements"] = ["原文 $(touch /tmp/wrong)；`echo wrong` 不应作为命令执行。"]
        result = self.plan(data)
        self.assertEqual(result["status"], "planned")
        self.assertEqual(len(result["argv"]), 9)
        self.assertIn(data["requirements"][0], result["argv"][-1])

    def test_strict_types_unknown_fields_and_missing_evidence_fail_closed(self):
        for update in ({"prior_custom_regroups": True}, {"prior_custom_regroups": -1},
                       {"authority_covers_refinement": "true"}, {"board_hash": "invented"},
                       {"project": "relative/book"}, {"rejection_reasons": []},
                       {"requirements": [], "self_proposed": ""}, {"gate": "unknown"},
                       {"changes_confirmed": ["unknown"]}, {"decision_kind": "automatic"}):
            with self.subTest(update=update):
                data = request()
                data.update(update)
                self.assertNoCommand(self.plan(data), "invalid")
        data = request()
        del data["source_quote"]
        self.assertNoCommand(self.plan(data), "invalid")

    def test_does_not_mutate_input_or_claim_authorization_is_verified(self):
        data = request()
        original = copy.deepcopy(data)
        result = self.plan(data)
        self.assertEqual(data, original)
        self.assertIn("不证明授权原话真实性", result["limitations"][0])
        self.assertFalse(result["authorization_verified"])
        self.assertFalse(result["board_verified"])
        self.assertFalse(result["history_verified"])

    def test_engine_entry_is_checked_and_json_cannot_choose_executable(self):
        self.assertNoCommand(MODULE.plan(request(), engine_root=self.engine / "missing"), "invalid")
        with patch.dict(os.environ, {}, clear=True):
            self.assertNoCommand(MODULE.plan(request()), "invalid")
        with patch.dict(os.environ, {"NOVEL_LEDGER": str(self.engine)}):
            self.assertEqual(MODULE.plan(request())["status"], "planned")
        data = request()
        data["engine_argv"] = ["sh", "-c", "echo bad"]
        self.assertNoCommand(self.plan(data), "invalid")

    def test_duplicate_json_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            MODULE._unique_object([("authority_covers_refinement", False),
                                   ("authority_covers_refinement", True)])

    def test_optional_owner_is_only_forwarded_never_created_or_claimed(self):
        data = request()
        self.assertNotIn("--owner", self.plan(data)["argv"])
        data["owner"] = "real-owner-from-current-project"
        result = self.plan(data)
        self.assertEqual(result["argv"][4:7], ["--owner", data["owner"], "regroup"])
        self.assertFalse(result["owner_verified"])
        self.assertNotIn("claim", result["argv"])
        self.assertNotIn("run", result["argv"])
        data["owner"] = ""
        self.assertNoCommand(self.plan(data), "invalid")


if __name__ == "__main__":
    unittest.main()
