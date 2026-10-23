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

`init` 后、尚未展示方案且无 pending 时，把作者已经明确决定的完整门值整理成 `要求.json`（**键必须是门 ID**，字段名当键会被拒并返回 `valid_gates`）。作者给了核心概念并委托其余内容时，只导入已定值；缺口由总编沿逐门流程在委托内形成候选并代选，不把委托原话包装成作者已定的具体值。只有方向而没有该门完整 value 时，作为本门生成要求，不补造可跳门的决定。

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

1. 先读当前 `work/board.md`、`work/question.json` 并核对真实选项与展示版本，再按 `policy.md` 的决定权分支处理：**亲选**时原样贴板面（或给文件链接），按 question 原文提问并等真实答复；**委托代选**时核对有效委托覆盖本门，比较候选、写明当次选择与理由后直接执行并继续，板面链接留作可审阅依据，不发起需要用户答复的提问；**权限缺口**先查当前原话及台账，确有缺失才就缺口询问。给用户的板面不自拟摘要、不替换引擎文案、不展示字段/哈希/命令。
2. 第一门（genre）尚未定向且需作者亲选时：把任务目录 `catalog.md` 十二类目**原文**贴进对话（铺目录是正文文本步骤，不是提问选项）。已有作者方向或总编在有效委托内落定的立项方向时，在该方向内出案；委托全权选题时总编自行比较目录，不再要求用户先选类目。
3. 亲选用用户答复，委托用有效授权原话加当次理由，按当前板面的真实数据执行其一；引擎默认亲选的交互文案不要求在已有委托后再索取一次选择，版本绑定、合法选项和实际宿主约束仍然遵守：

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

旧组编号不能套新门——传错 id 时重读当前板面并核对 `valid_options`：委托范围内重新决策，亲选原答复无法对应当前组时才请用户重选。预选、超时、沉默都不代表选择；有效委托内的明确代选也不依赖用户再次答复。

4. 每次 `choose` / `regroup` / `back` 后向台账追加一行（用户原话；代选时授权原话＋当次理由）。

## D2b 不满意时输入自己的需求

总编可以批评并提出要求，不必从不满意的板面机械挑一个。先核对当前板面，再把自己的编辑判断单列：具体哪里不成立、希望产生什么阅读体验、代价是什么，依据见 `references/editorial-judgment.md`。交互沿 D2：亲选展示等待；委托内自行取舍并继续；已有决定先沿用，只向作者补取真实缺口。

1. 写清三件事：**拒绝原因、必须保留的具体机制/字段、新要求**；可附自拟候选的概念，但它此时只是生成要求。拒绝记录向下轮只传本门 reason 与旧标题/pitch，不带旧完整 value，因此保留项要展开写。涉及已选门（含 intake 预填门）时，从引擎门选择与原台账辨明来源：`author_locked` 是作者明确锁定的内容；`editor_selected` 是总编在委托内选定、作者未另行锁定的内容。来源不明不能擅自归为总编自定。用户本次已明确改变锁定项，或有效委托明确覆盖回退总编自定项时，沿已有决定执行；只有授权缺失才询问。已选门变更必须走真实 `back`，不得借当前门换组偷改；正文目标、模式或激活后改约不走本规划器。
2. 用只读规划器检查请求并生成 argv。它只检查声明形状和治理上限，**不证明授权、哈希、历史或 owner 属实**；调用方必须按当前板面与台账核对。

```bash
python3 "<chief-editor>/scripts/plan_opening_request.py" --engine "$NOVEL_LEDGER" 请求.json
```

请求 JSON 基础字段：`project`（本项目绝对路径）、`gate`、`board_hash`（当前 64 位哈希）、`decision_kind`（author/delegated）、`source_quote`（逐字）、`authority_covers_refinement`、`changes_confirmed`（本次涉及开书已选门的 mainline/style/target/scope，未改变则空数组）、`rejection_reasons`、`retain`、`requirements`、`prior_custom_regroups`；可选 `self_proposed` 和恢复出的真实 `owner`。原因与要求是文本数组，`requirements` 与自拟概念至少一项非空。没有任意命令/脚本字段。

