# 流程 S：唤醒·接管

进入条件：每次会话的第一件事；或用户说"继续上次的开书 / 门选到哪了"。

前置：按 `environment.md` 解析可信入口与 `$CHIEF_EDITOR_MEMORY`，`export PYTHONUTF8=1`。开书门推进使用记录中的固定运行入口；开发树有变动不自动替换项目构建。遇 `engine_changed` 先按准确冻结版本恢复，升级另核对授权，不先重开任务。

## 步骤

1. 读 `$CHIEF_EDITOR_MEMORY/authorization.md` **头部**的最新授权与撤销记录：仍生效且明确覆盖本次新书选题的委托才走通道 B（`flows/selection.md`）；其他范围的委托不套用。范围缺失或不清时，开新书再问一次。
2. 读同一文件**尾部台账**：按 `P=` 列**分项目**恢复各自的档位与策略原话。总编范围内不存在 owner（`run` 属于 novel-ledger 的写作阶段）；台账里若出现历史 owner，那是交接前的旧记录，只读不沿用。
3. 读 `$CHIEF_EDITOR_MEMORY/decisions/*.md`：新记录读取唯一 JSON 证据块的 `control`，旧记录按原 Markdown 字段读取。只将已落定、项目路径明确、`status=active` 的真实项目列入恢复清单；`synthetic=true` 示例和 draft/pending 提案不启动项目。逐条取项目路径、当前方向指纹、停点（可标注聚焦顺序）；按 `memory/templates.md` 的"当前方向同步"核对台账已完成的 direction_update，推进前补齐因中断未更新的投影，只读进度查询则报告未同步缺口而不写入。既有条目缺方向指纹时只从本条 chosen 与已存门摘要提炼，不跨项目读取正文或设定，不以旧 chosen 覆盖已同步的新方向。
4. 逐项目先只读查状态。本轮用户只要求分析或查看进度时，到这里交付状态即止，不自动推进项目：

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" status --tasks
```

5. 用户确实要求继续推进时，按现场分流。**不能把唤醒写成无条件 `advance`**：它会重物化 pending 的任务视图。下表现场名是本技能的宿主判定，不是引擎 action：

| 现场 | 动作 | 可重物化 pending |
|---|---|---|
| `read_only_request` | `status_only`：只返回进度或分析，不调用 advance | `false` |
| `beyond_activation` | 项目已过约定激活（世界/纲要/正文/交付阶段）：交付进度摘要并按 `flows/handoff.md` H2 指回 novel-ledger；不 advance、不认领 owner、不重派 | `false` |
| `gate_pending` | 开书门未完：`opening:D1` 主干自执接续 | `true` |
| `awaiting_choice` | 开书门待选：`opening:D2` 按三态处置 | `false` |

几个 active 项目就逐个恢复；命令按项目隔离。

一切以引擎当前返回为准：不手改库、不凭上一轮的记忆续跑。

## 隔离

唤醒阶段只看状态摘要（项目名、方向指纹、进度/停点）。项目目录里的正文、卷纲章纲、`world_model`、任务文件、`board`/`question`/`dispatch`/`brief` 只在**该项目自己的**流程步骤里读；需要给用户转呈 T0 时才读该项目自己的 board 与 question，且只为它转呈（`red-lines.md#12`）。已过激活的项目连任务文件也不读——那是 novel-ledger 的辖区，总编只看 `status` 摘要。

## 记忆

读取清单本身不改记忆。实际执行恢复命令后仍按 `policy.md` 追加台账；`advance` 会物化任务文件，不把它当作只读状态查询。读 `authorization.md` + `decisions/*`。

## 出口

| action | stage / 前提 | 去向 |
|---|---|---|
| `task_ready` | `opening_options` | `opening:D1`：主干自执 |
| `task_ready` | `world_model` / `opening_contract` / `volume_outline` / `chapter_outline` | `flows/handoff.md`：开书完成，交接 |
| `await_choice` | 开书阶段 | `opening:D2`：按三态处置 |
| `world_ready` / `outline_ready` / `ready_to_complete` / `completed` / `target_reached` 及一切正文阶段动作 | 任意 | `flows/handoff.md`：指回 novel-ledger |
| `author_decision` / `paused` 且项目仍在开书门内 | 开书阶段 | 按 `policy.md` T0 上报处置，解停后接 `opening:D1` |
| 无项目 / 用户要开新书 | 用户确实要开新书 | `flows/selection.md` |
