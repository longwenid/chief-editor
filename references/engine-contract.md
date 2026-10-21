# 引擎操作面：novel-ledger CLI 契约

何时读：执行任何治理命令、解释引擎返回、处置错误码之前。本文只划总编侧的操作边界与处置入口；字段与机制细则一律**引用** novel-ledger 技能文档（`$NOVEL_LEDGER/references/` 下的 runtime.md、opening.md 等），不复制内容——引擎文档升级时以引擎为准。

约定：`$NOVEL_LEDGER` 指向 novel-ledger 技能目录（本机默认 `C:/Users/longwen/.zcode/skills/novel-ledger`），`$PROJECT` 为独立小说项目绝对路径，Windows 用 `python`。人读长内容（board.md/question.json/dispatch.md/brief.md/task.json）一律走引擎物化文件；控制台只看机器可读的短 JSON，先 `PYTHONUTF8=1`（runtime.md:73）。

## 允许的命令

均形如 `python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" ...`；带 owner 的命令此前须先 run 取得 owner。

### 目标与推进（T1）

| 命令 | 用途与要点 | 作者门槛 |
|---|---|---|
| `run (--through N \| --complete) [--fast\|--standard] [--seconds S] --source '作者授权原话'` | 保存正文授权目标并取得 owner 租约（默认 300 秒）；--fast 开五章一组快速连写（writing_mode=fast）；前置：约定已激活；目标不得低于已冻结任务/修订范围（application.py:424-450） | 必填 --source：原话逐字入 book.decisions（application.py:448）——T0 |
| `advance [--compact] [--after 任务ID]` | 总编核心"现在干什么"：返回当前 action 与派工信息；--compact 只带任务身份与路径；绝不自行拼下一任务（novel-ledger SKILL.md:53） | — |
| `--owner ID watch [--steps N] [--poll 秒] [--idle-limit 秒]` | 无人值守主循环：引擎进程内等待提交（零主干推理、自动续租），完成即带回下一 task_ready；快速模式等整组；--steps 0 长跑供外部派工器（unattended.py:19-73） | 只需 owner；watch 不产生新授权 |
| `--owner ID renew [--seconds S]` | 延长主控租约（application.py:463-470）；watch 已自动续租 | — |
| `--owner ID claim --task 任务ID --session 宿主Worker会话 [--seconds S]` | **初始认领由主干进程执行**：为任务绑定 Worker 会话并返回 token，转给 Worker 填入回执顶层 execution_claim；Worker 进程自己 claim 会被 worker_boundary 拒绝；claim=null 表示无需认领（novel.py:211-217；runtime.md:108） | 需真实宿主 Worker 会话，不能伪造 |
| `--owner ID pause --reason 原因 [--cancel]` | 暂停（保留任务与候选）；--cancel 取消在途任务留档 | — |
| `--owner ID resume` | 从暂停恢复，不增加返修额度；被 revision_bounds/repair_budget/author_decision/remedy_exhausted 拒绝时这些停点必须先由作者处置（application.py:595-606）→ 自动降级 T2 | 存在未答 author_decision 时 resume 被拒，必须先 answer（application.py:599） |

### 作者决定入口（T0：只转呈、只存原话，绝不代答）

> 让位说明：用户以原话（常设或逐次）委托代选时，本节入口由总编按 SKILL.md「三档预授权」的代选纪律代行——--source 逐字记授权原话＋当次代选对象与理由，绝不伪称作者本人拍板；引擎侧机制（绑定准确展示版本、只接受已展示选项）不变。本文件各处"上报/转呈/绝不代答"均按此让位理解。