需要回退或追加额度时另填：

- `confirmed_change_context: [{field, gate, origin, decision_ref, selection_method?}]`：逐项且无重复地匹配 `changes_confirmed`；gate 必须在引擎当前有效已选记录中，origin 为上述两类来源，decision_ref 定位原选择或授权台账，不能仅凭门序推定已选。selection_method 为 `choose`（旧请求默认）或 `intake`；后门预填须明确 `intake` 并核对原记录，可用 `option.id=author:<gate>`、空 `board_hash` 及原话确认。当前待选门不能同时声明已选，普通未选门不能冒充预填。
- `change_authorization: {kind, quote, source_ref, fields}`：kind 为 `current_author_decision`（用户本次明确改变）或 `delegated_backtrack`（仍有效且覆盖回退的委托）；quote 逐字，source_ref 定位真实原话，fields 精确覆盖本次变更。后者只能改 `editor_selected`。调用方必须核对原话确实覆盖这些变更；填入非空文本不构成授权证明。旧请求缺这些依据仍保守停下，先找已有记录，不直接重复问。
- `regroup_extension: {limit, quote, source_ref}`：用户本次明确追加的有限**累计总上限**（整数且大于默认两轮），逐字原话及消息定位；不得自行推定或从“继续”扩大额度。调用方核对范围是本项目、本门和对应次数；历史累计不清零。后续会话沿台账恢复这条仍有效的追加决定，无需再授权一次。只用于当前门 regroup；back 请求不混入额度追加，回退后针对实际门另行规划。

| 规划状态 | 处置 |
|---|---|
| `planned` | 核对声明后按 `action` 执行返回 `argv`：`regroup` 绑定当前板面；`back` 回最早受影响门并留痕，随后按门序重做。均不拼 shell 字符串 |
| `needs_author` | 依据或权限不足；先恢复已有决定、核对来源，只有真实缺口才交付提案等待，不执行猜测命令 |
| `stopped` | 本项目同门已达有效有限上限（默认两轮）；保留历次要求、结果与未解决项。已有明确追加原话时带 extension 重新规划，未获追加才停 |
| `unsupported` | 例如 scale 系统门：只支持真实 t0～t5 及窗口滑动，不生成自拟档位；说明差距，回真实 choose --tier 或交作者 |
| `invalid` | 修正输入或核对现场，不当作引擎已接受 |

3. `regroup` 成功后重新 `advance`，按 D1 自执真实 `opening_options` 门任务；`back` 成功后 `advance` 返回**最早未选门**，可能仍是 genre，而非 `back_gate`（例如 genre 未选时修改已 intake 的 voice）。按实际返回取任务或系统板，再依门序恢复后续设计。旧板面和受影响后门选择已失效，不能套用旧哈希/旧 ID。读真实必读记录，在本门合法字段内生成 2～3 个实质不同候选；保留未获变更授权的原内容。自拟概念可成为其中一个候选，不能只交一个方案或私造新门。
4. 创意门 `check` → `submit` → 核对新 board/question → 按 D2 亲选或委托分支，对**新哈希、真实选项 ID**执行 `choose`。引擎没有 `choose --text`、特殊 `custom` ID 或任意自由文本直选入口。`intake` 仅在尚未展示且无 pending 的原有入口适用，不能用来绕过当前板面。新组仍需逐项核对是否解决拒绝原因，机械通过不证明跨组语义新颖。
5. 每次向现有授权台账追加 `request_kind=custom_opening`、实际 action、门 ID、累计轮次、完整 reason、板面哈希与实际返回；尝试被拒也记。回退另记变更字段、原决定定位、来源分类、变更授权定位及 `back_gate`，使用规划返回的 `command_decision_kind`。同门换组默认最多两轮，跨会话、换板或 back 都不清零；back 本身不计一次 regroup，也不恢复额度。追加时记录原话、定位与新累计总上限，按 extension 执行至有限上限。不得用回退或空泛换组无限循环。

