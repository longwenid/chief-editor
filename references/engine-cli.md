# L2 引擎契约：命令面、返回处置与错误码

何时读：执行任何引擎命令之前、解释引擎返回之前、处置错误码之前。本文件只讲**命令怎么用、返回怎么处置**；"这条命令谁能决定"一律查 `policy.md` §2，本文件不列档位。

引擎目录、解释器、编码、记忆根怎么解析见 `environment.md`。与引擎文档冲突时以引擎文档为准，本文件只引用不复述。

## 1 命令表

均形如 `python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" …`；带 `--owner` 的命令此前须先 `run` 取得 owner。

### 1.1 目标与推进

| 命令 | 用途与要点 |
|---|---|
| `run (--through N \| --complete) [--fast\|--standard] [--seconds S] --source '原话'` | 保存正文授权目标并取得 owner 租约（默认 300 秒）；`--fast` 开五章一组快速连写；前置：约定已激活；目标不得低于已冻结任务与修订范围。`--source` 逐字入账 |
| `advance [--compact] [--after 任务ID]` | "现在干什么"：返回当前 action 与派工信息；`--compact` 只带任务身份与路径。绝不自行拼下一任务 |
| `--owner ID watch [--steps N] [--poll 秒] [--idle-limit 秒]` | 无人值守主循环：进程内等待提交（零主干推理、自动续租），完成即带回下一 `task_ready`；快速模式等整组；`--steps 0` 长跑供外部派工器 |
| `--owner ID renew [--seconds S]` | 延长主控租约；`watch` 已自动续租 |
| `--owner ID claim --task 任务ID --session 宿主Worker会话 [--seconds S]` | **初始认领由主干进程执行**：为任务绑定 Worker 会话并返回 token，转给 Worker 填入回执顶层 `execution_claim`。`claim=null` 表示无需认领 |
| `--owner ID pause --reason 原因 [--cancel]` | 暂停（保留任务与候选）；`--cancel` 取消在途任务留档 |
| `--owner ID resume` | 从暂停恢复，不增加返修额度；撞 `revision_bounds` / `repair_budget` / `author_decision` / `remedy_exhausted` 即被拒，按 T2 上报 |

### 1.2 作者决定入口

> 让位：存在委托原话时，本节命令由总编按 `policy.md` §3 代行——`--source` 记授权原话与当次理由，绝不伪称作者本人拍板。引擎侧机制（绑定准确展示版本、只接受已展示选项）不变。

| 命令 | 用途与要点 |
|---|---|
| `choose --option 方案ID --board 展示哈希 --source '原话'` | 记录当前门的选择，绑定准确展示版本；旧组编号不能套新门；亲选等真实答复，委托依 policy §3；不接受自由文本或特殊 custom ID |
| `choose --tier t0~t5 --source 原话` | 结构门直达档位，窗口自动滑动 |
| `regroup --board 展示哈希 --reason '具体拒绝原因、保留项和新要求'` | 在有效决定权限内否决当前组；reason 入历史并传本门下轮，创意门重新产候选，scale 仅滑档位窗口；不收 --source/--text。自拟候选仍须生成、核验、展示后 choose；闭环与上限见 flows/opening.md D2b |
| `back --gate 门ID --reason 原因` | 退回某门重选：保留前门，后续依赖门归档后重选；约定激活后改方向须用 `recontract` |
| `--owner ID approve --prose-hash HASH --source '认可原话'` | 首章认可：绑定准确 `prose_hash`（不符报 `pilot_version`），同时固定文风锚点 |
| `--owner ID answer --decision-id ID --option '选项label' --source '答复原话'` | 应答 `status.author_decision`：核对 id、选项必须已展示；答复即冻结此前派工（`stale_task`）。**先 answer 再 advance** |
| `--owner ID recontract --file 完整候选.json --source '原话' [--patch]` | 激活后的方向性改约：已有正文时自第 1 章重写全书，代价随已写章数线性增长——先向作者说明再执行；`--patch` 只改列出字段 |
| `--owner ID revise --from-chapter N --reason 原因 (--changes-file 变更.json \| --through M \| --to-end \| --proposal-hash HASH --source '授权原话')` | 历史修订：无范围四选一直接拒绝并提示先跑 `revision-impact`；`--proposal-hash` 是超界方案入口，起章/终点/变更须匹配该方案 |
| `--owner ID replan --from-chapter N --reason 原因` | 未写窗口章纲重排 |
| `--owner ID lexical --file 规则.json --source '原话'` | 按书设置字面规则（如 `forbidden_name_chars`）；修改会取消在途任务 |
| `--owner ID feedback --text '原话'` | 对当前候选正文安排修复；已验收正文的历史修改改用 `revise` |

### 1.3 开书与收尾