| 命令 | 用途与要点 |
|---|---|
| `choose --option 方案ID --board 展示哈希 --source '作者原话'` | 记录作者在当前门的选择，绑定准确展示版本（旧组编号不能套新门）；必须等真实作者选择到来（opening.md:30,144） |
| `choose --tier t0~t5 --source 原话` | 结构门直达档位，窗口自动滑动（opening.md:99,145） |
| `regroup --board 展示哈希 --reason '换一组'` | 作者否决当前方案组后换新组：新组须与被拒旧组实质不同并吸收作者随换组补充的偏好（opening.md:53,146）；命令收 --reason 不收原话字段 |
| `back --gate 门ID --reason 原因` | 返回某一门重选：保留前门，后续依赖门归档后重选（opening.md:147,150）；约定激活后改方向须用 recontract |
| `--owner ID approve --prose-hash HASH --source '作者认可原话'` | 首章（pilot）作者认可：绑定准确 prose_hash（不符报 pilot_version），同时固定文风锚点（application.py:472-488；runtime.md:123） |
| `--owner ID answer --decision-id ID --option '选项label' --source '作者答复原话'` | 应答 status.author_decision 展示的待决问题：核对 id、选项必须已展示；答复即冻结此前派工（stale_task，application.py:647）。**先 answer 再 advance/recontract**（runtime.md:196-203） |
| `--owner ID recontract --file 完整候选.json --source '作者原话' [--patch]` | 激活后的方向性改约：已有正文时在新分支自第 1 章重写全书，代价随已写章数线性增长——**须先向作者说明再执行**；--patch 只改列出字段（runtime.md:136,139） |
| `--owner ID revise --from-chapter N --reason 原因 (--changes-file 变更.json \| --through M \| --to-end \| --proposal-hash HASH --source '授权原话')` | 历史修订（作者明确请求）：无范围四选一直接拒绝并提示先跑 revision-impact；--proposal-hash 是作者授权超界方案的入口，起章/终点/变更须匹配该方案（runtime.md:132,175,208-214） |
| `--owner ID replan --from-chapter N --reason 原因` | 作者明确要求的未写窗口章纲重排（runtime.md:133） |
| `--owner ID lexical --file 规则.json --source '作者原话'` | 按书设置字面规则（如 forbidden_name_chars 硬禁人名用字）；修改会取消在途任务（opening.md:49；runtime.md:134） |
| `--owner ID feedback --text '作者原话'` | 对当前候选正文安排修复；已验收正文的历史修改改用 revise（runtime.md:131） |

### 开书与收尾

| 命令 | 用途与要点 | 作者门槛 |
|---|---|---|
| `init [--contract 约定.json --source '作者原话']` | 新建独立项目；零输入进入逐门开书，--contract 直接导入完整约定（默认目标试章）；已有约定的项目不得再次 init（README:154-166） | 零输入 init 不要求 source（opening.md:123）；--contract 导入需 --source |
| `intake --file 要求.json --source '作者原话'` | init 后、未展示方案且无 pending 时按**门 ID** 保存作者已定的部分门值（键必须是门 ID，字段名当键被拒并返回 valid_gates）；不替缺口补造决定（opening.md:19,139） | 需 --source；只保存作者已定的值 |
| `opening --file 约定.json --source '作者原话'` | 已 init 且未派过门任务时导入完整约定；派过门任务后按 creation 拒绝，此时用 recontract（opening.md:17,154） | 需 --source |
| `--owner ID revision-impact --from-chapter N [--changes-file 变更.json]` | 只读影响分析：不改项目不返回正文，给出 last/rewrite_chapters/chapter_actions/coverage/expansion；Worker 不能调用（runtime.md:159-175） | — |
| `--owner ID promote \| discard` | 修订候选分支验收后转正（revision_ready 且属当前授权目标）或放弃恢复父稿（runtime.md:83,97）；不属于当前授权目标或作者要先看候选，交作者决定 | 修订采纳边界归作者 |
| `--owner ID complete` | 完本验收：章数、篇幅区间、required 节点与线路解清、开放伏笔兑现、首章认可；重复调用复验准确快照，旧 audit.ok 与 completed 均不豁免（runtime.md:149-153） | 首章认可是验收项（须已 approve） |
| `--owner ID deliver` | 从完本快照交付 book.md/book.html/delivery.json；交付失败只重试该快照的 deliver，不重新写书（runtime.md:151,153） | — |
| `--owner ID export [--format md\|html] [--output 文件]` | 导出纯文本或简化 HTML 预览；默认不写 book.html，另存须显式 --output（README:117）；导出不代替完本验收 | — |
| `--owner ID html` | 重建 book.html 全书只读视图，删了可随时重建（README:115；runtime.md:87） | — |
| `status [--tasks]` | 查当前状态（含 author_decision、revision_proposal）；--tasks 列全部派工任务生命周期，取代直接查库（runtime.md:110）；恢复项目第一步（runtime.md:29-34） | — |
| `usage` | 查看 read/recall 实际记录字符量（宿主 token 由独立 observe.py 观测，不从字符估算）（runtime.md:151） | — |
| `compact` | 回收不可达内容寻址文档空间；不改故事与账本状态，可重复执行（runtime.md:135） | — |

### 门任务自执时的 Worker 面（唯一例外）

opening_options 门任务主干可自执（contracts.py:177 CONTROLLER_STAGES）：`read --task 任务ID` / `recall --task`（novel.py:186-199 对主控放行，正文与冻结审读阶段不在此列）、`check --file result.json` 试算（checked 不代表已提交，novel.py:264-268；runtime.md:121）、`submit --file result.json`（session 填主干身份，门任务不绑定会话，novel-ledger SKILL.md:55）。

