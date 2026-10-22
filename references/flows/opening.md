# 流程 D：开书十三门

进入条件：立项已落定、项目目录已选定。

唯一开书协议：13 门固定门序 `genre → premise → voice → scale → world → ladder → origin → edge → protagonist → relationships → opposition → payoff → title`。门序不可换、不可跳、不可"合并成一次问"。协议版本由引擎声明，声明旧版本的项目读取即拒（`red-lines.md#2`）。

档位：本流程几乎全是 T0 入口，逐门见 `policy.md` §2；门任务判分与提交属 T1 自执。

## D0 建项目（零输入逐门）

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" init
```

零输入 `init` 不要求 `--source`。已有约定的项目不得再次 `init`。

## D0b 分支：作者已定部分门值

`init` 后、尚未展示方案且无 pending 时，把作者原话整理成 `要求.json`（**键必须是门 ID**，字段名当键会被拒并返回 `valid_gates`；只存作者已定的值，不替缺口补造决定）：

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" intake --file 要求.json --source '作者原话'
```

## D0c 分支：作者给完整约定且未派过门任务

```bash
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" opening --file 约定.json --source '作者原话'
```

派过门任务后此命令被拒，改用 `recontract`（T0）。

## D1 逐门自执四步（每门重复）

```bash
# ① 取任务与 task_path
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" advance --compact
# ② 读 task_path 下的 brief.md（读盘；input.json 是同一内容的 JSON 原文，不必解析）
# ③ 读必读记录（opening_options 阶段对主控放行）
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" read --task "$TASK"
# ④ 从 task_path/result.template.json 复制起稿 result.json（只填 data，信封三字段不手写），
#    试算通过后提交；session 填主干自己的会话身份（门任务不绑定会话）
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" check --file "$TASK_PATH/result.json"
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" submit --file "$TASK_PATH/result.json"
```

`checked` ≠ 已提交；`submit` 返回 `accepted` 才算落账。

门任务自执是主干读正文的唯一例外（`opening_options` 阶段），`red-lines.md#8`。

## D2 await_choice 处置（全部 T0）

1. 先把引擎物化的 `work/board.md` 内容**原样**贴给用户（或给文件链接），再按 `work/question.json` 的选项**原样**发起提问——不自拟摘要、不替换引擎文案、不把字段/哈希/命令展示给用户。
2. 第一门（genre）作者未给方向时：把任务目录 `catalog.md` 十二类目**原文**贴进对话（铺目录是正文文本步骤，不是提问选项）。曾有一次把四个类目塞进选项，结果其余八个类目从作者视野里消失。
3. 用户答复后执行其一（有委托原话时按 `policy.md` §3 代行并照记台账）：

```bash
# 普通门选择（方案 id 用展示组里的真实 id，不一定是 A/B/C）
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" choose --option "$OPTION" --board "$BOARD" --source '用户原话'
# 结构门（scale）档位直达
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" choose --tier t5 --source '用户原话'
# 用户否决当前组（新组须与被拒组实质不同，并吸收用户随换组补充的偏好）
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" regroup --board "$BOARD" --reason '换一组'
# 用户要改已选门（保留前门；后续依赖门归档后重选）
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" back --gate "$GATE" --reason '原因'
```

旧组编号不能套新门——传错 id 被拒并返回 `valid_options`，按 `valid_options` 重新问用户。预选、超时、沉默都不代表选择。

4. 每次 `choose` / `regroup` / `back` 后向台账追加一行（用户原话；代选时授权原话＋当次理由）。

## D2b 不满意时输入自己的需求

总编可以批评并提出要求，不必从不满意的板面机械挑一个。先原样展示当前板面，再把自己的编辑判断单列：具体哪里不成立、希望产生什么阅读体验、代价是什么，依据见 `references/editorial-judgment.md`。亲选按用户原话；委托代选只在仍有效且覆盖本次细化的范围内自主执行；未授权则把批评和建议交作者，保留板面等待决定。

1. 写清三件事：**拒绝原因、必须保留的具体机制/字段、新要求**；可附自拟候选的概念，但它此时只是生成要求。不能只写“再高级一点”或“保留 B 的优点”。拒绝记录向下轮只传本门 reason 与旧标题/pitch，不带旧完整 value，因此保留项要展开写。要改变已确认主线、风格、目标或授权范围时，先取得作者明确新决定；不得借换组推翻前门。
2. 用只读规划器检查请求并生成 argv。它只检查声明形状和治理上限，**不证明授权、哈希、历史或 owner 属实**；调用方必须按当前板面与台账核对。

```bash
python3 "<chief-editor>/scripts/plan_opening_request.py" --engine "$NOVEL_LEDGER" 请求.json
```

请求 JSON 字段：`project`（本项目绝对路径）、`gate`、`board_hash`（当前 64 位哈希）、`decision_kind`（author/delegated）、`source_quote`（逐字）、`authority_covers_refinement`、`changes_confirmed`（将改变的 mainline/style/target/scope，未改变则空数组）、`rejection_reasons`、`retain`、`requirements`、`prior_custom_regroups`；可选 `self_proposed` 和恢复出的真实 `owner`。原因与要求是文本数组，`requirements` 与自拟概念至少一项非空。没有任意命令/脚本字段。