| 命令 | 用途与要点 |
|---|---|
| `init [--contract 约定.json --source '原话']` | 新建独立项目；零输入进入逐门开书，`--contract` 直接导入完整约定；已有约定的项目不得再次 `init` |
| `intake --file 要求.json --source '原话'` | `init` 后、未展示方案且无 pending 时按**门 ID** 保存作者已定的部分门值（字段名当键被拒并返回 `valid_gates`）；不替缺口补造决定 |
| `opening --file 约定.json --source '原话'` | 已 `init` 且未派过门任务时导入完整约定；派过门任务后被拒，此时用 `recontract` |
| `--owner ID revision-impact --from-chapter N [--changes-file 变更.json]` | 只读影响分析：不改项目、不返回正文，给出 `last` / `rewrite_chapters` / `chapter_actions` / `coverage` / `expansion`；Worker 不能调用 |
| `--owner ID promote \| discard` | 修订候选分支验收后转正（`revision_ready` 且属当前授权目标）或放弃恢复父稿 |
| `--owner ID complete` | 完本验收：章数、篇幅区间、required 节点与线路解清、开放伏笔兑现、首章认可；重复调用复验准确快照，旧 `audit.ok` 与 `completed` 均不豁免 |
| `--owner ID deliver` | 从完本快照交付 `book.md` / `book.html` / `delivery.json`；失败只重试该快照的 `deliver`，不重新写书 |
| `--owner ID export [--format md\|html] [--output 文件]` | 导出纯文本或简化 HTML 预览；默认不写 `book.html`；导出不代替完本验收 |
| `--owner ID html` | 重建 `book.html` 全书只读视图，删了随时可重建 |
| `status [--tasks]` | 查当前状态（含 `author_decision`、`revision_proposal`）；`--tasks` 列全部派工生命周期，取代直接查库；恢复项目第一步 |
| `usage` | 查看 `read`/`recall` 实际记录字符量（宿主 token 由独立观测脚本统计，不从字符估算） |
| `compact` | 回收不可达内容寻址文档空间；不改故事与账本状态，可重复执行 |
| `audit` | 只读验收服务，可作健康检查；其 `ok` 不豁免 `complete`/`deliver` 复验 |

### 1.4 门任务自执时的 Worker 面（唯一例外）

`opening_options` 门任务主干可自执：`read --task 任务ID` / `recall --task`（仅此阶段对主控放行，正文与冻结审读阶段不在此列）、`check --file result.json` 试算（`checked` 不等于已提交）、`submit --file result.json`（`session` 填主干身份，门任务不绑定会话）。

不在总编操作面的命令：`patch`、`worker-next`（Worker-only）；`preflight`（Worker 回执试算流程，总编回执试算走 `check`）；`host-step` / `host-loop`（外部模型进程宿主才用的可选适配器）。

## 2 禁止清单

- `read` / `recall` / `patch` / `worker-next` 是 Worker-only；唯一例外是 `opening_options` 门任务的 `read`/`recall`。`patch` 无任何主干例外。
- 正文与冻结审读阶段主控不可读（`role_boundary`）；要核对进度用 `status`，不读正文。
- `submit` 仅在自执 `opening_options` 门任务时使用。
- Worker 命令绝不代行；反向同理，Worker 不能执行主控或作者命令、不能 `init`。派工提示里不写任何治理命令。
- 不手改库、不伪造回执；不改写 schema、不修改或复制临时引擎取消判据（`references/red-lines.md#4`、`references/red-lines.md#12`）。

## 3 owner 租约

1. `run --source` 保存授权目标并返回 owner；此后每条治理命令带 `--owner`。
2. 租约默认 300 秒；`watch` 在引擎进程内每 30 秒自动续租。
3. 手动延长用 `renew --owner ID [--seconds S]`。
4. 租约过期重新 `run` 认领，**沿用已授权的实际目标，不扩大范围**（`references/red-lines.md#11`）。
5. 初始 `claim` 由主干进程执行并转交 token；Worker 进程自己 `claim` 会被 `worker_boundary` 拒绝。
6. 档位归属见 `policy.md` §2，本文件不重复。

## 4 watch 返回动作处置

`watch` 返回后主干只做一件事：按动作处置。

