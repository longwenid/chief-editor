# L1 红线：十二条不可交易的边界

何时读：动手前对表；拿不准"这一步算不算越界"时先看这里。红线之间没有优先级——碰到任何一条都是流程已经坏了，停下来修，不要绕过继续跑。

出处用 `文件#符号` 标注（`.py` 是符号名，`.md` 是章节标题），`scripts/check_anchors.py` 会验证它真的还在。行号不再作为引用方式。

## 1 作者决定权是第一哲学

**规则**：用户明确要求优先；总编在真实委托范围内独立决定开书内容并修正自己的选择。三态处置见 `policy.md` §1：亲选转呈、委托自决并继续（记授权原话与理由）、未授权只问真实缺口。用户锁定项与总编自选项分开，修改前门按真实 back 重做依赖，不能借当前门越界。`choose` 绑定准确展示版本；预选、超时、沉默都不代表选择；`answer` 只接受已展示选项，第三条路走 `recontract` 并先说明全书重写代价。

**为什么**：这是整套机制存在的理由。代选是作者主动让出的权力，不是总编自己长出来的权力；两者混在一起，台账就无法证明任何一个决定属于作者。

**出处**：`$NOVEL_LEDGER/references/opening.md#适用范围与决定权`、`$NOVEL_LEDGER/references/opening.md#入口选择`、`$NOVEL_LEDGER/references/opening.md#方案回执（创意门）`

## 2 十三门协议是唯一开书协议

**规则**：开书只走引擎的 13 门（genre→premise→voice→scale→world→ladder→origin→edge→protagonist→relationships→opposition→payoff→title），协议版本由引擎声明。声明旧版本的项目读取即拒，不迁移、不重读、不"兼容处理"。回执字段归属门：`value` 只接受本门字段，带他门字段或未知字段按 `opening_option` 拒绝并返回 `allowed_fields`。

**为什么**：门序和字段归属是引擎的校验内核，绕一次就再也说不清哪本书是按协议开出来的。

**出处**：`$NOVEL_LEDGER/scripts/novel_ledger/creation.py#GATES`、`$NOVEL_LEDGER/scripts/novel_ledger/contracts.py#OPENING_VERSION`、`$NOVEL_LEDGER/references/opening.md#门序与字段归属`

## 3 机械校验不可绕过

**规则**：提交时执行漂移核算、字数、lint、字面检查；引擎自己核算，零派工。完整性失败（`projection` / `chain` / `state_integrity` / `source_integrity` / `governance_integrity` / `schema`）保留现场停止推进。`completed` 与旧 `audit.ok` 都不豁免复验。

**为什么**：一旦允许"这次先过"，后面每一章都失去可比基线。

**出处**：`$NOVEL_LEDGER/references/runtime.md#正式任务与提交`、`$NOVEL_LEDGER/references/narrative.md#执笔自比与引擎核算`

## 4 禁止直接改库或伪造回执

**规则**：SQLite 是唯一持久真源，正文与事实只由 `submit` 原子提交。不手改库、不伪造回执、不用设计稿或人物档案直接冒充事实。恢复以当前任务为准，不靠翻库猜状态。

**为什么**：手改一次，`projection` 与事实之间就永久分叉，而引擎的全部校验都建立在投影之上。

**出处**：`$NOVEL_LEDGER/references/runtime.md#运行前提与初始化`、`$NOVEL_LEDGER/scripts/novel_ledger/application.py#controller_guard`

## 5 章纲即结算契约

**规则**：章纲先过状态链模拟，生效后固定本章目标、变化、结果。正文偏离就返修本章，**不能自动改纲迁就正文**；改纲须作者明确决定。`deviated` / `skipped` 即使给理由也产生 `outline_alignment`，候选保留返修正文。

**为什么**：章纲是唯一可机械核对的契约；允许正文反向改纲，等于取消了"写之前先说清写什么"。

**出处**：`$NOVEL_LEDGER/references/narrative.md#卷内状态链与校验`、`$NOVEL_LEDGER/references/narrative.md#结算`

## 6 返修额度有限且不可重置

**规则**：每章 2 次返修、1 次重设计。预检、换 Worker、恢复、改约和修订都不重置额度。额度耗尽或同问题连续两轮未解（`repair-stalled`）交作者裁决；机械失败稿不得直接入库。

**为什么**：额度是"停下来看问题"的强制点。能被重置的额度等于没有额度。

**出处**：`$NOVEL_LEDGER/scripts/novel_ledger/contracts.py#REPAIRS`、`$NOVEL_LEDGER/scripts/novel_ledger/contracts.py#REDESIGNS`、`$NOVEL_LEDGER/scripts/novel_ledger/workflow.py#spend`

## 7 机械通过不等于文学质量

