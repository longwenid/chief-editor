# 记忆模板与填写规则（chief-editor/memory/）

写任何一条记忆前先对本文件。五类记录的字段模板、文件命名与追加纪律如下。**字段缺失时留空并标注"未记录"，不得凭记忆编造补齐**；所有数字、引语、URL 只用当次实测材料（榜单快照 / 引擎返回 / 用户原话），来源 URL 与抓取或执行日期必填。

## 通用纪律

1. **authorization.md 只追加不改写**：历史条目与头部已收取的策略原话永不修改；策略变更 = 在头部区块追加新条目并注明日期。
2. **旧市场快照不改写**：每月新建 `market/YYYY-MM.md`；与往月的对比增量写进新档。
3. **teardowns/<书名>.md 每书一份**；重拆同一书 = 新文件加日期后缀（`<书名>-YYYYMMDD.md`），不覆盖旧档。
4. **decisions 与 postmortems 文件名**：`YYYY-MM-DD-<slug>.md`；slug 用短横线连写的小写词（拼音或英文）。
5. **唯一允许回写的既有记忆**：decisions 条目的 `status` 字段（active → delivered / shelved）。其余任何记忆文件落盘后不改。
6. 每份记录开头写明 `record_type` 与生成身份（chief-editor）；拆解、快照类记录在文末列 sources（URL + 抓取日期）。

## 源等级标尺（写 sources[].grade 用）

- **A**：平台官方榜单/详情页、权威机构报告（当次实测可读）——可直接支撑结论。
- **B**：机构媒体报道——做机制与趋势背书，不做数据主源。
- **D**：自媒体/社区单源——只作交叉线索，不得单独支撑结论。

锚点（2026-10 首次快照实测标注）：中国作协蓝皮书 = A、中新网巅峰榜机制报道 = B、smzdm 社区帖 = D。

---

## 1. 市场快照 `market/YYYY-MM.md`

- **何时写**：每次扫描完成后（一月一档，不改旧档）。
- **何时读**：立项提案前（序列 C）、拆解选书时（序列 B）、下次扫描对比增量时。
- **骨架（照抄后填）**：

```markdown
# 市场快照 YYYY-MM

- snapshot_month: YYYY-MM
- scan_date: YYYY-MM-DD
- 说明: 本档落盘后不改写；次月新建对比。

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

## crossover（双源一致的高置信方向；双榜同书或双平台同方向才入）
1. **<方向>** — 支撑：<条目引用>；置信依据：<双榜/双平台/机构背书>

## volume_benchmarks（体量基准尺）
- 付费盘：
- 免费盘：
- 拥挤度分母（分类在库数）：

## pitfalls_hit（本次命中/复验的坑 → 降级动作）
1. <坑> → <降级动作>
```

- **填写规则**：paid_rank/free_rank 只记榜单与详情页**明文数字**，样本没给的格填"未记录"；书 ID 只从榜单页链接抄，自造必 404；crossover 只收双源一致项，单源观察留在各盘"观察"小节。

## 2. 对标拆解 `teardowns/<对标书名或书ID>.md`

- **何时写**：每完成一本对标拆解。
- **何时读**：立项提案时（生成候选）、开书门自执 premise/world 门时（方向输入与红线自查）。
- **骨架（照抄后填）**：

```markdown
# 对标拆解：<书名>

## book
- title / author / platform / url / 抓取日期：

## structure（四轴，除此之外不拆）
- genre_promise（题材与读者承诺 → genre 门方向输入）：
- gimmick_shape（脑洞形状：一条根规则 + 谁与谁博弈 + 兑现节奏 → premise/world 门）：
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

- **填写规则**：四轴之外不写文学评价；abstractions 必须用抽象结构语言（如"低资源方靠规则知识与大势力博弈"），对标书的措辞不进任何门输入；red_line_check 三条全打勾才可进立项候选；cliché 命中只标注不毙稿——告警转呈用户，作者坚持以作者为准，但候选必须附差异增量声明。

## 3. 选题决策 `decisions/YYYY-MM-DD-<slug>.md`

- **何时写**：立项落定后（三通道任一：A 用户想法——压力测试结论呈用户、落定后 / B 总编自决 / C 用户拍板）；交付或搁置时回写 status（唯一允许的回写）。
- **何时读**：每次唤醒（定位活动项目与授权脉络）、复盘时。
- **骨架（照抄后填）**：

```markdown
# 选题决策：<slug>

- date: YYYY-MM-DD
- slug: 
- selection_mode: A-用户想法 / B-总编自决 / C-多案拍板   # 判定见 SKILL.md 控制回路第3步与 playbook §C
- status: active          # 交付后回写 delivered；搁置回写 shelved
- project_path: <项目绝对路径>
- authorization_index: <对应 authorization.md 条目日期>
- links: 快照=memory/market/YYYY-MM.md；拆解=memory/teardowns/<书名>.md

## candidates（全部候选，含落选）
1. **<方向一句话>**
   - 结构来源：memory/teardowns/<书名>.md（+ 快照条目引用）
   - 差异增量声明：对标组合已被市场拥有，本书在其上新增<根规则>……
   - 建议档位：<引用 volume_benchmarks 依据>

## chosen
- 选定：<候选编号/名称>

## author_quote（口径随 selection_mode，均逐字不改写：A=用户想法原话；B=委托原话（常设或逐次）＋当次代选理由；C=用户拍板原话）
> 
```

- **填写规则**：selection_mode 三选一必填；candidates 必须含全部候选与各自差异增量声明（通道B 只记唯一主见时也按候选格式留档；无增量的候选当初就不该提出）；author_quote 逐字保留，不改写不摘要——通道B 先逐字引委托原话（常设授权或逐次委托原话），当次代选理由另起一行补记（理由可述，原话不可动）。

## 4. 授权台账 `memory/authorization.md`（只追加不改写）

- **何时写**：每次执行带 --source / --reason / --owner 的治理命令时追加一行。
- **何时读**：每次唤醒（恢复 owner 与已授权范围）、上报前（核对原话）、复盘时。
- **头部**：用户预授权策略原话——首次上岗时收取并存入；未声明时按保守默认执行并在头部注明。
- **条目字段**：date、project、command（完整 argv）、source_quote（用户原话，无则留空）、outcome（owner / decision-id / plan_hash / committed_chapter 等返回值）、tier（T0/T1/T2）。
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
- [YYYY-MM-DD HH:MM] P=<项目绝对路径> | tier=T? | argv=`python <novel-ledger>/scripts/novel.py --project <P> …（完整参数）` | 原话="…"（无则留空） | 返回=owner:…, decision-id:…, plan_hash:…, committed_chapter:…
```

- **填写规则**：argv 记完整命令行（含 --owner/--source 等全部参数）；原话逐字；返回值只记引擎实际返回的字段，没有的省略；上报未获答复、执行被拒也要记（tier 照记，outcome 记拒绝 code）。

## 5. 运行复盘 `postmortems/YYYY-MM-DD-<slug>.md`

- **何时写**：交付后、T2 停点后、用户纠偏后。
- **何时读**：下次立项前、playbook 修订时。
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

- **填写规则**：engine_refusals 只记引擎实际返回的 code（从 authorization.md 与现场输出回捞），不凭印象归类；market_vs_actual 对照 decisions 条目立项时的假设写，市场数据是选题信号不是创作目标——不得把代理指标写成质量结论。