`regroup` 的 reason 会入引擎历史并进入**本门**下轮记录（`$NOVEL_LEDGER/scripts/novel_ledger/creation.py#regroup`、`$NOVEL_LEDGER/scripts/novel_ledger/context.py#build`）；不自动成为后门或全书持久约束。需要长期保留的内容必须落实到已校验并选定的合法 value，再在后续门核对同一读者承诺。scale 换组只滑系统档位窗口，不经过创意 Worker。

`back` 的 reason 留在引擎历史，不自动成为 `opening_rejections`；总编恢复回退流程时从现有台账带入本次变更、保留项与授权原话，按新任务合法字段重新落实。记录定位指向原真源，不复制另一套小说事实。

## D3 世界与纲要设计（正文授权前）

十三门全部完成后，按引擎返回依次处理 `world_model` / `opening_contract` / `volume_outline` / `chapter_outline` 的实际任务，不自行猜门序后的下一任务。此时尚未正文 `run`，通常没有 controller owner；约定未激活时 `run` 也会被引擎拒绝，不能为取得 owner 提前保存正文授权。

1. 按 `flows/writing.md` F1/F2 创建真实独立 Worker，使其先等候身份准备。尚无 owner 时，由主干执行不带 `--owner` 的 `prepare-worker`；仅向该 Worker 交付返回的 `worker_env`，再转发刷新后的 `dispatch.md` 与任务路径。`claim=null` 只表示尚未认领，所有新的设计 Worker 都须准备身份；ready 仅表示登记成功，不能当作已开工或完成。无法交付真实身份的宿主保留任务并报告能力缺口。
2. 保留 task ID 与真实 Worker 身份，等宿主的提交/结束事件。**不调用 `watch` 或 `renew`**，不编造 owner；活跃 Worker 存在时不再次 `advance`。宿主无法核实原执行者状态时保留任务并报告，不能用重派探测。
3. Worker 结束后先用 `status --tasks` 核对任务生命周期；已提交则带准确 `--after` 取下一步。若 Worker 已停止且没有提交，先保留 result.json 并核实执行失败原因，按引擎恢复提示为同一任务重新准备身份；确需刷新视图时才重新 advance。技术阻断须修复原因后才使用 prepare-worker 的 reset-failures，不靠换人清零；连续两次空转保留现场报告。停点或错误按权威处置表处理。

```bash
# 仅限从未正文 run 的开书设计阶段；SESSION 来自真实宿主
python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" prepare-worker --task "$TASK" --session "$SESSION"
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

门选择与原话由引擎入库（`book.decisions`）；总编在 `authorization.md` 追加原话、当次判断与停点。`author_locked` / `editor_selected` 由原门选择和授权来源恢复，后续作者明确锁定时以新原话为准，不另建决定或小说事实账本。回退后 genre/premise 实际重选完成时，按 `memory/templates.md` 的“当前方向同步”追加旧/新指纹与准确选择来源，并仅更新 decisions 的当前方向投影；同步完成后才用新方向查重或作派工背景。原候选、原话、判断与预测保持原样，方向调整如何影响读者承诺另行说明。

genre / premise / voice / payoff 的选择理由回指立项记录中的同一读者承诺和审美取舍；新增证据导致调整时说明依据并核对作者权限。长期兑现沿引擎已有约定、章纲、伏笔/线路与实际 Worker 报告检查，不另建承诺结算账本；开篇机械通过不能推成全书优秀。

## 出口

设计 `task_ready` → 本节；`outline_ready` 且已有明确正文授权 → `flows/writing.md` E 保存同一授权；没有正文授权则交付开书成果并停在授权入口。
