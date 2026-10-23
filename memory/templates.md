# 记忆模板与填写规则（chief-editor/memory/）

写任何一条记忆前先对本文件。五类记录的字段模板、文件命名与追加纪律如下。**字段缺失时按相应 schema 写未知和原因，不得凭记忆编造补齐**；所有数字、引语、URL 只用当次实测材料（榜单快照 / 引擎返回 / 用户原话），来源 URL 或可核验位置、观察或执行日期必填。
## 0. 写之前先定位记忆根

本文件是**模板**，不是数据。实例写在 `$CHIEF_EDITOR_MEMORY`（解析顺序见 `references/environment.md` §5），技能目录只保留本文件与空目录 `.gitkeep`。

- 下文所有 `memory/xxx` 写法都指 `$CHIEF_EDITOR_MEMORY/xxx`；
- 首次运行记忆根不存在时按本文件的骨架建档；
- 记忆根是多项目共用的总编级资产，项目目录（正文/卷纲/设定）各自独立，两者不混。


## 通用纪律

1. **authorization.md 只追加不改写**：历史条目与头部已收取的策略原话永不修改；策略变更 = 在头部区块追加新条目并注明日期。
2. **旧市场快照不改写**：每次扫描新建 `market/YYYY-MM-DD-HHMMSSffffff-<id>.md`；同月可有多份，比较增量写进新快照。文件名使用 UTC 保存时刻和唯一 id，不代表市场观察时点。新 JSON 用 `observations[].at`，具体结论用对应 evidence_ids 的时点判时效；旧版 `market/YYYY-MM.md` 仍只读其 scan_date。缺观察时间则未验证，不回写或迁写。
3. **teardowns/<书名>.md 每书一份**；重拆同一书 = 新文件加日期后缀（`<书名>-YYYYMMDD.md`），不覆盖旧档。
4. **decisions 文件名**：`YYYY-MM-DD-<slug>.md`；slug 用短横线连写的小写词（拼音或英文），已存在时另取唯一 slug，不覆盖。**postmortems 文件名**：`YYYY-MM-DD-<slug>-<id>.md`，同日同项目不同事件各建新记录。
5. **既有记忆仅允许回写两项控制元数据**：decisions 的 `status`（仅全书完本交付后 active → delivered，或作者明确搁置后 active → shelved）及下文规定的当前 `direction_fingerprint`。部分章节交付和 T2 停点保持 active；原立项 candidates/chosen、依据、作者原话、预测及阈值不回写。范围、停点与方向变更来源追加留痕，其他记录落盘后不改。
6. 每份新证据块写明 `record_type`、`record_id`、`created_at` 与 sources（URL/可核验位置及观察时间）；实际执行身份沿授权台账和宿主任务返回留痕，不凭生成标签证明身份或原话真实。旧格式的 sources 仍按原位置读取。

## 编辑证据块（新记录）

市场、审美对照、立项与复盘的新记录各使用一个 `json` fenced 证据块，分别采用 `market_snapshot` / `taste_comparison` / `selection_decision` / `postmortem`；完整字段与有效范例见 `references/editorial-judgment.md`。该块是编辑证据真源，下面的表格与自然语言只作它的阅读投影或 record_id 引用，不另填一套相冲突的数字、偏好、预测或结论。小说事实始终留在引擎中。

记录先在工作目录起草，再运行 `python3 "<chief-editor>/scripts/check_editorial_evidence.py" 候选.md`（也接受单个 JSON 记录）；检查通过后新建记忆，历史内容不可变，仅上述控制元数据按真实结果更新。脚本只检查结构、引用和可比性，不证明来源真实或审美正确。无记录输入不算验收通过。旧版不补造证据；缺新字段时标 legacy/未验证，不能宣称历史记录已通过新检查。

新记录可用 `python3 "<chief-editor>/scripts/save_editorial_record.py" --memory-root "$CHIEF_EDITOR_MEMORY" --file 候选.json` 安全保存；有跨记录引用时，逐个追加 `--evidence 已有记录.md`。它再次校验全部显式材料后以排他创建写入单一 Markdown/JSON 记录；拒绝重复 record_id、覆盖和路径逃逸，不会编辑授权台账或旧状态。文件名由 UTC 保存时刻和 record_id 生成：market 为日期时间含微秒，decisions/postmortems 为日期加 ID，teardowns 为 ID。只在当前 Mac 验证了安全写入后端；不支持相应系统能力时明确停止，不降级绕过。

