# 市场证据、审美比较与校准

本模块只做三件事：把市场样本放回可比队列；用匿名成对细读及反例约束审美判断；把选题预测先登记、再按实际观察校准。商业适配、作品价值、作者已表达的偏好分别记录，不合成总分。热度可以影响商业判断，不能充当审美证据；偏好只能来自用户原话，缺失就是未表达。

## 设计与验收

- 四类记录：`market_snapshot`、`taste_comparison`、`selection_decision`、`postmortem`。每份 Markdown 只有一个 JSON 证据块；JSON 是该模块唯一真源，正文只展示摘要或引用 `record_id`，不另存相同字段。
- 市场卡带来源的真实上游 `origin_id`、观察时间和曝光干扰。队列按平台、商业模式、阶段、受众、指标单位/分母/窗口分开。头部、上升、普通、掉队样本各有观察或明确缺失原因；不把榜首截面写成趋势，不把同源转载写成独立双源。
- 审美卡先隐藏身份与榜位，用同类且处于声明长度范围的样本，给出可比理由；换序复评。每条判断写文本位置、叙事机制、阅读体验、代价和适用边界，另写反例。允许非模板佳作、不可比与不足以判断，不设模板合规奖励和伪总分。
- 创作增量按作品类型和本次阅读目标判断：解释它相对同类作品提供了什么不同体验、怎样成立并支撑建议体量。新增根规则只是可能来源，人物、关系、声音或生活经验也可以成立；不把这些可能来源变成逐项打勾的模板。
- 决策卡先登记带时间窗、指标、反证阈值和最低观察量的预测。复盘逐项区分判断错误、执行偏离、曝光变化和观察不足；没有读者数据就写“市场适配未验证”。
- 长篇兑现仅引用引擎已有事实源与 Worker 报告。主干不读小说正文、不新增故事事实账本；本模块不抓小说、不运行引擎。公共对标细读也保留位置指针，不把整段正文复制进记忆。
- 验收：正反回归覆盖无证据趋势、同源转载、不可比队列、未经表达的偏好、热度与文本相反、偏好冲突、未上架复盘和非模板判断。静态结构/可比性通过不等于文学质量或市场效果成立。

## 创作增量与开书主见

先说明这本书希望读者怎样读、记住什么，再选择适合其类型与阅读目标的比较依据。规则驱动的故事可以检验新规则是否改变选择与博弈；关系驱动的故事可以检验人物欲望和关系变化是否持续带来不可替代的体验；生活或声音驱动的故事可以检验具体经验、观察和叙述方式如何让熟悉处境变得可感。这些是判断示例，允许其他成立路径，也不要求一部作品同时满足它们。

创作增量须可辨识、能持续兑现，并守原创边界：说清它相对已知同类作品的差异、怎样形成阅读体验、要承受什么代价，以及为什么足以支撑建议体量。已有类型规则可以沿用；换名、叠加标签、机械加一条设定都不自动构成增量。没有可用文本时提出有依据的创作假设和反证条件，不把未写出的效果说成已经证明，也不因缺少新根规则淘汰人物或表达成立的选题。

总编负责给出可以执行的编辑主见。用户明确委托本次开书后，在 `policy.md` 界定的范围内完成方案、作出选择并修正自定项；用户给定核心时，在该核心与明确禁区内自主填缺；用户没有给定方向时，形成唯一主推并保留最接近的舍弃方案及取舍。每次判断应解释为什么选择、牺牲了什么和什么证据会使自己改变主意。用户明确约束、保留决定权或委托范围之外的变更按治理规则处理；主见不依靠综合分数，也不把尚未表达的作者偏好当依据。

## 文件与调用

```bash
python3 -B scripts/check_editorial_evidence.py <记录.json或.md> [其他记录...]
```

只读检查明确传入的文件，不递归扫描目录、不跟随记录里的指针取正文或联网。无参返回 `NOT_CHECKED` 和非零退出码；单元测试由 `python3 -B -m unittest discover -s tests -p test_editorial_evidence.py` 执行。跨记录引用必须把相应记录一起传入；复盘必须带原始决策，不能事后补造预登记。未提供实例时，只能报告实例未验证。

下文示例均为合成记录（`synthetic: true`），只能演示结构，不能作为真实市场证据。实际来源身份、原话真实性、匿名隔离与阅读效果仍需人工核实；脚本不会证明这些事实。

## 字段约定

市场时效取实际 `observations[].at`，新记录没有 scan_date；created_at 是编档时间，文件名是保存时间，均不能刷新旧数据。整档排序取实际观察时点最大值；使用某 claim 时只看其 evidence_ids 对应时点，无观察或日期缺失就不能当作当月证据。旧版 Markdown 才读其原 scan_date，不回写补造。

