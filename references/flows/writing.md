# 流程 E/F：正文授权与无人值守连写

进入条件：`advance` 返回 `world_ready` / `outline_ready`（开书完成，要开始写正文），或唤醒后项目正在连写中。

前置：读 `policy.md` §2 定档；读 `engine-cli.md` §4 处置表。多项目并行时逐项目各跑本循环，每条命令与上报先报项目名。

## E 正文授权（T0）

1. `outline_ready` 时把**实际卷纲覆盖**交付用户，核对已有正文授权原话；只有目标尚未授权时才取缺失决定：写到第几章（`--through N`）还是完本（`--complete`）。已有明确授权直接保存，不重复询问；固定运行入口按 `environment.md` 核实。
2. 执行（原话逐字入账；目标不得低于已冻结任务与修订范围）：

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" run --through 40 --source '作者授权原话（逐字）'
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" run --complete --source '作者授权原话（逐字）'
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" run --through 40 --fast --source '作者授权原话（逐字）'
```

3. 模式按 `policy.md` 处置：已有明确模式沿原话执行；未指定时可在已授权目标内选择标准或快速模式，复盘注明实际模式。首章认可后，同卷顺序执笔可使用五章快速组；作者要求逐章新会话用 `--standard`。历史机械路径的费用比例不适用于新项目默认独立连续性核验，不承诺节省比例或文学质量。见 `$NOVEL_LEDGER/references/runtime.md#快速无人值守：五章一组`。
4. 保存返回的 owner；此后每条治理命令带 `--owner`。租约默认 300 秒，`watch` 在引擎进程内每 30 秒自动续租；过期则重新 `run` 认领，**沿用已授权目标不扩大**（`red-lines.md#11`）。
5. 台账追加 run 条目：完整 argv、原话、owner、目标章号、写作模式、`decision_kind`。

## F 连写主循环（T1，授权目标内）

本循环必须已有正文 `run` 返回的真实 owner；正文授权前的世界与纲要任务走 `flows/opening.md` D3。每轮：核实/预创建真实 Worker → 主干准备身份 → 宿主注入凭据并转发派工 → 等待 → 按返回动作分支。主干不读写正文，也不借核验通道代审。

### F1 主干准备执行身份

先核对任务、宿主执行者与租约：原 Worker 仍活跃或 claim.expired=false 就保留并等候；身份或活动不明则报告，不靠重派探测。`claim=null` 只表示尚未认领，租约过期也不证明旧执行者已停止。新任务由宿主创建真实独立 Worker，使其停在自举边界等待，取得真实会话 ID 后由主干准备；无法创建/等待真实执行者就报告能力缺失，不能填随机 SESSION 或借新子进程冒充空历史模型。`host-check` 只检查协议能力，不能证明宿主已创建模型。

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" prepare-worker --task "$TASK" --session "$SESSION"
```

宿主把响应 `worker_env` 仅注入该 Worker，立即交付刷新后的派工卡和生成的 commands。`ready` 只证明身份登记，不证明 Worker 正在执行或模型隔离成立；保留 task ID、真实身份和简短运行状态，不留下空挂租约。凭据不进任务文件和模型草稿，生成的 Python Worker 入口在内存中补齐身份，首条 read 自动验证 ready；不额外调用主干 read/ready。不能注入环境时，只有宿主可按权威文档把本次凭据传给外层 worker 的指定参数。见 `$NOVEL_LEDGER/references/runtime.md#执行身份与技术恢复`。

技术失败按 `details.recovery` 的 actor/action/retry_allowed 处理，与文学返修分账。已确认原因修复后，才对同一任务 `prepare-worker --reset-failures`；保留 result.json，不用 resume、换 Worker 或重派清计数。仅凭据过期时沿允许的原会话重新准备并重交原候选；真正空历史重开使用 `--fresh-context` 并重交全部必读材料，不能把已绑定快速组转给另一会话。`engine_changed` 走 environment 的准确构建恢复，不用 reset-failures 绕过。

### F2 派工

宿主注入 F1 返回的凭据后，转发 **`dispatch.md` 路径 + 角色 + `task_path` + 一句背景与简短提交状态要求** 给同一 Worker。

- 不手写环境自举、不复述协议、不改写 `commands`/`guides`；
- 背景那一句只取自本项目已同步的当前方向指纹与状态摘要；已完成重选而投影未更新时先按 `memory/templates.md` 同步，不能把原立项旧方向带给 Worker（`red-lines.md#9`、`red-lines.md#12`）；
- 快速组内 Worker 用 `worker-next` 接续；该命令 Worker-only，总编绝不代行，派工卡里可以提示 Worker 使用；
- 使用 F1 已核实或预创建的真实独立 Worker；没有该能力就保留任务并报告宿主限制，不用随机会话名或主干代写冒充派工（`red-lines.md#12`）。