新 decisions 的项目路径、状态、模式、当前方向指纹与授权定位仅存证据块的 `control`；chosen 关联同块 candidates，表示原立项选择。落定记录才可 active，提案是 draft。阶段交付保留 `control.status=active`，完本或明确搁置时只改该字段。下面各类的 Markdown 骨架用于兼容阅读与投影，新记录不要逐字段再手填一份。

**当前方向同步**：原立项预测保持历史语义，`control.direction_fingerprint` 是供恢复、查重和派工使用的当前方向投影。受托或作者决定回退后，只有 genre/premise 两门的实际选择均已重新落定，才从真实门值提炼新指纹；提案、back 成功或重选未完成都不能提前当成新方向。先向授权台账追加 `request_kind=direction_update`、P、decision_record_id、旧/新指纹、genre/premise 的准确选择定位及授权定位，再仅更新该 control 字段并校验记录；不重写原候选、理由、原话或预测。旧格式只更新同一条目的原方向指纹字段，不加第二个投影。新记录保存器不负责此更新。

恢复、查重及派工前按项目核对最后一条已完成的 direction_update 与 control 是否一致；追加后中断而未更新时，凭其准确选择定位核实后补齐投影。跨项目只处理该变更的指纹与来源定位摘要，不读取他项目正文或设定；来源无法核实时标“方向待同步”并报告具体缺口，不能把陈旧指纹当作确定的当前方向。重选未完成期间保留旧指纹但标明待重选状态，不当作新方向已落定。

独立审美评审仅获得去名气后的 A/B 材料与范围；sources 的身份映射保留在总编记录中，不在匿名评审前透露。每份比较卡只存一处，其他拆解条目以 record_id 引用。作者授权原话仍在授权台账；审美偏好的 quote 只记录实际表达的偏好，两者不可互相推定。

## 源等级标尺（写 sources[].grade 用）

- **A**：平台官方榜单/详情页、权威机构报告（当次实测可读）——可直接支撑结论。
- **B**：机构媒体报道——做机制与趋势背书，不做数据主源。
- **D**：自媒体/社区单源——只作交叉线索，不得单独支撑结论。

锚点（2026-10 首次快照实测标注）：中国作协蓝皮书 = A、中新网巅峰榜机制报道 = B、smzdm 社区帖 = D。

---

## 1. 市场快照 `market/YYYY-MM-DD-HHMMSSffffff-<id>.md`

- **何时写**：每次扫描完成后新建一份，含同月复扫；不改旧档。
- **何时读**：立项提案前（序列 C）、拆解选书时（序列 B）、下次扫描对比增量时。
- **骨架（照抄后填）**：

```markdown
# 市场快照 YYYY-MM-DD-HHMMSS-<id>

- snapshot_month: YYYY-MM
- snapshot_id: YYYY-MM-DD-HHMMSS-<id>
- scan_date: YYYY-MM-DDTHH:MM:SSZ
- 说明: 本档落盘后不改写；后续扫描另建快照并引用本档比较。

## sources（本次实际使用的源；grade 用 A/B/D 标尺）
| # | name | url | grade | 降级路径（该源失效时改用谁） |
|---|------|-----|-------|------------------------------|

## paid_rank（付费盘；数字以 m.qidian.com 明文为准）
| 书名 | 作者 | 分类 | 月票 | 字数 | 书友数 | book_id | url |
|------|------|------|------|------|--------|---------|-----|

榜面构成与观察（每条注来源）：
1. …

## free_rank（免费盘；在读人数只在榜单页）
| 书名 | 作者 | 分类 | 在读 | tags | book_id | url |
|------|------|------|------|------|---------|-----|

观察（每条注来源）：
1. …

## new_book_layer（新书层采样；30 万字以下未断更层）
- 采样榜：
- 观察：

## crossover（由证据块生成的方向观察与适用范围）
1. **<方向>** — 支撑：<观察ID>；事实/推断/假设：<分类>；范围与限制：<可比队列、时点、独立来源、未验证项>

## volume_benchmarks（体量基准尺）
- 付费盘：
- 免费盘：
- 拥挤度分母（分类在库数）：

## pitfalls_hit（本次命中/复验的坑 → 降级动作）
1. <坑> → <降级动作>
```