不在总编操作面的命令：`patch`、`worker-next`（Worker-only，novel.py:18）；`preflight`（Worker 回执试算流程，属 Worker 集但不在 WORKER_ONLY，总编不用，回执试算走 `check`）；`host-step`/`host-loop`（外部模型进程宿主才用的可选适配器，runtime.md:216-224）。`audit` 是 SEALED 的只读验收服务，总编可执行作健康检查，但其 ok 不豁免 complete/deliver 复验（runtime.md:153）。

## 禁止清单

- `read`/`recall`/`patch`/`worker-next` 是 Worker-only（novel.py:18 WORKER_ONLY）；唯一例外是 opening_options 门任务的 read/recall（novel.py:186-199；contracts.py:177）。patch 无任何主干例外。
- 正文与冻结审读阶段主控不可读（role_boundary）；总编要核对进度用 status，不读正文。
- `submit` 是 Worker 命令：总编仅在自执 opening_options 门任务时使用。
- Worker 命令绝不代行：`worker-next` 只出现在派工卡里由组内 Worker 执行；主干执行 Worker 命令属越界（novel.py:218"Worker 不能执行主控或作者命令"反向同理）。
- Worker 不能执行主控或作者命令、不能 init、回执不能改投其他任务或会话（novel.py:218,227,260-262）——派工提示里不写任何治理命令。
- 不手改库、不伪造回执（novel-ledger SKILL.md:37）；不改写 schema、不修改或复制临时引擎取消判据（runtime.md:96）。

## owner 租约规则

1. `run --source 原话` 保存授权目标并返回 owner（application.py:424-450）；此后每条治理命令带 `--owner`。
2. 租约默认 300 秒（application.py:424,404）；`watch` 在引擎进程内每 30 秒自动续租（unattended.py:14-16 RENEW_EVERY）。
3. 手动延长用 `renew --owner ID [--seconds S]`（application.py:463-470）。
4. 租约过期重新 `run` 认领，**沿用已授权的实际目标，不扩大范围**（runtime.md:40）。
5. 初始认领（claim）由主干进程执行并转交 token；Worker 进程 claim 被 worker_boundary 拒绝（novel.py:211-217）。
6. 授权目标内的治理动作属 T1 直接执行；一切触碰作者字段（--source/--tier/裁决/改约/超界修订）属 T0 上报。

## watch 返回动作处置表

watch 返回后主干只做一件事：按动作处置（unattended.py:44-46 停点原样带回；runtime.md:75,77-93 动作分支）。

| action | 总编处置 |
|---|---|
| task_ready | 按返回的 task 派下一工（转发 dispatch.md+角色+task_path+一句背景），再跑一次 watch |
| wait_for_batch | 原 Worker 正在接续本组，继续 watch 等整组，**不另派工** |
| await_author（T0） | 向用户呈准确版本首章；认可后 `approve --prose-hash HASH --source 原话`；认可必须针对准确版本 |
| author_decision / paused 带裁决（T0） | 把问题+选项原样上报；用户答复后 `answer --decision-id 当前ID --option '选定label' --source 答复原话`，**再** advance（顺序红线：先 answer 后派工，答复即冻结此前派工） |
| paused（其他）/ idle | 诊断：Worker 空转（无提交、无报告）用 `advance --compact` 重派同一 pending（未提交不计返修额度），连续两次空转保留现场上报；快速组停摆先确认原执行者已停止再 `pause --cancel` 结束组、resume/advance 重开（已提交章节与额度保留，runtime.md:53） |
| revision_blocked（T0） | 呈 proposal.plan_path 完整方案（摘要字段见 runtime.md:185-191）；等用户对该 plan_hash 的 `revise --proposal-hash HASH --source 原话`；**不得用改约、重新 run 或 resume 绕过**（runtime.md:194） |
| revision_ready | 属当前授权目标=promote；不属于或作者要先看候选再决定=交作者（runtime.md:83） |
| ready_to_complete | `complete`（复验准确快照）→ 通过后 `deliver` |
| completed | 从完本快照 `deliver` 或恢复失败的交付；交付成功后结束 |
| target_reached | 刷新 html，按实际完成章节范围交付，不冒充全书完本（runtime.md:87） |
| world_ready / outline_ready | 交付返回的世界及实际卷纲覆盖；已有正文授权但未保存时用 run 保存同一授权后继续，否则到本次开书目标结束（runtime.md:88） |
| await_choice（T0） | 先贴 board.md 内容再按 question.json 选项原样提问（opening.md:28）；第一门未定向另有 catalog.md 十二类目原文贴出（opening.md:45） |
| wait_for_submit / resync / preparing | 见 runtime.md:81-83,92：等待或联系当前子 agent / 放下过期 after 重取状态 / 只对真实缺口等待作者 |