### F3 等待

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" watch
```

等待在引擎进程内发生并自动续租。快速组也会因需派独立读者、原 Worker 重交或作者裁决提前返回；按实际 action 继续，不把一次返回当整组完成。

### F4 按返回动作分支

处置表在 `engine-cli.md` §4，这里只标出连写阶段最常踩的三处：

1. **`task_ready`** 派下一工（回 F1/F2），再跑一次 `watch`；`wait_for_batch` 继续等整组，不另派。
2. **`author_decision`** 把问题与选项**原样**上报，拿到答复后先 `answer` 再 `advance`——答复即冻结此前派工（`stale_task`），先派工后答复等于白派一个 Worker。
3. **`paused` / `idle`** 先按引擎 code 排除 T2、作者裁决、技术阻断及独立核验等待；后两者分别走 F1/F4b，不能普通重派。确认原执行者已停止且没有提交后，才带真实 owner `advance --compact` 重派同一 pending（未提交不计返修额度）；执行状态不明就保留现场上报，不能靠重派试探。连续两次空转保留现场上报。快速组停摆先确认原执行者已停止，再 `pause --cancel` 结束组、`resume`/`advance` 重开（已提交章节与额度保留）。`resume` 撞 `revision_bounds` / `repair_budget` / `author_decision` / `remedy_exhausted` 被拒 → 按 `policy.md` 处置。

### F4b 独立连续性核验

新 CLI 项目默认 required 连续性核验，旧项目沿用原模式；看 `status.assurance`，不自行关闭核验或降低宿主可信要求恢复。细节只按 `$NOVEL_LEDGER/references/quality.md#主控与执笔交接`。

| action | 主干动作 |
|---|---|
| `review_required` | 核实请求尚未绑定读者，保留准确候选和原执笔 Worker；实际创建另一空历史读者，取得宿主身份后 prepare-observer |
| `review_in_progress` | 原读者已绑定，沿真实 owner watch 等待并续租；不另派、不模型轮询 |
| `review_author_required` | 保留准确报告和候选，按 policy 核对裁决权限；无对应原话则交作者，不能另派读者覆盖歧义 |
| `review_complete` | 联系原执笔 Worker，保持上下文并核实有效凭据，用准确原候选重做 submit；核实 outcome 与 committed_chapter |

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" prepare-observer --request "$REQUEST" --session "$OBSERVER_SESSION"
```

宿主仅向该独立读者注入 `observer_env` 并交付返回的 commands，清除执笔 Worker 的环境。读者按引擎流程先纯读、冻结观察，再比较与报告；主干和原执笔者不运行 review-read/review-observe/review-report，不自填空报告。读者停滞先核实原执行者状态；不能用更换候选或引擎升级跳过仍关联的核验。没有真实读者能力则保留候选报告缺口。

### F5 回执与反馈

Worker 报"完成"必须核对 `outcome`、总 `findings`、`worker_boundary` 与 `committed_chapter`：`continuity_review_required` 是候选保存待核验，`repair_required` 是待返修，`chapter_committed` 才是正式入章。`accepted=true` 或 `transaction.persisted` 不能代替章节确认；`await_review` 时保留原执笔上下文，不能把它当任务已结束。

用户对当前候选正文的反馈：

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" feedback --text '作者原话'
```

已验收正文的历史修改走 `revise`（作者发起的方向性操作见 `flows/delivery.md` 附录）。

### F6 辅助命令

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" renew --seconds 300   # 手动续租
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" pause --reason '原因'  # 暂停保留现场
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" status --tasks                       # 任务生命周期
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" usage                                # read/recall 字符量
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" compact                              # 回收文档空间
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" audit                                # 只读验收检查（不豁免复验）
```

## 修订分支

`revision_blocked`（T0）：把 `proposal.plan_path` 的**完整方案**呈用户；拿到对该 `plan_hash` 的明确授权后：

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" revise --from-chapter "$N" --proposal-hash "$HASH" --source '授权原话' --reason '采纳已展示的准确修复方案'
```

不得用 `recontract`、重新 `run` 或 `resume` 绕过（`red-lines.md#10`）。旧授权不自动套到新哈希。

`revision_ready`：修订属当前授权目标 = `promote`；不属于或作者要先看候选 = 交作者决定（promote / discard）。

## 记忆

每条带 `--source` / `--reason` / `--owner` 的治理命令向台账追加一行（`decision_kind` 必填）。异常停点当场写 postmortems 草稿（code + 处置），别等复盘时回忆。

## 出口

`ready_to_complete` / `completed` / `target_reached` → `flows/delivery.md`。