通用字段：`schema_version: 1`、`record_type`、唯一 `record_id`、有时区的 `created_at`、`sources`；示例另带 `synthetic: true`。source 用 `source_id/origin_id/ref/observed_at/kind`（上游未明时 origin_id=null 并写 origin_missing_reason，不计为独立源），其中 kind 为 `official_market/repost/public_text/worker_report/engine_state/author_message/reader_data`。转载须保留真实上游 origin_id，独立网页不是独立来源。ref 是可核验位置，不自动读取。

市场 claims 分 `kind: fact/inference/hypothesis`，`claim_type: observation/trend`，`scope: sample/market`，`status: supported/tentative/unverified`；假设不得伪装成已证实。supported trend 只陈述明确口径内的 sample：同一队列、同一作品或固定聚合序列、两个实际不同时点、已知分母与稳定曝光，方向与观察首尾一致。广泛市场趋势保持 tentative，不因另有几个无关样本就升级；supported 的 market 截面结论须其 evidence_ids 自身覆盖四类样本及两个独立 origin，声称独立支持也须两个真实上游。异队列、未知曝光或采样不足只能降级，不硬比较。队列 descriptor 本身的真实性及样本选择偏差仍需复核。

审美 findings 的 `basis` 只能是 `text`；其 source 必须是公共文本位置或隔离 Worker 的报告。先完成两轮匿名比较后，才可附 `context_after_review` 描述名气/榜位等背景，背景不进入审美依据。长度 band 是本次可比范围，必须说明理由，不是美学门槛；不可比时停判。反例可来自同对样本的另一处，也可来自第三个样本。

决策 basis 三栏各自写结论与验证状态。作者未表达偏好时写 `not_expressed`，不填偏好原话或推定顺从；已表达时必须有 `author_message` 来源与逐字 `quote`。偏好冲突时保持 `pending_author`；要选冲突方向必须有用户明确处置原话及定位。数值预测用 `falsifier.kind=numeric` 加 `operator: lt/lte/gt/gte/ne` 与 threshold；叙事承诺可用 `kind=qualitative` 加可观察 condition，不强制 metric 或分数。两类都先写 window、minimum_observations 与 source_plan；最低观察量是读者数或承诺检查覆盖量，不是美学分。复盘不得挪阈值或改条件。

复盘的 `confirmed/refuted` 是登记预测在指定观察窗内的结果，不能提升为文学认可；缺数据或不足最低观察量用 `unobserved`，尚未到窗末用 `pending`；部分观察保留真实量、来源和限度。定性观察以 condition_met、assessment 和 locations（报告/事实源的具体位置）解释反证条件是否满足，明确是人工/模型判断，不是机械质量证明。`market_fit` 仅为 `unverified/observed`，observed 至少要有真实读者数据；未发布或只有引擎通过时必须 unverified。归因可以有多项并给出证据说明，不用“执行不够好”掩盖预测错误。

### 选题控制元数据

`selection_decision.control` 是项目恢复的唯一字段源：`project_path/status/selection_mode/direction_fingerprint/authorization_index/decision_kind/author_quote/author_source_id`；delegated 另填 `delegated_reason`，理由与用户原话分开。`direction_fingerprint` 为当前方向投影，真实门重选完成后按 `memory/templates.md` 的“当前方向同步”更新，来源保留在原台账；其余立项内容不随当前方向重写。`candidates` 用 `candidate_id/proposal/increment`，chosen 是原立项的其中一个 candidate_id，不暗造未记录选项。作者偏好在 basis 中单独保存，不能从委托原话推定。

仅 decision_status=chosen 且有绝对项目路径时，control.status 才能 active/delivered/shelved。proposed/pending_author 必须 draft，路径未定用 null+project_path_reason，不纳入 active 项目恢复。授权定位和引语仍须与对话/原台账核对；本脚本只能校验来源字段，原话真实性保持未验证，不把它当成授权执行器。

现有记忆有独立 JSON 块就只回写主模板允许的 control.status 与当前方向投影，不在 Markdown 再建一套状态或指纹。旧 Markdown 记录按同样纪律更新对应原字段，不自动迁写或伪填缺失证据。当前方向与原立项预测不再相同时，复盘如实记录方向调整带来的适用范围变化，不能改原预测以伪装命中。

## 最小有效示例

以下四类完整示例与 tests/test_editorial_evidence.py 的 minimal_* fixture 同源核对，全部合成。每个块应分别作为一份记录；selection 的证据空缺明确 unverified，postmortem 引用该 selection，验证/保存时需显式提供原决策作为 --evidence，不能把示例复制成真实记录。

### 市场卡：只有局部趋势，其他层明确缺失

