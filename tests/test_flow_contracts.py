"""Static flow-contract regressions; never import/run the engine or open a book DB.

The tables in the flow documents are inspectable decision contracts. These tests
check their branches and executable CLI examples against the real CLI's AST.
They cannot prove an LLM/host follows the prose, creates real Worker sessions,
or renews a lease correctly. Integration tests need a separate authorized host.

Run: NOVEL_LEDGER=<engine-root> python3 -B -m unittest discover -s tests
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import shlex
import unittest


ROOT = Path(__file__).resolve().parents[1]
FLOWS = ROOT / "references" / "flows"


def code_tags(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def table_rows(text: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def branches(text: str, width: int) -> dict[str, list[str]]:
    """Index documented branch keys, expanding multi-key first cells."""
    result = {}
    for cells in table_rows(text):
        if len(cells) == width:
            for key in code_tags(cells[0]):
                if key in result:
                    raise AssertionError(f"ambiguous branch: {key}")
                result[key] = cells[1:]
    return result


def bash_commands(text: str) -> list[list[str]]:
    """Only concrete examples: notation such as [optional] stays documentation."""
    commands = []
    for block in re.findall(r"```bash\n(.*?)```", text, re.S):
        for line in block.splitlines():
            if not re.match(r"^python(?:3)?\s", line):
                continue
            words = shlex.split(line, comments=True)
            if len(words) < 2 or not words[1].endswith("/novel.py"):
                continue  # Skill helpers have their own tests; this schema is the engine CLI.
            if any(word.startswith(("[", "(")) or "|" in word for word in words):
                continue
            commands.append(words)
    return commands


def engine_path() -> Path | None:
    candidates = [ROOT.parent / "novel-ledger", Path.home() / ".zcode/skills/novel-ledger"]
    if os.environ.get("NOVEL_LEDGER"):
        candidates.insert(0, Path(os.environ["NOVEL_LEDGER"]).expanduser())
    return next((p / "scripts/novel.py" for p in candidates if (p / "scripts/novel.py").is_file()), None)


def literal(node: ast.AST, names: dict):
    """Small, non-executing evaluator for parser command predicates/flag names."""
    if isinstance(node, ast.Name):
        return names[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return literal(node.left, names) + literal(node.right, names)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left, right = literal(node.left, names), literal(node.right, names)
        if not isinstance(left, (set, frozenset)) or not isinstance(right, (set, frozenset)):
            raise ValueError("Only set union is supported in CLI declarations")
        return left | right
    if isinstance(node, (ast.Set, ast.Tuple, ast.List)):
        values = [literal(value, names) for value in node.elts]
        return set(values) if isinstance(node, ast.Set) else tuple(values) if isinstance(node, ast.Tuple) else values
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        left, right = literal(node.left, names), literal(node.comparators[0], names)
        op = node.ops[0]
        if isinstance(op, ast.Eq):
            return left == right
        if isinstance(op, ast.In):
            return left in right
        if isinstance(op, ast.NotIn):
            return left not in right
    if isinstance(node, ast.BoolOp):
        values = [literal(value, names) for value in node.values]
        return all(values) if isinstance(node.op, ast.And) else any(values)
    return ast.literal_eval(node)


@dataclass
class Schema:
    flags: dict[str, bool] = field(default_factory=dict)
    required: set[str] = field(default_factory=set)
    groups: list[tuple[bool, set[str]]] = field(default_factory=list)


def cli_schemas(source: str) -> dict[str, Schema]:
    """Extract add_argument metadata; no engine import, eval, exec, or dispatch."""
    module = ast.parse(source)
    declarations, constants, resolving = {}, {}, set()
    for node in module.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            declarations[node.targets[0].id] = node.value
    parser = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "parser")
    loop = next(node for node in parser.body if isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == "command")
    schemas = {}

    def constant(name):
        if name in constants:
            return constants[name]
        if name in resolving:
            raise ValueError(f"Cyclic CLI constant: {name}")
        resolving.add(name)
        expression = declarations[name]
        dependencies = {node.id for node in ast.walk(expression) if isinstance(node, ast.Name)}
        value = literal(expression, {dependency: constant(dependency) for dependency in dependencies})
        constants[name] = value
        resolving.remove(name)
        return value

    # Resolve referenced declarations only. Never import or execute the engine,
    # including unrelated module initializers or dynamic command factories.
    for name in {"PUBLIC", "SEALED"} | {node.id for node in ast.walk(loop) if isinstance(node, ast.Name) and node.id in declarations}:
        constant(name)

    def visit(statements, names, schema, groups):
        for node in statements:
            if isinstance(node, ast.If):
                visit(node.body if literal(node.test, names) else node.orelse, names, schema, groups)
            elif isinstance(node, ast.For):
                for value in literal(node.iter, names):
                    visit(node.body, {**names, node.target.id: value}, schema, groups)
            elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Attribute) and call.func.attr == "add_mutually_exclusive_group":
                    required = next((ast.literal_eval(k.value) for k in call.keywords if k.arg == "required"), False)
                    entry = (required, set())
                    schema.groups.append(entry)
                    groups[node.targets[0].id] = entry
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                if not isinstance(call.func, ast.Attribute) or call.func.attr != "add_argument":
                    continue
                flags = [literal(arg, names) for arg in call.args]
                keywords = {k.arg: k.value for k in call.keywords}
                action = ast.literal_eval(keywords["action"]) if "action" in keywords else "store"
                takes_value = action not in {"store_true", "store_false", "store_const", "version"}
                required = ast.literal_eval(keywords["required"]) if "required" in keywords else False
                for flag in flags:
                    schema.flags[flag] = takes_value
                    if required:
                        schema.required.add(flag)
                    receiver = call.func.value
                    if isinstance(receiver, ast.Name) and receiver.id in groups:
                        groups[receiver.id][1].add(flag)

    for command in sorted(constants["PUBLIC"] | constants["SEALED"]):
        schema = Schema(flags={"--project": True, "--owner": True})
        visit(loop.body, {**constants, "command": command}, schema, {})
        schemas[command] = schema
    return schemas


def command_errors(words: list[str], schemas: dict[str, Schema]) -> list[str]:
    command = next((word for word in words[2:] if word in schemas), None)
    if command is None:
        return ["unknown command"]
    schema = schemas[command]
    flags = {word for word in words[2:] if word.startswith("--")}
    errors = [f"missing {flag}" for flag in sorted(schema.required - flags)]
    errors += [f"unsupported {flag}" for flag in sorted(flags - schema.flags.keys())]
    for required, members in schema.groups:
        count = len(flags & members)
        if count > 1 or required and count != 1:
            errors.append(f"exclusive group {sorted(members)}: {count}")
    for index, word in enumerate(words):
        if schema.flags.get(word) and (index + 1 == len(words) or words[index + 1].startswith("--")):
            errors.append(f"missing value for {word}")
    return errors


class FlowContracts(unittest.TestCase):
    def test_authoritative_idle_table_preserves_the_same_worker_guards(self):
        recovery = branches((FLOWS / "wakeup.md").read_text().split("## 隔离")[0], 3)
        authority = (ROOT / "references" / "engine-cli.md").read_text()
        idle = next(cells[1] for cells in table_rows(authority)
                    if len(cells) == 2 and "idle" in code_tags(cells[0]))
        tokens = code_tags(idle)
        for state in ("worker_active", "worker_unknown", "worker_stopped_pending"):
            with self.subTest(state=state):
                self.assertIn(state, tokens, "idle timeout does not establish host termination")
                self.assertEqual(tokens[tokens.index(state) + 1], code_tags(recovery[state][0])[0])

    def test_read_only_and_active_workers_never_redispatch(self):
        recovery = branches((FLOWS / "wakeup.md").read_text().split("## 隔离")[0], 3)
        for state, operation in {"read_only_request": "status_only", "worker_active": "wait_existing", "worker_unknown": "report_pending"}.items():
            with self.subTest(state=state):
                self.assertEqual(code_tags(recovery[state][0])[0], operation)
                self.assertEqual(code_tags(recovery[state][1]), ["false"])
        for state in ("worker_stopped_pending", "task_done", "no_pending"):
            self.assertEqual(code_tags(recovery[state][1]), ["true"])

    def test_opening_task_routing_uses_stage(self):
        text = (FLOWS / "wakeup.md").read_text()
        routes = [cells for cells in table_rows(text) if len(cells) == 3 and code_tags(cells[0]) == ["task_ready"]]
        stage_targets = {}
        for _, stages, target in routes:
            for stage in code_tags(stages):
                self.assertNotIn(stage, stage_targets)
                stage_targets[stage] = code_tags(target)[0]
        self.assertEqual(stage_targets["opening_options"], "opening:D1")
        for stage in ("world_model", "opening_contract", "volume_outline", "chapter_outline"):
            self.assertEqual(stage_targets[stage], "opening:D3")
        self.assertTrue(any(code_tags(row[2]) == ["writing:F1"] for row in routes))

    def test_unowned_design_waits_for_host_then_advances_after(self):
        design = branches((FLOWS / "opening.md").read_text(), 3)
        self.assertEqual(code_tags(design["not_started"][0]), ["host_event"])
        self.assertEqual(code_tags(design["not_started"][1]), ["advance_after"])
        self.assertEqual(code_tags(design["authorized"][0]), ["watch"])
        commands = bash_commands((FLOWS / "opening.md").read_text())
        completed = [words for words in commands if "advance" in words and "--after" in words]
        self.assertTrue(completed)
        self.assertTrue(all("--owner" not in words for words in completed))
        self.assertFalse(any("watch" in words for words in commands))

    def test_wakeup_advance_preserves_recovered_owner(self):
        advances = [words for words in bash_commands((FLOWS / "wakeup.md").read_text()) if "advance" in words]
        self.assertTrue(advances)
        for words in advances:
            self.assertIn("--owner", words)
            self.assertEqual(words[words.index("--owner") + 1], "$OWNER")

    def test_design_and_writing_prepare_real_workers(self):
        for name, needs_owner in (("opening", False), ("writing", True)):
            commands = bash_commands((FLOWS / f"{name}.md").read_text())
            preparations = [words for words in commands if "prepare-worker" in words]
            with self.subTest(flow=name):
                self.assertTrue(preparations, "claim=null does not waive execution identity preparation")
                self.assertFalse(any("claim" in words for words in commands), "new dispatch uses prepare-worker")
                for words in preparations:
                    self.assertEqual("--owner" in words, needs_owner)
                    self.assertIn("--task", words)
                    self.assertIn("--session", words)

    def test_review_lifecycle_has_distinct_recovery_routes(self):
        actions = (ROOT / "references" / "engine-cli.md").read_text().split("## 4 watch 返回动作处置")[1].split("## 5")[0]
        authority = {key: cells[1] for cells in table_rows(actions) if len(cells) == 2
                     for key in code_tags(cells[0]) if key.startswith("review_")}
        writing = branches((FLOWS / "writing.md").read_text().split("### F4b")[1].split("### F5")[0], 2)
        for action in ("review_required", "review_in_progress", "review_author_required", "review_complete"):
            self.assertIn(action, authority)
            self.assertIn(action, writing)
        for name in ("opening", "writing", "wakeup"):
            for words in bash_commands((FLOWS / f"{name}.md").read_text()):
                self.assertFalse({"review-read", "review-observe", "review-report", "worker-ready"} & set(words),
                                 "controller examples must not impersonate the observer/Worker")

    def test_partial_delivery_remains_discoverable(self):
        delivery = branches((FLOWS / "delivery.md").read_text(), 2)
        for result in ("target_reached", "preview_export", "delivery_failed"):
            self.assertEqual(code_tags(delivery[result][0]), ["active"])
        self.assertEqual(code_tags(delivery["completed_and_delivered"][0]), ["delivered"])
        self.assertEqual(code_tags(delivery["author_shelved"][0]), ["shelved"])


class RealCliExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        engine = engine_path()
        if engine is None:
            raise unittest.SkipTest("Set NOVEL_LEDGER to check real CLI arguments; document contracts still run")
        cls.schemas = cli_schemas(engine.read_text(encoding="utf-8"))

    def test_executable_flow_examples_have_real_required_arguments(self):
        checked = 0
        for name in ("wakeup", "opening", "writing", "delivery"):
            for words in bash_commands((FLOWS / f"{name}.md").read_text()):
                checked += 1
                with self.subTest(flow=name, command=words):
                    self.assertEqual(command_errors(words, self.schemas), [])
        self.assertGreater(checked, 20)

    def test_original_missing_revision_reason_is_rejected(self):
        revision = next(words for words in bash_commands((FLOWS / "writing.md").read_text()) if "revise" in words)
        self.assertEqual(command_errors(revision, self.schemas), [])
        broken = list(revision)
        index = broken.index("--reason")
        del broken[index:index + 2]
        self.assertIn("missing --reason", command_errors(broken, self.schemas))

    def test_real_cli_target_group_remains_required_and_exclusive(self):
        prefix = ["python", "$NOVEL_LEDGER/scripts/novel.py", "--project", "$PROJECT", "run"]
        self.assertTrue(command_errors(prefix, self.schemas))
        self.assertTrue(command_errors(prefix + ["--through", "40", "--complete"], self.schemas))
        self.assertEqual(command_errors(prefix + ["--through", "40", "--source", "原授权"], self.schemas), [])

    def test_real_identity_and_review_commands_keep_required_bindings(self):
        cases = {
            "prepare-worker": {"--task", "--session"},
            "prepare-observer": {"--request", "--session"},
            "review-resolve": {"--request", "--disposition", "--source"},
            "recover-engine": {"--task", "--input-hash", "--source"},
            "review-read": {"--request"},
            "review-report": {"--request", "--file"},
        }
        for command, required in cases.items():
            with self.subTest(command=command):
                self.assertTrue(required <= self.schemas[command].required)
                prefix = ["python3", "$NOVEL_LEDGER/scripts/novel.py", command]
                errors = command_errors(prefix, self.schemas)
                for flag in required:
                    self.assertIn(f"missing {flag}", errors)


class CliAstCompatibility(unittest.TestCase):
    SOURCE = """
