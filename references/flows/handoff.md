# 流程 H：交接 novel-ledger

进入条件：十三门全部完成（title 门已 `choose`，引擎约定激活），`advance` 返回 `world_model` / `opening_contract` / `volume_outline` / `chapter_outline` 任一任务；或唤醒时发现项目已过约定激活。

总编的职责到开书选择为止。世界与纲要设计、正文授权、无人值守连写、修订与交付全部由 novel-ledger 技能执行——那是已做过成本优化的低成本宿主（后台 Worker + watch 等待，主控不逐条跑引擎命令）。总编不执行 `run` / `watch` / `prepare-worker` / `prepare-observer` / `revise` / `complete` / `deliver` 等写作阶段命令，也不派任何写作 Worker。

## H1 交付开书成果

用只读命令核对落定状态，向用户交付**开书成果摘要**（不读正文——开书阶段尚无正文）：

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" status
```

摘要包含：书名与题材、读者承诺、世界档位与阶梯、主角与对手关系、主题锚点、卷数与章数区间、立项记录定位（decisions 文件与方向指纹）。数字与判断全部来自引擎状态与 decisions 证据块，不自拟。

## H2 交接卡

向用户输出交接指引，内容固定三行：

1. **项目路径**（绝对路径）与当前状态（约定已激活，下一步任务阶段名）；
2. **恢复方式**：在项目所属目录新开一个会话，使用 novel-ledger 技能，对它说"恢复项目 `$PROJECT` 继续写"——novel-ledger 会沿引擎状态自动接手世界模型、卷纲、章纲与正文连写；
3. **编辑资产定位**：decisions 记录（方向指纹、选题依据）与 market/teardowns 快照路径，供后续复盘引用。

交接即结束本次总编流程。不为"省一次切换"而在总编会话里代跑写作命令——主会话每多一次引擎往返就多一次全量上下文重发（实测单请求 200K+ tokens），这正是本流程存在的理由。

## H3 台账

交接本身追加一行台账：`decision_kind=author`，argv 记 `handoff`，原话记用户本轮指令，返回记交接时的引擎状态与下一步阶段名。此后该项目的推进命令不再由本技能产生；novel-ledger 阶段的治理留痕走它自己的流程。

## H4 唤醒时遇到已过激活的项目

唤醒发现项目已过约定激活（世界/纲要/正文/交付任一阶段）：

- 只读回答进度可以：`status --tasks` 摘要 + 指回 H2 的恢复方式；
- 不 `advance`、不 `watch`、不认领 owner、不重派任务——即使台账里有历史 owner 也不沿用（那是写作阶段租约，归 novel-ledger 管辖）；
- 用户要求"继续写/写到哪了/修订/交付"时，直接给出 H2 交接指引，不展开写作编排。

## 记忆

decisions 的 `control.status` 保持 `active`。完本交付（`delivered`）或作者明确搁置（`shelved`）的回写只在用户把 novel-ledger 阶段的真实结果回告总编时进行；总编不主动查询或推断写作阶段结果。

| 用户回告的结果 | decisions.status |
|---|---|
| `partial_delivery` / `t2_stop` / 交接后仍在写作 | `active` |
| `completed_and_delivered`（novel-ledger 完本复验与正式交付均成功） | `delivered` |
| `author_shelved`（作者明确搁置） | `shelved` |

## 出口

交接完成 → 流程结束。用户回告交付结果 → 按模板回写 decisions 状态并写复盘（`memory/templates.md` §5）。