```json
{
  "schema_version": 1,
  "record_type": "market_snapshot",
  "record_id": "market-demo",
  "created_at": "2026-10-02T13:00:00Z",
  "synthetic": true,
  "sources": [
    {
      "source_id": "panel",
      "origin_id": "origin:synthetic-panel",
      "ref": "synthetic://panel",
      "observed_at": "2026-10-02T12:00:00Z",
      "kind": "official_market"
    }
  ],
  "cohorts": [
    {
      "cohort_id": "paid-new",
      "platform": "示例平台",
      "business_model": "paid",
      "stage": "new",
      "audience": "示例类型读者",
      "metric": {
        "name": "active_readers",
        "unit": "people",
        "denominator": "同一固定入组作品，非全市场",
        "window": "daily"
      }
    }
  ],
  "observations": [
    {
      "observation_id": "day1",
      "cohort_id": "paid-new",
      "work_id": "work-X",
      "role": "head",
      "at": "2026-10-01T12:00:00Z",
      "value": 100,
      "source_ids": [
        "panel"
      ],
      "exposure": {
        "state": "stable",
        "detail": "合成固定曝光样本"
      }
    },
    {
      "observation_id": "day2",
      "cohort_id": "paid-new",
      "work_id": "work-X",
      "role": "head",
      "at": "2026-10-02T12:00:00Z",
      "value": 120,
      "source_ids": [
        "panel"
      ],
      "exposure": {
        "state": "stable",
        "detail": "同一合成曝光条件"
      }
    }
  ],
  "missing_roles": {
    "rising": "未取得上升层样本",
    "ordinary": "未取得普通层样本",
    "dropout": "未取得掉队层样本；不做市场泛化"
  },
  "claims": [
    {
      "claim_id": "local-change",
      "kind": "inference",
      "claim_type": "trend",
      "direction": "up",
      "scope": "sample",
      "status": "supported",
      "statement": "该固定样本的观测人数上升；不能据此断言全市场偏好。",
      "evidence_ids": [
        "day1",
        "day2"
      ]
    }
  ]
}
```

### 品味卡：热度与文本冲突，非模板样本仍可获偏好

```json
{
  "schema_version": 1,
  "record_type": "taste_comparison",
  "record_id": "taste-demo",
  "created_at": "2026-10-02T13:00:00Z",
  "synthetic": true,
  "sources": [
    {
      "source_id": "blind-report",
      "origin_id": "origin:isolated-review",
      "ref": "synthetic://blind-report",
      "observed_at": "2026-10-02T12:00:00Z",
      "kind": "worker_report"
    }
  ],
  "comparability": {
    "status": "comparable",
    "reason": "同类决定场景；长度范围足以保留行动后果，不要求固定句式",
    "length_band": {
      "min": 300,
      "max": 900,
      "unit": "han"
    }
  },
  "pair": [
    {
      "label": "A",
      "source_id": "blind-report",
      "location": "匿名材料A，第1场景，行1-30",
      "genre": "现实幻想",
      "length": {
        "value": 500,
        "unit": "han"
      }
    },
    {
      "label": "B",
      "source_id": "blind-report",
      "location": "匿名材料B，第1场景，行1-35",
      "genre": "现实幻想",
      "length": {
        "value": 650,
        "unit": "han"
      }
    }
  ],
  "review": {
    "identity_hidden": true,
    "popularity_hidden": true,
    "first_order": [
      "A",
      "B"
    ],
    "repeat_order": [
      "B",
      "A"
    ],
    "first_verdict": "B",
    "repeat_verdict": "B",
    "final_verdict": "B"
  },
  "findings": [
    {
      "label": "A",
      "source_id": "blind-report",
      "basis": "text",
      "location": "A，行18-25",
      "mechanism": "声称牺牲，但后续行动未承受损失",
      "experience": "选择代价可被读者感知",
      "cost": "解释稍慢",
      "boundary": "只适用于本次场景与目标读者，不外推全书"
    },
    {
      "label": "B",
      "source_id": "blind-report",
      "basis": "text",
      "location": "B，行23-35",
      "mechanism": "人物用行动损失而非解释兑现选择",
      "experience": "选择代价可被读者感知",
      "cost": "解释稍慢",
      "boundary": "只适用于本次场景与目标读者，不外推全书"
    }
  ],
  "counterexample": {
    "label": "B",
    "source_id": "blind-report",
    "basis": "text",
    "location": "B，行1-6",
    "mechanism": "开头密集回顾削弱当下张力",
    "experience": "选择代价可被读者感知",
    "cost": "解释稍慢",
    "boundary": "只适用于本次场景与目标读者，不外推全书",
    "status": "observed",
    "challenges": "B也有信息拥堵，不能把行动兑现当成通用质量保证"
  },
  "context_after_review": "完成换序后揭盲：A为热榜头部，B无榜位；此背景不改变上述文本判断。",
  "template_deviation": "B没有三段打脸或句末钩子，本次仍因具体行动与代价被偏好；不为模板合规加分。"
}
```

### 决策卡：三栏分离，先登记可反证预测