| 规划状态 | 处置 |
|---|---|
| `planned` | 核对声明后逐参数执行返回的 `argv`；命令是已有 `regroup --board HASH --reason ...`，不拼 shell 字符串 |
| `needs_author` | 授权不足或改变已确认项；交付具体提案并等待，不能执行任何返回外的猜测命令 |
| `stopped` | 本项目同门自定义换组已累计两轮；保留历次要求、结果与仍未解决项报告作者 |
| `unsupported` | 例如 scale 系统门：只支持真实 t0～t5 及窗口滑动，不生成自拟档位；说明差距，回真实 choose --tier 或交作者 |
| `invalid` | 修正输入或核对现场，不当作引擎已接受 |

3. `regroup` 成功后重新 `advance`，按 D1 自执真实 `opening_options` 门任务：读含 `opening_rejections` 的必读记录，在已有选择与本门合法字段内生成 2～3 个实质不同候选。自拟概念可成为其中一个候选，不能只交一个方案或私造新门。
4. `check` → `submit` → 重新展示 board/question → 在有效授权内对**新哈希、真实选项 ID**执行 `choose`。引擎没有 `choose --text`、特殊 `custom` ID 或任意自由文本直选入口。`intake` 仅在尚未展示且无 pending 的原有入口适用，不能用来绕过当前板面。新组仍需逐项核对是否解决拒绝原因，机械通过不证明跨组语义新颖。
5. 每次向现有授权台账追加 `request_kind=custom_opening`、门 ID、累计轮次、完整 reason、板面哈希与实际返回；尝试被拒也记。同门最多两轮，跨会话、换板或 back 都不清零；作者明确追加范围时另记原话与新的有限上限，规划器仍保守停下，由作者路径处理。不得用空泛换组无限循环。

`regroup` 的 reason 会入引擎历史并进入**本门**下轮记录（`$NOVEL_LEDGER/scripts/novel_ledger/creation.py#regroup`、`$NOVEL_LEDGER/scripts/novel_ledger/context.py#build`）；不自动成为后门或全书持久约束。需要长期保留的内容必须落实到已校验并选定的合法 value，再在后续门核对同一读者承诺。scale 换组只滑系统档位窗口，不经过创意 Worker。

## D3 世界与纲要设计（正文授权前）

十三门全部完成后，按引擎返回依次处理 `world_model` / `opening_contract` / `volume_outline` / `chapter_outline` 的实际任务，不自行猜门序后的下一任务。此时尚未正文 `run`，通常没有 controller owner；约定未激活时 `run` 也会被引擎拒绝，不能为取得 owner 提前保存正文授权。

1. 按 `flows/writing.md` F1/F2 的宿主身份与转发规则创建真实独立 Worker。尚无 owner 时，只有需要 Worker 认领的任务才由主干调用不带 `--owner` 的 `claim`；派工视图 `claim=null` 表示可直接派工，不是 claim 命令会返回 null。
2. 保留 task ID 与真实 Worker 身份，等宿主的提交/结束事件。**不调用 `watch` 或 `renew`**，不编造 owner；活跃 Worker 存在时不再次 `advance`。宿主无法核实原执行者状态时保留任务并报告，不能用重派探测。
3. Worker 结束后先用 `status --tasks` 核对任务生命周期；已提交则带准确 `--after` 取下一步。若 Worker 已停止且没有提交，可重新物化同一 pending 并恢复派工，连续两次空转就保留现场报告；停点或错误按权威处置表处理。

```bash
# 仅限从未正文 run 的开书设计阶段；需要认领时才执行
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" claim --task "$TASK" --session "$SESSION"
# 已核实提交的设计任务
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" advance --compact --after "$DONE_TASK"
# 无 pending，或已确认原执行者停止且需恢复同一任务时
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" advance --compact
```

| run 状态 | 允许的等待 | 提交后推进 |
|---|---|---|
| `not_started` | `host_event` | `advance_after`（不带 owner） |
| `authorized` | `watch`（携带真实 owner） | `watch` 返回下一 action，沿原授权进入 writing F4 |

收到 `outline_ready` 后交付世界视图与**实际卷纲覆盖**。已有明确正文授权就按同一原话保存，只有缺失时才询问；拿到真实 owner 后进入 writing F 循环。`world_ready` 若尚缺实际卷纲覆盖，仍依当前引擎阶段处理设计交付，不能跳过纲要或把设计完成当作正文授权。

## 记忆

门选择与原话由引擎入库（`book.decisions`）；总编只在 `authorization.md` 追加原话与停点。配合 decisions 里已有的方向指纹，保持门选择与立项主见不互相打脸。

genre / premise / voice / payoff 的选择理由回指立项记录中的同一读者承诺和审美取舍；新增证据导致调整时说明依据并核对作者权限。长期兑现沿引擎已有约定、章纲、伏笔/线路与实际 Worker 报告检查，不另建承诺结算账本；开篇机械通过不能推成全书优秀。

## 出口

设计 `task_ready` → 本节；`outline_ready` 且已有明确正文授权 → `flows/writing.md` E 保存同一授权；没有正文授权则交付开书成果并停在授权入口。
