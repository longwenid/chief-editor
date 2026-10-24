# L2 引擎契约：命令面、返回处置与错误码

何时读：执行任何引擎命令之前、解释引擎返回之前、处置错误码之前。本文件只讲**命令怎么用、返回怎么处置**；"这条命令谁能决定"一律查 `policy.md` §2，本文件不列档位。

引擎目录、解释器、编码、记忆根怎么解析见 `environment.md`。与引擎文档冲突时以引擎文档为准，本文件只引用不复述。

## 0 职责边界

总编操作面只覆盖开书阶段（`init` 到十三门完成）。约定激活后的写作阶段命令——`run` / `watch` / `renew` / `claim` / `pause` / `resume` / `prepare-worker` / `prepare-observer` / `approve` / `feedback` / `review-resolve` / `recover-engine` / `recontract` / `revise` / `replan` / `lexical` / `revision-impact` / `promote` / `discard` / `complete` / `deliver` / `export` / `html`——由 novel-ledger 技能在交接后执行（`flows/handoff.md`）。下文不再逐条列出这些命令的用法。

## 1 命令表

项目命令形如 `python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" …`。开书设计阶段没有 controller owner，不带 `--owner`。新建固定副本的 `pin-engine` 不带项目；解析源入口、固定运行入口及恢复见 `environment.md`。

### 1.1 推进与核对

| 命令 | 用途与要点 |
|---|---|
| `pin-engine --output 运行目录 [--ref 准确发布引用]` | 生成或复用清单有效的固定运行副本，随后使用返回的 entry。不修改开发树，不复制临时补丁引擎 |
| `host-check` | 只读检查引擎所见宿主能力 |
| `advance [--compact] [--after 任务ID]` | "现在干什么"：返回当前 action 与任务信息；`--compact` 只带任务身份与路径。门任务据此进入 opening D1 自执；世界/纲要阶段任务是交接信号（handoff H1） |
| `status [--tasks]` | 查当前状态（含 `author_decision`、`revision_proposal`）；`--tasks` 列全部派工生命周期，取代直接查库；恢复项目第一步 |
| `usage` | 查看 `read`/`recall` 实际记录字符量 |
| `compact` | 回收不可达内容寻址文档空间；不改故事与账本状态，可重复执行 |
| `audit` | 只读验收服务，可作健康检查 |

### 1.2 作者决定入口

> 让位：存在委托原话时，本节命令由总编按 `policy.md` §3 代行——`--source` 记授权原话与当次理由，绝不伪称作者本人拍板。引擎侧机制（绑定准确展示版本、只接受已展示选项）不变。

| 命令 | 用途与要点 |
|---|---|
| `choose --option 方案ID --board 展示哈希 --source '原话'` | 记录当前门的选择，绑定准确展示版本；旧组编号不能套新门；亲选等真实答复，委托依 policy §3；不接受自由文本或特殊 custom ID |
| `choose --tier t0~t5 --source 原话` | 结构门直达档位，窗口自动滑动 |
| `regroup --board 展示哈希 --reason '具体拒绝原因、保留项和新要求'` | 在有效决定权限内否决当前组；reason 入历史并传本门下轮，创意门重新产候选，scale 仅滑档位窗口；不收 --source/--text。自拟候选仍须生成、核验、展示后 choose；闭环与上限见 flows/opening.md D2b |
| `back --gate 门ID --reason 原因` | 退回某门重选：保留前门，后续依赖门归档后重选 |
| `answer --decision-id ID --option '选项label' --source '答复原话'` | 应答开书阶段内的 `status.author_decision`：核对 id、选项必须已展示 |

### 1.3 开书

| 命令 | 用途与要点 |
|---|---|
| `init [--contract 约定.json --source '原话']` | 新建独立项目；零输入进入逐门开书，`--contract` 直接导入完整约定；已有约定的项目不得再次 `init` |
| `intake --file 要求.json --source '原话'` | `init` 后、未展示方案且无 pending 时按**门 ID** 保存作者已定的部分门值（字段名当键被拒并返回 `valid_gates`）；不替缺口补造决定 |
| `opening --file 约定.json --source '原话'` | 已 `init` 且未派过门任务时导入完整约定；派过门任务后被拒 |

### 1.4 门任务自执时的 Worker 面（唯一例外）

`opening_options` 门任务主干可自执：`read --task 任务ID` / `recall --task`（仅此阶段对主控放行）、`check --file result.json` 试算（`checked` 不等于已提交）、`submit --file result.json`（`session` 填主干身份，门任务不绑定会话）。

