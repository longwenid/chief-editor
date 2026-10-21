# 总编操作手册（chief-editor · references/playbook.md）

本手册是总编身份的照抄级操作序列：市场扫描 → 对标拆解 → 立项拍板 → 开书十三门 → 正文授权 → 无人值守连写 → 交付复盘。每步给出可照抄的命令、授权档位与要写的记忆条目。

权限模型、引擎操作面与原创红线全文见本技能 `SKILL.md`、`references/engine-contract.md`、`references/originality.md`；引擎行为一律以 novel-ledger 技能文档为准（`C:/Users/longwen/.zcode/skills/novel-ledger/references/runtime.md` 与 `opening.md`）。本手册只引用不复制引擎文档；引擎文档升级时以引擎为准。

## 0. 通用约定（每条序列开始前过一遍）

1. **替换符**：`<novel-ledger>` = `C:/Users/longwen/.zcode/skills/novel-ledger`；`<P>` = 项目目录绝对路径；`<owner>` = run 返回的 owner；`<task>` = 任务 ID；`<会话ID>` = 宿主 Worker 会话 ID。多项目并行时每个项目各自代入 `<P>`（<P1>/<P2>…），owner 各项目各持一份、绝不跨项目混用。
2. **Windows**：一律用 `python`（不是 python3），Git Bash 执行。
3. **UTF-8**：会话开始先 `export PYTHONUTF8=1`——中文 JSON 与长文本经引擎物化文件读写时必设；不在控制台直接打印长 JSON（GBK 控制台会乱码），读盘里的文件。
4. **长内容走文件**：board.md / question.json / catalog.md / brief.md / result.template.json / result.json / dispatch.md / proposal.plan_path 都是引擎物化到磁盘的文件——读盘、改盘、`--file` 提交；绝不在命令行内联长中文。
5. **三档预授权速查**（全文见 SKILL.md）：
   - **T0 作者专属**（默认必须上报；常设或逐次原话授权时总编代选）：choose / choose --tier / regroup / back / approve / answer / recontract / revise --proposal-hash / replan / lexical / 首次 run --source。无代选授权时引擎物化的 board.md / question.json / proposal.plan_path **原样转呈**用户，不自拟摘要替换引擎文案、不替用户圈重点、不代答；拿到用户真实答复（或代选授权）后以其原话作 `--source` 执行——代选时逐字记授权原话＋当次代选对象与理由（纪律见 SKILL.md 三档预授权与 authorization.md 头部处置条）。预选、超时、沉默都不代表选择。
   - **T1 预授权治理**（目标内自主，不重复询问）：run 保存授权目标后，advance / watch / claim / renew / pause / resume / 派工 / export / html / complete / deliver / promote（修订属当前授权目标时）在该目标内直接执行。
   - **T2 上报即停**：完整性失败（projection / chain / state_integrity / source_integrity / schema）、repair_exhausted / repair-stalled、remedy_exhausted——保留现场报告用户；不改 schema、不修改或复制临时引擎取消判据、不直接写库。
6. **留痕**：每条带 --source / --reason / --owner 的治理命令执行后，向 `memory/authorization.md` 追加一行（格式见 memory/templates.md §4；只追加不改写）。
7. **顺序红线**：author_decision 先 answer 再 advance / recontract——答复会冻结此前派工（stale_task，application.py:647），先派工后答复等于白派一个 Worker。
8. **完成判定**：Worker 报告完成必须核对返回里的 committed_chapter；accepted=true 只表示回执已受理，可能仍产生返修候选。

## S. 唤醒·接管（每次会话开始；多项目并行）

```bash
export PYTHONUTF8=1
# ① 恢复授权脉络（只读不写）：
#    memory/decisions/ 全部 status=active 条目 → 逐条取 项目绝对路径、方向指纹、停点
#      → 汇成 active 项目清单（可标注当前聚焦顺序；既有条目无方向指纹字段时
#        从其 chosen 与门选择提炼，例：力量计税=仙侠修真×计税制度，不回溯改写原条目）
#    memory/authorization.md 尾部 → 按 P= 列分项目恢复各自 owner、预授权档位、策略原话
#      （owner 绝不跨项目混用）
# ② 逐项目（有几个 active 项目就逐个过，命令本就带 --project），
#    一切以引擎当前返回为准（不手改库、不凭记忆续跑）：
python <novel-ledger>/scripts/novel.py --project <P1> status --tasks
python <novel-ledger>/scripts/novel.py --project <P1> advance --compact
python <novel-ledger>/scripts/novel.py --project <P2> status --tasks
python <novel-ledger>/scripts/novel.py --project <P2> advance --compact
```