```json
{
  "schema_version": 1,
  "record_type": "selection_decision",
  "record_id": "selection-demo",
  "created_at": "2026-10-03T12:00:00Z",
  "synthetic": true,
  "sources": [
    {
      "source_id": "author",
      "origin_id": "origin:conversation-message",
      "ref": "synthetic://author",
      "observed_at": "2026-10-02T12:00:00Z",
      "kind": "author_message"
    }
  ],
  "decision_status": "chosen",
  "control": {
    "project_path": "/synthetic/books/editorial-demo",
    "status": "active",
    "selection_mode": "B",
    "direction_fingerprint": "现实幻想×承诺的行动代价",
    "authorization_index": "authorization.md#合成委托条目",
    "decision_kind": "delegated",
    "author_quote": "这次请你定方向，先作受控试验。",
    "author_source_id": "author",
    "delegated_reason": "在委托范围内选择B；理由不冒充作者原话"
  },
  "candidates": [
    {
      "candidate_id": "B",
      "proposal": "候选B，先作受控试验",
      "increment": "用行动代价而非标签堆叠展开冲突"
    }
  ],
  "chosen": "B",
  "basis": {
    "commercial_fit": {
      "status": "unverified",
      "conclusion": "暂无读者或充分市场证据，商业适配未验证",
      "market_record_ids": []
    },
    "work_value": {
      "status": "unverified",
      "conclusion": "尚未取得可比匿名细读，不冒充文学认可",
      "taste_record_ids": []
    },
    "author_preference": {
      "status": "not_expressed",
      "alignment": "unknown"
    }
  },
  "predictions": [
    {
      "prediction_id": "retention",
      "statement": "指定试读窗口内读者留存率达到0.2；这只测该受众的商业适配",
      "metric": {
        "name": "reader_retention",
        "unit": "ratio",
        "denominator": "完成相同曝光流程的100名试读者"
      },
      "window": {
        "start": "2026-10-04T00:00:00Z",
        "end": "2026-10-10T23:59:59Z"
      },
      "falsifier": {
        "kind": "numeric",
        "operator": "lt",
        "threshold": 0.2
      },
      "minimum_observations": 100,
      "source_plan": {
        "kind": "reader_data",
        "ref": "经授权的同受众试读汇总；未试读则不评市场成败"
      }
    }
  ],
  "long_form_refs": []
}
```

### 复盘卡：未上架、无读者数据，市场适配未验证

```json
{
  "schema_version": 1,
  "record_type": "postmortem",
  "record_id": "postmortem-demo",
  "created_at": "2026-10-11T12:00:00Z",
  "synthetic": true,
  "sources": [],
  "selection_record_id": "selection-demo",
  "results": [
    {
      "prediction_id": "retention",
      "outcome": "unobserved",
      "attribution": [
        "insufficient_observation"
      ],
      "explanation": "作品尚未发布，也未开展授权试读；不能用引擎通过代替市场反馈",
      "observation": {
        "value": null,
        "sample_size": 0,
        "source_ids": [],
        "at": null
      }
    }
  ],
  "market_fit": "unverified",
  "lesson": "市场适配未验证；等待真实同口径读者观察，不回填阈值。",
  "long_form_refs": []
}
```

## 定性反证的填写方式

叙事承诺不必折成数字：prediction.falsifier 可写 kind=qualitative、condition="Worker审读前30章后，人物承诺仍只有口头声明，找不到承担行动代价的位置"；source_plan 指向引擎已有隔离审读报告，minimum_observations 表示至少检查一个声明窗口。复盘 observation 写 value=null、condition_met=true/false、assessment（依据与局限）、locations=[{source_id,location}]、实际覆盖量、来源与时点。条件满足对应 refuted，未满足对应 confirmed；这只说明该反证条件的观察结果，不是文学认可。主干只读报告结论与位置，不读正文；没有材料则 pending/unobserved，不重建小说事实账本。

## 设计依据与执行时复核

- [中国作家网的网络文学评价讨论](https://www.chinawriter.com.cn/n1/2022/0726/c404027-32485739.html)强调具体类型/文本与评价观念；本模块据此把商业流量和作品价值分开。这是设计取向，不是可自动证明的文学标准。
- [MT-Bench / Chatbot Arena 评审研究](https://arxiv.org/abs/2306.05685)揭示 LLM 评审的位置、冗长与自我偏好等局限。本模块据此采用匿名、换序和不稳定说明，属于防偏设计；该论文不证明这些措施对长篇小说审美有效。
- [番茄官方推荐验证流程调整通知](https://fanqienovel.com/writer/zone/article/7602553801446260761)是平台规则复核入口。当前可读取标题与发布时间，正文细则抓取不全；执行市场扫描时重新核对当时官方规则，不在本模块固化或声称验证任何具体阈值。