PUBLIC = {'prepare-observer', 'review-resolve'}
OBSERVER = {'review-read', 'review-observe', 'review-report'}
SEALED = {'read'} | OBSERVER
raise RuntimeError('This module must never execute')
def parser():
    for command in sorted(PUBLIC | SEALED):
        sub = subs.add_parser(command)
        if command in OBSERVER | {'prepare-observer', 'review-resolve'}:
            sub.add_argument('--request', required=True)
        if command in ('review-observe', 'review-report'):
            sub.add_argument('--file', required=True)
        if command == 'prepare-observer':
            sub.add_argument('--session', required=True)
"""

    def test_named_set_union_preserves_observer_command_flags_without_execution(self):
        schemas = cli_schemas(self.SOURCE)
        self.assertEqual(set(schemas), {"read", "prepare-observer", "review-resolve", "review-read", "review-observe", "review-report"})
        self.assertEqual(schemas["read"].required, set())
        self.assertEqual(schemas["prepare-observer"].required, {"--request", "--session"})
        self.assertEqual(schemas["review-read"].required, {"--request"})
        self.assertEqual(schemas["review-report"].required, {"--request", "--file"})

    def test_constant_dependency_order_does_not_change_union(self):
        reordered = self.SOURCE.replace("OBSERVER = {'review-read', 'review-observe', 'review-report'}\n", "")
        reordered += "\nOBSERVER = {'review-read', 'review-observe', 'review-report'}\n"
        self.assertEqual(cli_schemas(reordered), cli_schemas(self.SOURCE))

    def test_dynamic_command_sets_fail_closed(self):
        with self.assertRaises((KeyError, ValueError)):
            cli_schemas(self.SOURCE.replace("{'read'} | OBSERVER", "load_commands()"))

    def test_cyclic_command_sets_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "Cyclic CLI constant"):
            cli_schemas(self.SOURCE.replace("{'review-read', 'review-observe', 'review-report'}", "SEALED"))


if __name__ == "__main__":
    unittest.main()
