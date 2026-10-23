# 流程 G：交付与复盘

进入条件：`advance` / `watch` 返回 `ready_to_complete`、`completed` 或 `target_reached`；或用户要交付、导出、修订已验收正文。

## G1 完本验收

`ready_to_complete` 时：

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" complete
```

验收项包括章数、篇幅区间、required 节点与线路解清、开放伏笔兑现、首章认可（须已 `approve`）。重复调用也复验准确快照——旧 `audit.ok` 与 `completed` 状态都不豁免。

## G2 交付

仅在本次 `complete` 复验通过，或引擎返回 `completed` 并提供准确完本快照时执行；`target_reached` 转 G3。

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" deliver
```

产出 `book.md` / `book.html` / `delivery.json`。交付失败**只重试该快照的 `deliver`**，不重新写书。

## G3 到点未完本

`target_reached`（授权目标到达但全书未完成）：

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" html
```

刷新全书视图，按**实际完成章节范围**交付，不冒充全书完本；decisions 保留 `status: active`，将本次交付范围、停点和授权目标追加到台账或新的复盘记录。只有用户明确要求扩大目标时才取新增授权；后续恢复沿已存授权核对，不把局部交付当作搁置或完本（`red-lines.md#11`）。

## G4 复盘

交付后、T2 停点后、用户纠偏后，新建 `$CHIEF_EDITOR_MEMORY/postmortems/YYYY-MM-DD-<slug>-<id>.md`（每次唯一，不覆盖同日旧档），骨架见 `memory/templates.md` §5：

- `engine_refusals`：引擎实际返回的 code + 一句话处置（从台账与现场输出回捞，不凭印象归类）；
- `market_vs_actual`：立项时的市场假设 vs 实际表现；
- `lesson`：一句话教训；
- `playbook_change_proposal`：改哪个流程文件、改成什么——提给维护者，总编不自行改主文档。

编辑判断复盘使用 `postmortem` JSON 证据记录，逐条引用立项时已登记的预测与实际观察，不改原预测。分别记录判断错误、执行偏离、曝光变化、观察不足；无足够对照时不强行归因。未上架或没有真实读者数据时，商业结论写“市场适配未验证”，完本、机械通过、作者认可都不能代替市场表现。

长篇阅读承诺与分阶段兑现引用引擎既有状态/纲要、Worker 报告或作者反馈；主干不借复盘直接读取正文，也不复制事实账本。保留不合模板却有效的文本机制及相反例子，检查总编是否因热度、名气或固定套路漏掉好方案。记录先过 `scripts/check_editorial_evidence.py`，文学结论仍须按 `references/editorial-judgment.md` 标明材料范围和未验证项。

## G5 回写决策状态

按实际结果更新，不能只因为“交付过一次”就关闭 active 项目。下表是本技能对结果的归类，不是新增引擎 action：

| 交付结果 | decisions.status |
|---|---|
| `target_reached` / `preview_export` / `delivery_failed` / `t2_stop` | `active` |
| `completed_and_delivered`（完本复验与正式交付均成功） | `delivered` |
| `author_shelved`（作者明确搁置） | `shelved` |

交付阶段只回写对应 decisions 唯一 JSON 证据块的 `control.status`；旧格式只改原 status 字段，不生成双份状态。局部交付范围、失败 code 和新作者原话另行追加留痕，不修改历史原话。开书重选后的方向投影另按 `memory/templates.md` 通用纪律同步，不借交付改写原立项判断或预测；save_editorial_record 只负责新增记录，不代行控制元数据回写。

## 附录：作者发起的方向性操作（全 T0，用户明示才执行）

```bash
# 历史修订：先只读影响分析，再带范围四选一（无范围会被拒并提示先跑 impact）
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" revision-impact --from-chapter "$N" [--changes-file 变更.json]
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" revise --from-chapter "$N" --reason '原因' (--changes-file 变更.json | --through "$M" | --to-end | --proposal-hash "$HASH" --source '授权原话')

# 方向性改约：已有正文 = 新分支自第 1 章重写全书、父分支保留可 discard，代价随已写章数线性增长——
# 必须先向作者说明该代价再执行；不能用改约绕过修复额度或作者边界、不能替代可 answer 的裁决
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" recontract --file 完整候选.json --source '作者原话' [--patch]

# 未写窗口章纲重排（作者明确要求；已有草稿/正式稿的章纲不能直接删）
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" replan --from-chapter "$N" --reason '原因'

# 字面规则（如 forbidden_name_chars 硬禁人名用字；修改会取消在途任务）
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" lexical --file 规则.json --source '作者原话'

# 预览导出（另存须显式 --output；导出不代替完本验收）
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" export [--format md|html] [--output 文件]
```

这些操作全部要作者原话，且不得用来绕过修复额度或作者裁决边界（`policy.md` §2、`red-lines.md#10`）。