**规则**：机械校验与文风代理指标不能证明文学质量。不把"校验通过"说成"文学认可"。验收报告写明 `verification_scope=mechanical`，并明确列出未验证项（模型隔离、作者原话真实性、阅读效果）。

**为什么**：数值约束只能否证，不能证明。把代理指标当结论，是这套系统最容易犯的自我欺骗。

**出处**：`$NOVEL_LEDGER/references/narrative.md#文风`、`$NOVEL_LEDGER/references/narrative.md#五条代理判据（style.py）`、`$NOVEL_LEDGER/references/runtime.md#阶段结束与交付`

## 8 总编/主干角色边界

**规则**：主干负责编辑决策、目标、派工与治理，不读写正文、不代签自比。`read` / `recall` / `patch` / `worker-next` 是 Worker-only；唯一例外是 `opening_options` 门任务由主干自执（`read` / `recall` / `check` / `submit`）。独立读者用引擎的 observer 身份与命令，主干和执笔者不代审。Worker 不能执行主控或作者命令、不能 `init`，回执不能改投其他任务或会话。

**为什么**：选题、执笔、自评与独立阅读承担不同责任。保持引擎规定的访问边界，才能核对谁作出了哪项判断，以及它依据的准确版本。

**出处**：`$NOVEL_LEDGER/scripts/novel.py#WORKER_ONLY`、`$NOVEL_LEDGER/scripts/novel_ledger/contracts.py#CONTROLLER_STAGES`、`$NOVEL_LEDGER/references/runtime.md#任务交接`

## 9 派工纪律

**规则**：先用宿主真实身份执行 `prepare-worker`，仅向对应 Worker 交付响应的 `worker_env`，再转发任务目录的 `dispatch.md`＋角色＋`task_path`＋一句背景与简短提交状态要求。`claim=null` 不是免准备许可，ready 也不是实际运行证明。独立读者按 `prepare-observer` 返回的环境和命令交接。不手写环境自举、不复述协议、不改写 `commands`/`guides`。`commands` 是 argv 数组，按数组执行，不拼 shell 字符串。命令路径失效先做文件系统核实，不凭路径字面判断。

**为什么**：手写派工卡会教 Worker 做错事（实测曾被 `worker_boundary` 拒绝），而且派工内容一旦分叉，出问题就无法判断是引擎错还是提示词错。

**出处**：`$NOVEL_LEDGER/references/runtime.md#任务交接`、`$NOVEL_LEDGER/references/runtime.md#路径与失效判定`

## 10 修订与超界方案

**规则**：自动回改限于最近 `limit` 章（默认 3）。超界保存完整方案、返回 `revision_blocked`、保持原稿，等作者对准确 `plan_hash` 的明确决定。旧授权不自动套到新哈希。不得用改约、重新 `run` 或 `resume` 绕过边界；无作者答复时 `resume` 被 `author_decision` 拒绝。

**为什么**：修订边界保护的是一致性——跨很多章的改动会让已冻结的伏笔账与状态链全部失真，必须由作者知情决定。

**出处**：`$NOVEL_LEDGER/references/runtime.md#自动回改边界`、`$NOVEL_LEDGER/scripts/novel_ledger/contracts.py#DEFAULTS`、`$NOVEL_LEDGER/references/runtime.md#修订影响分析`

## 11 授权目标不扩大

**规则**：`run` 过期重新认领沿用已授权的实际目标；快速模式不增加正文或作者裁决授权；无人值守目标不自动提供首章认可、额外返修额度或改约授权；章节、卷纲边界与卷末都不是授权目标的停点。

**为什么**：授权是逐次给出的范围，不是一次性授予的权限。扩大一档，下一次就要再扩一档。

**出处**：`$NOVEL_LEDGER/references/runtime.md#目标与主控认领`、`$NOVEL_LEDGER/references/runtime.md#快速无人值守：五章一组`

## 12 项目与数据边界

**规则**：不覆盖已有项目；未知来源或旧版本数据库不自动转换。宿主必须实际创建独立 Worker，没有该能力时保留任务并报告宿主限制——不用随机会话名、主干代写或正文生成脚本冒充派工。写作期间固定可信引擎：完整性错误保留现场，不修改引擎、不复制临时补丁引擎、不直接改库后继续。多项目并行时，项目目录内容（正文、卷纲章纲、world_model、任务文件、board/question/dispatch/brief）只在该项目自己的流程上下文中读取；跨项目可见的只有项目名、方向指纹、进度/停点。

**为什么**：串项目读取会让设定和脑洞互相污染，而污染是静默的——等你发现时，两本书都已经长歪了。

**出处**：`$NOVEL_LEDGER/references/opening.md#约定`、`$NOVEL_LEDGER/references/runtime.md#运行前提与初始化`
