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

    def test_each_changed_confirmed_item_requires_author(self):
        for field in ("mainline", "style", "target", "scope"):
            data = request()
            data["changes_confirmed"] = [field]
            self.assertNoCommand(self.plan(data), "needs_author")

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