- **填写规则**：paid_rank/free_rank 从 JSON 证据块投影当次明文数字，样本没给的格填"未记录"；书 ID 只从榜单链接抄。数字注明单位、分母/窗口、阶段与曝光限制；单源可作观察或假设，不能升格为市场趋势；同源转载不算独立证据。头部、上升、普通、掉队样本缺哪类就说明，不隐去选择偏差。

## 2. 对标拆解 `teardowns/<对标书名或书ID>.md`

- **何时写**：每完成一本对标拆解。
- **何时读**：立项提案时（生成候选）、开书门自执 premise/world 门时（方向输入与红线自查）。
- **骨架（照抄后填）**：

```markdown
# 对标拆解：<书名>

## book
- title / author / platform / url / 抓取日期：

## structure（可迁移结构限定四轴；审美比较另用唯一 JSON 证据块）
- genre_promise（题材与读者承诺 → genre 门方向输入）：
- gimmick_shape（核心处境与冲突：人物/关系/规则怎样制造持续压力，如何兑现 → premise/world 等合法门输入）：
- rhythm_volume（章幅/卷结构/字数/在读或月票 → scale 门档位参考）：
- payoff_shape（兑现方式 → payoff 门参考）：

## engine_cliche_hits（SETTING_CLICHES 词表：序列/途径/克苏鲁/克系/系统/幕后黑手/第四天灾/诸天/无限流/模拟器/签到/存档重开）
- 命中：
- 未命中：

## abstractions（抽象重述后的门方向输入——唯一可进引擎门输入的部分；不含对标专有名词）
- 

## red_line_check（三条红线逐条打勾）
- [ ] 红线一 专有名词不搬：对标书的人名/地名/组织名/功法序列称号体系名未进入任何候选与门方向输入
- [ ] 红线二 桥段不搬：具体情节序列/名场面/台词未搬，仅"该结构在本书世界的等价压力测试"层面的形状借鉴
- [ ] 红线三 设定组合不整搬：同一组设定标签未整体移植

## reuse_verdict（结构可借鉴性结论一句话）
- 
```

- **填写规则**：结构四轴不冒充审美结论；细读用 taste_comparison 记录文本位置、机制、体验、代价、边界和反例，允许非模板方案胜出或证据不足。abstractions 必须用抽象结构语言，对标措辞不进任何门输入；red_line_check 三条全打勾才可进立项候选；cliché 命中只告警不毙稿，候选仍附差异增量。具体场面只作有范围的阅读证据，不移入新书。

## 3. 选题决策 `decisions/YYYY-MM-DD-<slug>.md`

- **何时写**：立项落定后（三通道任一：A 用户想法——压力测试结论呈用户、落定后 / B 总编自决 / C 用户拍板）；交付或搁置时回写 status，真实方向重选完成后按上文仅同步方向投影。
- **何时读**：每次唤醒（定位全部 active 项目与授权脉络）、新立项方向查重时（`references/flows/selection.md` C1）、复盘时。
- **骨架（照抄后填）**：

```markdown
# 选题决策：<slug>

- date: YYYY-MM-DD
- slug: 
- selection_mode: A-用户想法 / B-总编自决 / C-多案拍板   # 判定见 references/flows/selection.md C0
- decision_kind: author / delegated   # 作者亲身决定 / 按委托原话代选（见 references/policy.md §3）
- direction_fingerprint: <类目>×<核心脑洞>   # 方向指纹（多项目立项查重用，见 flows/selection.md C1）：类目与核心脑洞双同=撞向必换
- status: active          # 部分交付或停点保持 active；仅完本交付后 delivered，作者明确搁置后 shelved
- project_path: <项目绝对路径>
- authorization_index: <对应 authorization.md 条目日期>
- links: 快照=memory/market/<实际快照文件名>.md；拆解=memory/teardowns/<书名>.md

## candidates（全部候选，含落选）
1. **<方向一句话>**
   - 结构来源：memory/teardowns/<书名>.md（+ 快照条目引用）
   - 差异增量声明：<本书可辨识的创作增量>如何改变具体阅读体验，靠什么持续展开，付出什么代价……
   - 建议档位：<引用 volume_benchmarks 依据>

## chosen
- 选定：<候选编号/名称>

## author_quote（口径随 selection_mode，均逐字不改写：A=用户想法原话；B=委托原话（常设或逐次）＋当次代选理由；C=用户拍板原话）
> 
```