| action | 处置 |
|---|---|
| `task_ready` | 先核实原 Worker 与 claim；仍活跃则等，不明则报告。确认允许派工后转发 `dispatch.md` + 角色 + `task_path` + 一句背景，再按当前阶段等待 |
| `wait_for_batch` | 原 Worker 正在接续本组，继续 `watch` 等整组，**不另派工** |
| `await_author` | 向用户呈准确版本首章；认可后 `approve --prose-hash HASH --source 原话`（T0，见 `policy.md` §2） |
| `author_decision` / `paused` 带裁决 | 把问题与选项原样上报；答复后 `answer`，**再** `advance` |
| `paused`（其他）/ `idle` | 先排除 T2 和待裁决停点，再核实宿主执行者：`worker_active` → `wait_existing`（沿真实 owner watch，设计阶段等宿主事件）；`worker_unknown` → `report_pending`（保留任务上报，不 claim/重派）；只有 `worker_stopped_pending` → `recover_task`，可 advance 重物化同一 pending。超时无提交不证明 Worker 已停；连续两次已确认的空转保留现场上报。快速组仍须确认原执行者停止，再 pause --cancel 结束组、resume/advance 重开，不扩大额度 |
| `revision_blocked` | 呈 `proposal.plan_path` 完整方案；等作者对该 `plan_hash` 的授权后 `revise --proposal-hash`；**不得用改约、重新 run 或 resume 绕过** |
| `revision_ready` | 属当前授权目标 = `promote`；不属于或作者要先看候选 = 交作者 |
| `ready_to_complete` | `complete`（复验准确快照）→ 通过后 `deliver` |
| `completed` | 从完本快照 `deliver`，或恢复失败的交付；成功即结束 |
| `target_reached` | 刷新 `html`，按实际完成章节范围交付，不冒充全书完本 |
| `world_ready` / `outline_ready` | 交付返回的世界与实际卷纲覆盖；已有正文授权但未保存时用 `run` 保存同一授权后继续 |
| `await_choice` | 先贴 `board.md` 原文再按 `question.json` 选项原样提问；第一门未定向另有 `catalog.md` 十二类目原文贴出（`$NOVEL_LEDGER/references/opening.md#第一门的全类目`） |
| `wait_for_submit` / `resync` / `preparing` | 等待或联系当前子 agent / 放下过期 `after` 重取状态 / 只对真实缺口等待作者 |

完整性失败与修复停点一律按 `policy.md` §2 的 T2 处置：保留现场、报告 code 与位置、等作者处置方向。

## 5 错误码处置入口

未登记的动作和命令错误按返回的 `code`/`details` 核实修正入口，不猜测成功、不无条件重试。以下只给入口：

| code | 含义与入口 |
|---|---|
| `creation` / `opening_option` / `opening_alignment` / `opening_diversity` / `opening_voice` | 开书协议与回执问题：`$NOVEL_LEDGER/references/opening.md#入口选择`、`$NOVEL_LEDGER/references/opening.md#方案回执（创意门）`、`$NOVEL_LEDGER/references/opening.md#门序与字段归属`、`$NOVEL_LEDGER/references/opening.md#结构门（体量与分卷）`。回执字段问题回到门任务自执修正后重交 |
| `author_decision` / `author_source` | 裁决与原话缺失：`$NOVEL_LEDGER/references/runtime.md#自动回改边界`（answer 顺序、第三条路走 recontract）；按 T0 上报 |
| `pilot_version` | 认可版本与当前首章不符：`$NOVEL_LEDGER/references/runtime.md#动作分支`；重新向用户呈准确版本 |
| `repair_budget` / `repair_exhausted` / `repair-stalled` | 返修额度与停滞：`$NOVEL_LEDGER/references/runtime.md#动作分支`、`$NOVEL_LEDGER/references/runtime.md#暂停与修改`；T2 保留现场交作者 |
| `remedy_exhausted` | 根问题最后一轮失败：T2 上报即停 |
| `revision_bounds` / `rewrite_limit` / `closed_volume` / `outside_recent_window` | 超自动回改边界：`$NOVEL_LEDGER/references/runtime.md#自动回改边界`；呈 `proposal.plan_path` 等 `plan_hash` 授权 |
| `stale_task` | 裁决前冻结的派工作废：按当前状态重新 `advance` 再派 |
| `projection` / `chain` / `state_integrity` / `source_integrity` / `schema` | 完整性失败：T2 上报即停，不改写 schema、不修改或复制临时引擎取消判据、不直接写库 |
| `role_boundary` / `worker_boundary` | 角色越界：核对谁该执行这条命令（`$NOVEL_LEDGER/references/runtime.md#任务交接`） |
| `controller_lease` / `lease` / `worker_lease` | 租约问题：`renew` 或重新 `run` 认领（目标不扩大） |
| `target` / `revision_target` / `writing_batch` | 目标与模式约束：`$NOVEL_LEDGER/references/runtime.md#目标与主控认领`、`$NOVEL_LEDGER/references/runtime.md#快速无人值守：五章一组` |
| `worker_busy` | 另一 Worker 持有任务租约：`$NOVEL_LEDGER/references/runtime.md#任务交接` |
| `word_budget` / `drift_coverage` / `drift_before` / `outline_alignment` / `literal_policy` | 提交时机械核算：字段级问题交回当前 Worker 修正，总编不代改回执、不代填判断 |
| `host_launch_failed` / `host_timeout` / `step_limit` | 外部进程适配器（仅子进程宿主）：`$NOVEL_LEDGER/references/runtime.md#可选子进程适配器` |
| `file` / `access` | CLI 层：核实文件路径与命令拼写（未登记命令默认拒绝） |
