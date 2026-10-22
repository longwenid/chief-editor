# 流程 E/F：正文授权与无人值守连写

进入条件：`advance` 返回 `world_ready` / `outline_ready`（开书完成，要开始写正文），或唤醒后项目正在连写中。

前置：读 `policy.md` §2 定档；读 `engine-cli.md` §4 处置表。多项目并行时逐项目各跑本循环，每条命令与上报先报项目名。

## E 正文授权（T0）

1. `outline_ready` 时把**实际卷纲覆盖**交付用户，核对已有正文授权原话；只有目标或模式尚未授权时才取缺失决定：写到第几章（`--through N`）还是完本（`--complete`）；标准还是快速模式。已有明确授权直接保存，不重复询问。
2. 执行（原话逐字入账；目标不得低于已冻结任务与修订范围）：

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" run --through 40 --source '作者授权原话（逐字）'
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" run --complete --source '作者授权原话（逐字）'
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" run --through 40 --fast --source '作者授权原话（逐字）'
```

3. 同卷顺序执笔可建议快速组（`--fast`，五章一组）：实测每章约省 54% 且返修率不劣（引擎 `validation/` 下 2026-10-22 成本实测）。已有明确模式沿原话执行，只有模式缺失时才问；成本数据是执行建议，不替代授权。作者要求逐章新会话用 `--standard`。
4. 保存返回的 owner；此后每条治理命令带 `--owner`。租约默认 300 秒，`watch` 在引擎进程内每 30 秒自动续租；过期则重新 `run` 认领，**沿用已授权目标不扩大**（`red-lines.md#11`）。
5. 台账追加 run 条目：完整 argv、原话、owner、目标章号、写作模式、`decision_kind`。

## F 连写主循环（T1，授权目标内）

本循环必须已有正文 `run` 返回的真实 owner；正文授权前的世界与纲要任务走 `flows/opening.md` D3。每轮：核实/预创建真实 Worker → 必要时主干认领 → 转发派工 → 等待 → 按返回动作分支。

### F1 主干认领

先核对任务和宿主执行者：原 Worker 仍活跃就保留它并等候，不重派。新任务先由宿主预创建独立 Worker、取得真实会话 ID，再进行下面的认领，认领完成后才让它执行任务。宿主不支持预创建/暂停执行时，只能用派工视图允许的无认领路径，或报告能力限制，不能填随机 SESSION。`claim=null` 指**派工视图**无需认领，可跳过下面命令；实际调用 `claim` 成功会返回 token。

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" claim --task "$TASK" --session "$SESSION"
```

初始认领必须由主干进程执行（Worker 自己 `claim` 会被 `worker_boundary` 拒绝）。返回 token 转给同一真实 Worker，填入其回执顶层 `execution_claim`（裸字符串）；不得把已绑定的快速组改交另一会话。

### F2 派工

转发 **`dispatch.md` + 角色 + `task_path` + 一句背景** 给 Worker。

- 不手写环境自举、不复述协议、不改写 `commands`/`guides`；
- 背景那一句只取自本项目的方向指纹与状态摘要（`red-lines.md#9`、`red-lines.md#12`）；
- 快速组内 Worker 用 `worker-next` 接续；该命令 Worker-only，总编绝不代行，派工卡里可以提示 Worker 使用；
- 使用 F1 已核实或预创建的真实独立 Worker；没有该能力就保留任务并报告宿主限制，不用随机会话名或主干代写冒充派工（`red-lines.md#12`）。

### F3 等待

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" --owner "$OWNER" watch
```

零主干推理、自动续租。快速模式等整组结束。

### F4 按返回动作分支

处置表在 `engine-cli.md` §4，这里只标出连写阶段最常踩的三处：

1. **`task_ready`** 派下一工（回 F1/F2），再跑一次 `watch`；`wait_for_batch` 继续等整组，不另派。
2. **`author_decision`** 把问题与选项**原样**上报，拿到答复后先 `answer` 再 `advance`——答复即冻结此前派工（`stale_task`），先派工后答复等于白派一个 Worker。
3. **`paused` / `idle`** 先按引擎 code 排除 T2 与作者裁决。确认原执行者已停止且没有提交后，才带真实 owner `advance --compact` 重派同一 pending（未提交不计返修额度）；执行状态不明就保留现场上报，不能靠重派试探。连续两次空转保留现场上报。快速组停摆先确认原执行者已停止，再 `pause --cancel` 结束组、`resume`/`advance` 重开（已提交章节与额度保留）。`resume` 撞 `revision_bounds` / `repair_budget` / `author_decision` / `remedy_exhausted` 被拒 → 按 `policy.md` 处置。

### F5 回执与反馈

Worker 报"完成"必须核对返回里的 `committed_chapter`——`accepted=true` 只表示回执已受理，可能仍产生返修候选。

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
