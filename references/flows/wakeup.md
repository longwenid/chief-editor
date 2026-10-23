# 流程 S：唤醒·接管

进入条件：每次会话的第一件事；或用户说"继续 / 接着写 / 上次写到哪了"。

前置：按 `environment.md` 解析可信入口与 `$CHIEF_EDITOR_MEMORY`，`export PYTHONUTF8=1`。写作推进使用记录中的固定运行入口；开发树有变动不自动替换项目构建。遇 `engine_changed` 先按准确冻结版本恢复，升级另核对授权，不先重派任务。

## 步骤

1. 读 `$CHIEF_EDITOR_MEMORY/authorization.md` **头部**的最新授权与撤销记录：仍生效且明确覆盖本次新书选题的委托才走通道 B（`flows/selection.md`）；其他范围的委托不套用。范围缺失或不清时，开新书再问一次。
2. 读同一文件**尾部台账**：按 `P=` 列**分项目**恢复各自的 owner、档位、策略原话。owner 绝不跨项目混用。
3. 读 `$CHIEF_EDITOR_MEMORY/decisions/*.md`：新记录读取唯一 JSON 证据块的 `control`，旧记录按原 Markdown 字段读取。只将已落定、项目路径明确、`status=active` 的真实项目列入恢复清单；`synthetic=true` 示例和 draft/pending 提案不启动项目。逐条取项目路径、当前方向指纹、停点（可标注聚焦顺序）；按 `memory/templates.md` 的“当前方向同步”核对台账已完成的 direction_update，推进前补齐因中断未更新的投影，只读进度查询则报告未同步缺口而不写入。既有条目缺方向指纹时只从本条 chosen 与已存门摘要提炼，不跨项目读取正文或设定，不以旧 chosen 覆盖已同步的新方向。
4. 逐项目先只读查状态，并向宿主核实 pending 对应的真实 Worker，以及已绑定的独立读者是否仍在运行；台账旧会话名、prepare-worker.ready、历史读取活动与租约过期都不是当前存活/停止证明。`claim=null` 只表示尚无执行认领；`status.assurance` 保留原核验与宿主模式，不能降低模式恢复。本轮用户只要求分析或查看进度时，到这里交付状态即止，不自动推进项目：

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" status --tasks
```

5. 用户确实要求继续推进时，先按现场选择恢复方式，再按 action 与 stage 分流。**不能把唤醒写成无条件 `advance`**：它会重物化 pending 的任务视图，可能隔离正在写入的回执。技术阻断按 details.recovery 修复后 prepare-worker，独立核验按 writing F4b，均不套普通空转重派。下表现场名是本技能的宿主判定，不是引擎 action：

| 现场 | 动作 | 可重物化 pending |
|---|---|---|
| `read_only_request` | `status_only`：只返回进度或分析，不调用 advance/watch/run/renew | `false` |
| `worker_active` | `wait_existing`：保留原 Worker/独立读者；有真实正文 owner 时用 F3 `watch`，正文授权前等宿主提交事件 | `false` |
| `worker_unknown` | `report_pending`：保留任务，报告宿主执行状态未核实；不重新 claim、不另派 | `false` |
| `worker_stopped_pending` | `recover_task`：确认原执行者已停止，再按 opening D1/D3 或 writing F4 恢复 | `true` |
| `task_done` / `no_pending` | `advance_current`：已完成任务用 `--after` 核实；无 pending 时取当前 action | `true` |

6. 需要推进时，已有 owner 就携带**该项目恢复出的真实 owner**；从未 `run` 的开书设计阶段才不带 owner。租约失效时，仅在已有正文授权且没有 T2/修订阻断的前提下，带恢复的 owner、原目标、原模式与原授权重新 `run`；不编造 owner、不增加目标。当前仍有有效其他主控时保留现场，不能抢占。

```bash
# 已有 run：只在上述表允许推进时执行
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" advance --compact
# 已完成任务有准确 ID 时，沿同一 owner 核实提交并取下一步
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" advance --compact --after "$DONE_TASK"
```

正文授权前的无 owner 命令及等待方式见 `flows/opening.md` D3。几个 active 项目就逐个恢复；命令与宿主 Worker 身份都按项目隔离。

一切以引擎当前返回为准：不手改库、不凭上一轮的记忆续跑。

## 隔离

唤醒阶段只看状态摘要（项目名、方向指纹、进度/停点）。项目目录里的正文、卷纲章纲、`world_model`、任务文件、`board`/`question`/`dispatch`/`brief` 只在**该项目自己的**流程步骤里读；需要给用户转呈 T0 时才读该项目自己的 board 与 question，且只为它转呈（`red-lines.md#12`）。

## 记忆

读取清单本身不改记忆。实际执行恢复命令后仍按 `policy.md` 追加台账；`advance` 会物化任务文件，不把它当作只读状态查询。读 `authorization.md` + `decisions/*`。

## 出口

| action | stage / 前提 | 去向 |
|---|---|---|
| `task_ready` | `opening_options` | `opening:D1`：主干自执，不派独立 Worker |
| `task_ready` | `world_model` / `opening_contract` / `volume_outline` / `chapter_outline`，且尚无正文 run | `opening:D3`：设计派工与无 owner 等待 |
| `task_ready` | 其余已授权运行阶段 | `writing:F1`：先核实原 Worker，再认领派工 |
| `wait_for_batch` / `await_author` / `author_decision` / `paused` / `idle` | 已有正文 run；停点先按权威处置表判定 | `flows/writing.md` |
| `await_choice` / `world_ready` / `outline_ready` | 开书阶段 | `flows/opening.md` |
| `revision_blocked` / `revision_ready` | 任意 | `flows/writing.md` 的修订分支 |
| `worker_blocked` | 任意非门派工 | `writing:F1`：核实并修复技术原因后准备同一任务，不重置文学额度 |
| `review_required` / `review_in_progress` / `review_author_required` / `review_complete` | 独立连续性核验 | `writing:F4b`：保留准确候选、原执笔者和已绑定读者 |
| `ready_to_complete` / `completed` / `target_reached` | 任意 | `flows/delivery.md` |
| 无项目 / 用户要开新书 | 用户确实要开新书 | `flows/selection.md` |