不在总编操作面的命令：`patch`、`worker-next`、`worker`、`worker-ready`、`worker-error`（Worker-only）；`review-read`、`review-observe`、`review-report`（独立读者专用）；`preflight`（Worker 回执试算流程，总编回执试算走 `check`）；`host-step` / `host-loop`（外部模型进程宿主才用的可选适配器）；以及 §0 列出的全部写作阶段命令。

## 2 禁止清单

- `read` / `recall` / `patch` / `worker-next` 是 Worker-only；唯一例外是 `opening_options` 门任务的 `read`/`recall`。`patch` 无任何主干例外。
- 正文与冻结审读阶段主控不可读（`role_boundary`）；要核对进度用 `status`，不读正文。
- `submit` 仅在自执 `opening_options` 门任务时使用。
- Worker 命令绝不代行；反向同理，Worker 不能执行主控或作者命令、不能 `init`。
- 不手改库、不伪造回执；不改写 schema、不修改或复制临时引擎取消判据（`references/red-lines.md#4`）。
- 写作阶段命令不代跑：即使台账里有历史 owner，也不在总编会话执行 `run` / `watch` / `prepare-worker` 等——按 `flows/handoff.md` 交接。

## 3 无 owner 阶段

开书设计阶段不存在 controller owner：`run` 尚未发生（它属于 novel-ledger 的正文授权），总编不持有也不沿用任何 owner。凡要求 `--owner` 的命令都不在总编操作面。

## 4 开书阶段返回动作分流

`advance` / `status` 返回后按动作分流；未列出的动作（`wait_for_batch` / `review_*` / `revision_*` / `ready_to_complete` 等）属写作阶段，一律按 `flows/handoff.md` 交接。

| action | 处置 |
|---|---|
| `task_ready`（`opening_options`） | opening D1 主干自执：读 brief → read → check → submit |
| `await_choice` | 按 policy 三态：亲选/未授权先贴 board.md 原文，按 question.json 原样提问并等真实答复；委托代选核对同一板面、准确哈希与真实选项后记录理由、choose 并继续。第一门未定向仍原样转呈 catalog.md 十二类目 |
| `task_ready`（`world_model` 等设计阶段）/ `world_ready` / `outline_ready` | 十三门完成：按 handoff H1/H2 交付开书成果并交接 novel-ledger |
| `author_decision` / `paused`（开书门内停点） | 把问题与选项原样上报；解停后继续 opening D1 |
| `preparing` / `wait_for_submit` | 只对真实缺口等待；开书门任务无外部 Worker，正常不会出现，出现即按现场核对 |

完整性失败与修复停点一律按 `policy.md` §2 的 T2 处置：保留现场、报告 code 与位置、等作者处置方向。

## 5 错误码处置入口

未登记的动作和命令错误按返回的 `code`/`details` 核实修正入口，不猜测成功、不无条件重试。以下只给入口：

| code | 含义与入口 |
|---|---|
| `creation` / `opening_option` / `opening_alignment` / `opening_diversity` / `opening_voice` | 开书协议与回执问题：`$NOVEL_LEDGER/references/opening.md#入口选择`、`$NOVEL_LEDGER/references/opening.md#方案回执（创意门）`、`$NOVEL_LEDGER/references/opening.md#门序与字段归属`、`$NOVEL_LEDGER/references/opening.md#结构门（体量与分卷）`。回执字段问题回到门任务自执修正后重交 |
| `author_decision` / `author_source` | 裁决与原话缺失：`$NOVEL_LEDGER/references/runtime.md#自动回改边界`；按 T0 上报 |
| `engine_changed` | 按 `details.recovery` 恢复准确固定构建；见 `$NOVEL_LEDGER/references/runtime.md#固定运行版本与受控切换` |
| `repair_budget` / `repair_exhausted` / `repair-stalled` | 门任务自执的返修额度与停滞：`$NOVEL_LEDGER/references/runtime.md#动作分支`；T2 保留现场交作者 |
| `remedy_exhausted` | 根问题最后一轮失败：T2 上报即停 |
| `stale_task` | 裁决前冻结的任务作废：按当前状态重新 `advance` |
| `projection` / `chain` / `state_integrity` / `source_integrity` / `governance_integrity` / `schema` | 完整性失败：T2 上报即停，不改写 schema、不修改或复制临时引擎取消判据、不直接写库 |
| `role_boundary` / `worker_boundary` | 角色越界：核对谁该执行这条命令（`$NOVEL_LEDGER/references/runtime.md#任务交接`） |
| `word_budget` / `drift_coverage` / `drift_before` / `outline_alignment` / `literal_policy` | 提交时机械核算：字段级问题回到当前门任务自执修正，总编不代改回执、不代填判断 |
| `file` / `access` | CLI 层：核实文件路径与命令拼写（未登记命令默认拒绝） |