按各项目 advance 返回的 action 进入对应序列（处置表见 F4 与序列 G）：task_ready / await_choice / await_author / author_decision / paused / revision_blocked / revision_ready / ready_to_complete / target_reached。逐项目独立处置、互不越位：报告与派工一律先报项目名；唤醒只跑 status（状态摘要），项目目录内容只在对应项目的流程步骤里读（读取隔离纪律见 SKILL.md）。

**记忆**：读 authorization.md 与 decisions/*；本步无写入。

## A. 市场扫描（用户要求时，或距最新 market/ 快照超过一个月）

- **A1 付费盘月票榜**（第一手，免登录）：WebFetch `https://m.qidian.com/rank/yuepiao/` → 记 Top20 书名/作者/分类/月票数（当月口径）。
- **A2 付费盘畅销榜并置**：WebFetch `https://m.qidian.com/rank/hotsales/` → Top20 含字数。**双榜同在的书 = 当期最强方向**；字数 = 体量代理。
- **A3 详情页补数**：从榜单页**抄** `/book/<书ID>/` 链接（书ID自造必 404）→ WebFetch 详情页取简介/标签/书友数（体量第二代理）。
- **A4 分类榜与历史月**（需要时）：起点桌面版对内置 WebFetch 返回空 → 用渲染式 webReader 抓 `https://www.qidian.com/rank/yuepiao/chn<NN>`（玄幻 21 / 仙侠 22 / 都市 4 …）；侧栏各分类在库总数 = 拥挤度分母；该页默认展示上一完整月归档。**数字仍回移动版取**（桌面版月票是字形混淆字体）。
- **A5 免费盘口径确认**：WebFetch `https://fanqienovel.com/rank` → 默认分类榜 + 榜单规则（阅读榜 = 30 万字以上已签约；新书榜 = 30 万字以下未断更；每日 15 点更新；仅排 1000 在读以上）。
- **A6 免费盘分类采样**（至少四类）：WebFetch `https://fanqienovel.com/rank/1_2_1014`（都市高武）、`/rank/1_2_261`（都市日常）、`/rank/1_2_257`（玄幻脑洞）、`/rank/1_2_539`（悬疑脑洞）；新书层把第二段换成 1：`https://fanqienovel.com/rank/1_1_262`（都市脑洞新书榜）。记在读数 + 简介脑洞标签；19 个男频分类 ID 枚举见最新快照 sources；女频 ID 未枚举，需要时从 /rank 导航页取链接。
- **A7 番茄详情页补数**：从榜单页**抄** `/page/<书ID>` → 简介全文/字数/标签/章节进度；修复榜单页乱码书名。**在读人数只在榜单页**，两页配合。
- **A8 交叉核对**：中国作协蓝皮书定趋势口径、中新网文定巅峰榜机制（URL 见最新快照 sources）；WebSearch 当月「平台+榜单名+年月」找第三方盘点帖。**双源一致才写进结论**；自媒体单源只作线索（D 级）。
- **A9 写快照**：按 memory/templates.md §1 骨架写 `memory/market/YYYY-MM.md`（一月一档，不改旧档）。

**降级速查**（全文见最新快照 pitfalls_hit[]）：桌面版返回空 → 渲染式 webReader 或全走 m.qidian.com；数字乱码 → 一律移动版明文；移动版无分类榜 → 桌面版 webReader；起点阅读指数榜 = 2023 陈旧快照，弃用；番茄巅峰榜无网页入口 → 第三方帖 + 机制报道交叉；知乎/百度百科 403、今日头条 JS 渲染取空 → 回避。

**记忆**：写 memory/market/YYYY-MM.md（双榜原始数据、sources+等级+降级路径、高置信方向、体量基准尺、坑命中）。

## B. 对标拆解（序列 C 前置；用户点名"对标 X"时 X 必拆）

- **B1** 从快照取 2~4 本高置信头部书，每书一份 `memory/teardowns/<书名>.md`。**只拆四轴**：

| 轴 | 拆什么 | 喂给哪个门 |
|---|---|---|
| 题材与读者承诺 | 分类、标签、读者预期 | genre 门方向输入 |
| 脑洞形状 | 一条根规则 + 谁与谁博弈 + 兑现节奏 | premise / world 门 |
| 节奏与体量 | 章幅、卷结构、月票/在读/字数/书友数 | scale 门档位参考 |
| 兑现方式 | 高潮怎么结、伏笔怎么还 | payoff 门参考 |

- **B2** 三条红线逐条自查（全文见 references/originality.md）：专有名词不搬 / 桥段不搬 / 设定组合不整搬。
- **B3** SETTING_CLICHES 词表自查：序列/途径/克苏鲁/克系/系统/幕后黑手/第四天灾/诸天/无限流/模拟器/签到/存档重开（novel-ledger scripts/novel_ledger/contracts.py:121-122）。命中即标注进 engine_cliche_hits——不因此毙掉候选；引擎板面告警原样转呈用户，用户坚持以作者为准，但立项必须附差异增量声明。
- **B4** 抽象重述：拆解结论以抽象结构语言重述进 abstractions 字段——这是唯一允许进入引擎门输入的部分；对标书的措辞与人名地名体系名不进任何门输入。

**记忆**：写 memory/teardowns/<书名>.md（含来源 URL 与抓取日期）。

## C. 立项提案（三通道：A 用户想法 / B 总编自决 / C 多案拍板）

- **C0 判通道**（开新书第一步；判定结果写进 decisions 的 selection_mode）：
  - 用户本次给了想法 → **通道A**；
  - 无想法但 authorization.md 头部有代选常设授权（以头部实时内容为准，授权可随时撤销）→ 默认**通道B**，不再询问；
  - 无想法也无常设授权 → **一次性**问用户：给想法即 A、让总编定即 B、要多案即 C；问一次即定，同一本书不重复追问。
- **C1 方向查重（三通道共同；候选生成前与落定前各过一遍）**：方向 = **类目＋核心脑洞**（例：力量计税 = 仙侠修真×计税制度、神明维修工 = 都市异能×神话残骸维修）。对照 `memory/decisions/` 全部 status=active 条目的方向指纹——**类目与核心脑洞双同 = 撞向，必须换方向**；仅同其一不算撞向（差异增量声明里说清增量即可）。既有条目没有方向指纹字段时从其 chosen 与门选择提炼，不回溯改写原条目。按通道处置：
  - **通道B**：绕开全部已占方向后形成唯一主见——主见的类目或核心脑洞至少其一不与任何 active 项目相同；
  - **通道C**：候选生成时直接排除撞向候选（"同结构异实现"不豁免类目＋脑洞双同）；
  - **通道A**：用户想法撞向时总编点破（指明与哪个项目撞、撞在哪一维）并给换向建议；用户仍坚持则按作者决定权留痕放行——decisions 注明撞向对象与用户坚持原话。
  - 查重对照面只有方向指纹与状态摘要（项目名/指纹/停点），不读其他项目的正文与设定（读取隔离纪律见 SKILL.md）。
- **C-A 用户想法**（用户核心概念优先，打磨不越权）：总编以品位对想法做诚实压力测试，逐项过——①差异化：与快照/拆解里同方向在位书相比增量是什么（无增量就明说）；②市场对位：快照 crossover 与 volume_benchmarks 里有没有它的读者盘与体量档；③原创红线：序列 B 三条红线逐条自查；④方向查重（C1）：撞向按 C1 通道A 处置。结论如实呈用户——可行说可行，有硬伤点破并给替代形状；改核心概念（题材、根规则、主角处境）必须用户点头，总编只打磨表达与结构。快照超过一个月先跑序列 A。
- **C-B 总编自决**（唯一主见，不骑墙）：从最新 market 快照与 teardowns 形成**一个**主推方向（不搞 2~3 案并列上交），主见须已过 C1 查重（绕开全部已占方向）；主见必须自答三问——为什么是它（市场证据引用）、它加什么新根规则（差异增量声明）、凭什么跑完（体量档与兑现路径）。理由写进 decisions；随后的十三门等 T0 入口按代选纪律执行（--source 逐字记委托原话——常设或逐次——＋当次代选对象与理由，台账照记，作者可 back/regroup/feedback 纠偏）。
- **C-C 多案拍板**（现行流程保留）：由快照+拆解生成 2~3 个**同结构异实现**候选，生成时按 C1 排除与 active 项目撞向的候选；每案必附差异增量声明：「对标组合已被市场拥有，本书在其上加什么新根规则」——无增量的候选不提出；每案附体量档位建议（引用快照 volume_benchmarks；市场数据只作选题信号与档位参考，不写成正文目标、不得说成质量结论）；连同快照结论呈用户拍板（不拍板不立项）。
- **C4 落定收尾（三通道共同）**：拍板/自决落定后在工作区选定**独立项目目录**（不覆盖已有项目）；选完设定 ≠ 正文授权。
- **C5 写 decisions 记忆**：含 selection_mode、direction_fingerprint（方向指纹）与 author_quote 对应口径；通道A 撞向放行时另注明撞向对象与用户坚持原话。

**记忆**：写 memory/decisions/YYYY-MM-DD-<slug>.md（selection_mode/方向指纹/全部候选或唯一主见/选定/author_quote 按口径/项目绝对路径/对标来源链接/status=active）。

## D. 开书十三门（唯一开书协议）

门序（引擎固定，不可换）：genre→premise→voice→scale→world→ladder→origin→edge→protagonist→relationships→opposition→payoff→title（novel-ledger scripts/novel_ledger/creation.py:12-19）。

**D0 建项目**（零输入逐门，不要求 --source）：

```bash
python <novel-ledger>/scripts/novel.py --project <P> init
```

已有约定的项目不得再次 init。

**D0b 分支——作者已定部分门值**（init 后、尚未展示方案且无 pending）：把作者原话整理成 要求.json（**键必须是门 ID**，字段名当键被拒并返回 valid_gates；只存作者已定的值，不替缺口补造决定）：

```bash
python <novel-ledger>/scripts/novel.py --project <P> intake --file 要求.json --source '作者原话'
```

**D0c 分支——作者给完整约定且未派过门任务**（派过门任务后此命令被拒，改用 recontract，T0）：

```bash
python <novel-ledger>/scripts/novel.py --project <P> opening --file 约定.json --source '作者原话'
```

**D1 逐门自执四步**（每门重复；opening_options 阶段主控可自执 read/recall——contracts.py:177 的 CONTROLLER_STAGES；正文与冻结审读阶段主控不可读）：

```bash
# ① 取任务与 task_path
python <novel-ledger>/scripts/novel.py --project <P> advance --compact
# ② 读 task_path 下的 brief.md（读盘；input.json 是同一内容的 JSON 原文，不必解析）
# ③ 读必读记录（开书阶段对主控放行）
python <novel-ledger>/scripts/novel.py --project <P> read --task <task>
# ④ 从 task_path/result.template.json 复制起稿 result.json（只填 data，信封三字段不手写），
#    试算通过后提交；session 填主干自己的会话身份（门任务不绑定会话）
python <novel-ledger>/scripts/novel.py --project <P> check --file <task_path>/result.json
python <novel-ledger>/scripts/novel.py --project <P> submit --file <task_path>/result.json
```

checked ≠ 已提交；submit 返回 accepted 才算落账。

**D2 await_choice 处置**（全部 T0）：

1. 先把引擎物化的 work/board.md 内容**原样**贴给用户（或给文件链接），再按 work/question.json 的选项**原样**发起提问——不自拟摘要、不替换引擎文案、不把字段/哈希/命令展示给用户（opening.md:28）。
2. 第一门（genre）作者未给方向时：把任务目录 catalog.md 十二类目**原文**贴进对话（铺目录是正文文本步骤，不是提问选项；opening.md:45）。
3. 用户答复后执行其一（常设/逐次代选授权在场时按 §0.5 T0 速查的代选纪律代行并照记台账）：

```bash
# 普通门选择（方案 id 用展示组里的真实 id，不一定是 A/B/C）
python <novel-ledger>/scripts/novel.py --project <P> choose --option <方案ID> --board <展示哈希> --source '用户原话'
# 结构门（scale）档位直达
python <novel-ledger>/scripts/novel.py --project <P> choose --tier t<N> --source '用户原话'
# 用户否决当前组（新组须与被拒组实质不同，并吸收用户随换组补充的偏好）
python <novel-ledger>/scripts/novel.py --project <P> regroup --board <展示哈希> --reason '换一组'
# 用户要改已选门（保留前门；后续依赖门的选择归档后重选）
python <novel-ledger>/scripts/novel.py --project <P> back --gate <门ID> --reason '原因'
```

旧组编号不能套新门——传错 id 被拒并返回 valid_options，按 valid_options 重新问用户。预选、超时、沉默都不代表选择（opening.md:30）。

4. 每次 choose / regroup / back 后向 authorization.md 追加一行（用户原话；代选时授权原话＋当次代选理由）。

**D3** 十三门全部完成、进入 world_model 阶段后：按引擎返回的任务派工（派工纪律见 F2），进入序列 F。

**记忆**：门选择与原话由引擎入库；总编只在 authorization.md 追加用户 choose/regroup/back 原话与每次上报停点。

## E. 正文授权（T0）

- **E1** outline_ready 交付实际卷纲覆盖后，向用户取正文授权原话：写到第几章（--through N）还是完本（--complete）、标准还是快速模式。
- **E2** 执行（原话逐字入 book.decisions，application.py:448；目标不得低于已冻结任务与修订范围，application.py:439-442）：

```bash
python <novel-ledger>/scripts/novel.py --project <P> run --through <N> --source '作者授权原话（逐字）'
python <novel-ledger>/scripts/novel.py --project <P> run --complete --source '作者授权原话（逐字）'
python <novel-ledger>/scripts/novel.py --project <P> run --through <N> --fast --source '作者授权原话（逐字）'   # 五章一组快速连写
```

- **E3** 保存返回的 owner；此后每条治理命令带 `--owner <owner>`。租约默认 300 秒，watch 在引擎进程内每 30 秒自动续租（unattended.py:14-16）。租约过期 → 重新 run 认领，**沿用已授权目标不扩大**。

**记忆**：authorization.md 追加 run 条目（完整 argv / 原话 / owner / 目标章号 / writing_mode）。

## F. 无人值守连写循环（T1，授权目标内）

每轮只做一件事：认领 → 派工 → 等待 → 按返回动作分支。多项目并行时逐项目各跑本循环：每条命令与上报先报项目名，owner 不跨项目混用；处理任一项目的任何一步不读其他项目的项目目录内容，派工背景一句只取自本项目的方向指纹与状态摘要（读取隔离纪律见 SKILL.md）。

**F1 主干认领**（初始认领必须主干进程执行，Worker 自己 claim 会被 worker_boundary 拒绝，novel.py:211-217）：

```bash
python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> claim --task <task> --session <会话ID>
```

返回 token 转给 Worker，填入其回执顶层 execution_claim（裸字符串）。claim=null 表示无需认领。

**F2 派工**：转发 **dispatch.md + 角色 + task_path + 一句背景** 给 Worker。不手写环境自举、不代 Worker 读库。快速组内 Worker 用 worker-next 接续（该命令 Worker-only，总编绝不代行；派工卡可提示 Worker 使用）。

**F3 等待**（零主干推理，自动续租）：

```bash
python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> watch
```

**F4 返回动作处置**（七类）：

1. **task_ready**（T1）——按 task 派下一工（回 F1/F2），再跑一次 watch。
2. **wait_for_batch**（T1）——继续 watch 等整组结束，不另派。
3. **await_author**（**T0**）——向用户呈**准确版本**首章；用户认可后：

   ```bash
   python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> approve --prose-hash <HASH> --source '作者认可原话'
   ```

   prose_hash 与当前首章不符会报 pilot_version——先取准确版本再认可。认可同时固定文风锚点。
4. **author_decision**（**T0**）——把问题+选项**原样**上报用户；答复后先 answer 再派工：

   ```bash
   python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> answer --decision-id <当前ID> --option '选定label' --source '作者答复原话'
   python <novel-ledger>/scripts/novel.py --project <P> advance --compact
   ```

   答复必须核对 decision-id 与当前待决一致、选项必须是已展示 label 之一。选项外的第三条路 = 新决定：先向用户转述 recontract 全书重写代价（answer 的 recover 文案已含，application.py:634-636）再执行 recontract。
5. **paused / idle**（T1 诊断）——Worker 空转：`advance --compact` 重派同一 pending（未提交不计返修额度）；**连续两次空转 → 保留现场上报**。快速组停摆：先确认原执行者已停止，再：

   ```bash
   python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> pause --cancel
   # 然后 resume / advance 重开（已提交章节与额度保留）
   python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> resume
   ```

   resume 撞 revision_bounds / repair_budget / author_decision / remedy_exhausted 被拒（application.py:595-600）→ 自动降级 T2 处置。
6. **revision_blocked**（**T0**）——把 proposal.plan_path **完整方案**呈用户；等用户对该 plan_hash 的明确授权：

   ```bash
   python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> revise --from-chapter <N> --proposal-hash <HASH> --source '授权原话'
   ```

   不得用 recontract、重新 run、resume 绕过。
7. **revision_ready**（T1）——修订属当前授权目标 → `promote`；不属于、或作者要先看候选再决定 → 交作者决定（promote / discard）。

**F5 回执与返修**：Worker 报"完成"必核对 committed_chapter（accepted=true 只表示受理）。用户对当前候选正文的反馈：

```bash
python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> feedback --text '作者原话'
```

已验收正文的历史修改走"附：修订与改约"的 revise。

**F6 常用辅助**：

```bash
python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> renew --seconds 300    # 手动续租
python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> pause --reason '原因'  # 暂停（保留任务与候选）
python <novel-ledger>/scripts/novel.py --project <P> status --tasks                        # 全部任务生命周期
python <novel-ledger>/scripts/novel.py --project <P> usage                                 # read/recall 字符量
python <novel-ledger>/scripts/novel.py --project <P> compact                               # 回收不可达文档空间
python <novel-ledger>/scripts/novel.py --project <P> audit                                 # 只读验收检查（不豁免 complete/deliver 复验）
```

**记忆**：每条治理命令追加 authorization.md 一行；异常停点当场写 postmortems 草稿（code+处置）。

## G. 交付与复盘

- **G1** advance 返回 ready_to_complete：

  ```bash
  python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> complete
  ```

  重复调用也复验准确快照——旧 audit.ok 与 completed 状态均不豁免；首章认可是验收项（须已 approve）。
- **G2** 交付：

  ```bash
  python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> deliver
  ```

  产出 book.md / book.html / delivery.json；交付失败**只重试该快照的 deliver**，不重新写书。
- **G3** target_reached（授权目标到点未完本）：`--owner <owner> html` 刷新全书视图；按**实际完成章节范围**交付；不冒充全书完本。
- **G4** 复盘（交付后 / T2 停点后 / 用户纠偏后）写 `memory/postmortems/YYYY-MM-DD-<slug>.md`：引擎拒绝事件（code+一句话处置）、市场假设 vs 实际表现、playbook 修正建议。涉及命令序列修正 → 提给 support 主笔更新本手册，总编不自行改主文档。
- **G5** 把 decisions 对应条目 status 回写为 delivered / shelved（唯一允许回写的既有记忆）。

**记忆**：写 memory/postmortems/YYYY-MM-DD-<slug>.md；回写 decisions 条目 status。

## 附. 作者发起的方向性操作（全 T0，用户明示才执行）

```bash
# 历史修订：先只读影响分析，再带范围四选一（无范围会被拒并提示先跑 impact）
python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> revision-impact --from-chapter <N> [--changes-file 变更.json]
python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> revise --from-chapter <N> --reason '原因' (--changes-file 变更.json | --through <M> | --to-end | --proposal-hash <HASH> --source '授权原话')

# 方向性改约：已有正文 = 新分支自第 1 章重写全书、父分支保留可 discard，代价随已写章数线性增长——
# 必须先向作者说明该代价再执行；不能用改约绕过修复额度或作者边界、不能替代可 answer 的裁决
python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> recontract --file 完整候选.json --source '作者原话' [--patch]

# 未写窗口章纲重排（作者明确要求；已有草稿/正式稿的章纲不能直接删）
python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> replan --from-chapter <N> --reason '原因'

# 字面规则（如 forbidden_name_chars 硬禁人名用字；修改会取消在途任务）
python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> lexical --file 规则.json --source '作者原话'

# 预览导出（另存须显式 --output；导出不代替完本验收）
python <novel-ledger>/scripts/novel.py --project <P> --owner <owner> export [--format md|html] [--output 文件]
```