完整性失败与修复停点（projection/chain/state_integrity/source_integrity/schema、repair_exhausted、repair-stalled、remedy_exhausted）一律 T2：保留现场报告用户，不重派、不 resume 硬顶、不改判据。

## 错误码处置入口

未登记的动作和命令错误按返回的 code/details 核实修正入口，不猜测成功或无条件重试（runtime.md:94）。以下只给入口，细则以引擎文档为准：

| code | 含义与处置入口 |
|---|---|
| creation / opening_option / opening_alignment / opening_diversity / opening_voice | 开书协议与回执问题：opening.md#入口选择(:9)、#方案回执(:103)、#门序与字段归属(:55)、#结构门(:93)；旧协议拒绝见 opening.md:81、creation.py:41-42。回执字段问题回到门任务自执修正后重交 |
| author_decision / author_source | 裁决与原话缺失：runtime.md#自动回改边界（answer 顺序、第三条路走 recontract，:196-203,137）；T0 上报 |
| pilot_version | 认可版本与当前首章不符（application.py:478）：runtime.md#正式任务与提交 approve(:123)、#动作分支 await_author(:90)；重新向用户呈准确版本 |
| repair_budget / repair_exhausted / repair-stalled | 返修额度（contracts.py:64-65）与停滞：runtime.md#动作分支 paused/repair_exhausted(:91)、#暂停与修改(:130)；T2 保留现场交作者 |
| remedy_exhausted | 根问题最后一轮失败（application.py:600）：T2 上报即停 |
| revision_bounds / rewrite_limit / closed_volume / outside_recent_window | 超自动回改边界（contracts.py:67 revision_limit 默认 3）：runtime.md#自动回改边界(:177-214)；T0 呈 proposal.plan_path 等 plan_hash 授权 |
| stale_task | 裁决前冻结的派工作废（application.py:647,666）：按当前状态重新 advance 再派（runtime.md:203） |
| projection / chain / state_integrity / source_integrity / schema | 完整性失败：runtime.md:94-96；T2 上报即停，不改写 schema、不修改或复制临时引擎取消判据、不直接写库 |
| role_boundary / worker_boundary | 角色越界（novel.py:18,186-199,211-217,218,227,260-262）：runtime.md#任务交接(:102-110)；核对谁该执行这条命令 |
| controller_lease / lease / worker_lease | 租约问题：runtime.md#目标与主控认领(:38)；renew 或重新 run 认领（目标不扩大） |
| target / revision_target / writing_batch | 目标与模式约束（application.py:426-446）：runtime.md#目标与主控认领、#快速无人值守(:42) |
| worker_busy | 另一 Worker 持有任务租约（application.py:411）：runtime.md#任务交接(:108-110) |
| word_budget / drift_coverage / drift_before / outline_alignment / literal_policy | 提交时机械核算（runtime.md:121；narrative.md:236-246 引擎核算八条）：字段级问题交回当前 Worker 修正，总编不代改回执、不代填判断 |
| host_launch_failed / host_timeout / step_limit | 外部进程适配器（仅子进程宿主）：runtime.md#可选子进程适配器(:216-224) |
| file / access | CLI 层：核实文件路径与命令拼写（novel.py:225 未登记命令默认拒绝） |

## 引擎不可变声明与 T2 停点清单

- 引擎不可变：写作期间固定可信引擎；完整性错误保留现场，**不修改引擎、不复制临时补丁引擎、不直接改库后继续**（novel-ledger SKILL.md:49）；"不改写 schema，不修改或复制临时引擎来取消判据"（runtime.md:96）。SQLite 是唯一持久真源，正文和事实由 submit 原子提交（novel-ledger SKILL.md:37）。
- T2 停点清单（上报即停，保留任务、候选与失败原因）：
  1. 完整性失败：projection / chain / state_integrity / source_integrity / schema；
  2. repair_exhausted / repair-stalled（额度耗尽或同问题连续两轮未解，runtime.md:91）；
  3. remedy_exhausted（application.py:600）；
  4. resume 撞 revision_bounds / repair_budget / author_decision / remedy_exhausted 的拒绝返回（application.py:595-600）——这些停点必须先由作者处置。
- T2 处置纪律：保留现场、报告用户具体 code 与位置；不改写 schema、不修改或复制临时引擎取消判据、不直接写库、不重派硬顶。T0 类决定（裁决、超界修订）在用户答复后按原话执行；完整性问题交给用户决定处置方向。