- **填写规则**：selection_mode 与 direction_fingerprint 必填；撞向放行记录对象与用户坚持原话。candidates 保存全部实际考虑的方向与差异增量：通道B对外唯一主推，对内另留最接近的舍弃方向与取舍。增量可以来自人物困境、关系结构、视角声音、生活经验或世界规则，不强制新增根规则，也不要求凑齐维度。selection_decision 证据块分别呈现商业适配、作品价值、作者已表达偏好，预登记可反证预测及复核条件，不合成总分。author_quote 逐字保留，代选理由另起一行；没有审美偏好原话时偏好写 unknown，不能从委托原话推定。

## 4. 授权台账 `memory/authorization.md`（只追加不改写）

- **何时写**：每次执行带 --source / --reason / --owner 的治理命令时追加一行。
- **何时读**：每次唤醒（恢复 owner 与已授权范围）、上报前（核对原话）、复盘时。
- **头部**：用户委托策略原话——本次消息已给委托就直接记录，无需再收取一次；未声明时注明真实缺口，不从历史摘要补造授权。
- **条目字段**：date、project（`P=`）、tier（T0/T1/T2）、decision_kind（author / delegated）、command（完整 argv）、source_quote（用户原话，无则留空）、outcome（owner / decision-id / plan_hash / committed_chapter 等返回值）。门决定另记 gate、choice_origin（author_locked / editor_selected）及对应原话定位；从引擎已选记录与本台账恢复来源，不把所有已选项都算用户锁定。
- **自定义请求**：另附 request_kind=custom_opening、gate、action（back / regroup）、board_hash、完整 reason。换组记 custom_regroup_number；回退记 back_gate、变更项的 decision_ref 和本次覆盖变更的 source_ref。跨会话累计同门换组，换 board/back 不清零；追加上限保存 regroup_extension 的 limit、quote、source_ref，核实是该项目该门的真实新授权。只存命令与决定来源，不复制故事事实；Worker/observer 凭据经宿主交付，不把完整环境写入此账。
- **骨架（首次上岗时照抄建立，此后只追加）**：

```markdown
# 授权台账（chief-editor · 只追加不改写）

## 用户预授权策略原话
- 收取日期：YYYY-MM-DD
- 原话：
> ……
（未声明时本节保留并注明：按保守默认执行——T1 仅限引擎机制内的治理动作，一切作者字段上报。
  收到声明后在此追加新条目并注明日期；本节既有行不改写。）

## 台账（一行一命令，照此格式追加）
- [YYYY-MM-DD HH:MM] P=<项目绝对路径> | tier=T? | decision_kind=author|delegated | argv=`python "$NOVEL_LEDGER/scripts/novel.py" --project "$PROJECT" …（完整参数）` | 原话="…"（无则留空） | 返回=owner:…, decision-id:…, plan_hash:…, committed_chapter:…
```

- **填写规则**：argv 记完整命令行（含 --owner/--source 等全部参数）；原话逐字；返回值只记引擎实际返回的字段，没有的省略；上报未获答复、执行被拒也要记（tier 照记，outcome 记拒绝 code）。

## 5. 运行复盘 `postmortems/YYYY-MM-DD-<slug>-<id>.md`

- **何时写**：交付后、T2 停点后、用户纠偏后。
- **何时读**：下次立项前、流程文件修订时。
- **骨架（照抄后填）**：

```markdown
# 运行复盘：<slug>

- date: YYYY-MM-DD
- project: <项目绝对路径>
- trigger: 交付完成 / 重大停点 / 用户纠偏（三选一或注明组合）

## engine_refusals（引擎实际返回的拒绝 code + 一句话处置）
1. <code> — <处置>

## market_vs_actual（立项时的市场假设 vs 实际表现）
- 假设：
- 实际：

## lesson（一句话教训）
- 

## playbook_change_proposal（改哪节、改成什么；交 support 主笔更新，总编不自行改）
- 
```

- **填写规则**：engine_refusals 只记实际返回；postmortem 证据块逐条引用事前预测，不回写阈值或候选。market_vs_actual 作为该块投影，区分判断错误、执行偏离、曝光变化、观察不足；没有真实读者数据时写“市场适配未验证”。完本、机械通过、作者认可各自记，均不充作商业成功或全书文学认可。长篇兑现仅引用现有引擎事实源/Worker报告，不复制小说事实。
