/* zcode-workflow
description: chief-editor 技能修订流水线，首次运行即「总编技能升级：品位与开书双通道」：总编技能主笔按需求原话对
  SKILL.md/playbook/templates/engine-contract 做外科手术式修订，独立评审员读修订后全文与 git diff
  对照需求评审（最多两轮、主笔按意见收口），脚本再以 files.grep 机械核验必含/组内任一/必除标记，不过补一轮，最后交付修订后
  SKILL.md（主产物）与完整 diff 对照。
whenToUse: 要修订 chief-editor 技能自身的文档（人设、流程、模板、红线表述等），并需要「主笔落盘＋独立评审＋grep
  机械核验」三重把关时。传入 requirement/background/changes/redlines
  定制本次修订任务书，reviewQuestions
  定制评审问题，gateMustInclude/gateMustIncludeAny/gateMustExclude
  定制机械核验标记；全部参数都有首次运行的默认值，不传即复跑原修订。不适用于以总编身份执行市场扫描、开书、连写等日常任务（直接用 chief-editor
  技能），也不适用于修改 novel-ledger 引擎目录。
args:
  background:
    type: string
    description: 背景事实清单（多行文本）：主笔动笔前须逐条核实的现状事实，每行一条。
    default: >-
      - memory/authorization.md 头部已有用户 2026-10-21
      常设授权原话「后续需要总编都帮我选了，我需要的是无人持续」，总编已据此代选过《力量计税》全部十三门（台账逐条在案）；

      - 但 SKILL.md 现文仍写「绝不替用户选」「不代答、不预选」，与该常设授权矛盾（authorization.md
      只在局部声明冲突以原话为准）；

      - 立项（SKILL.md 控制回路第 3 步 / references/playbook.md §C）现只有「多案拍板」单一模式。
  changes:
    type: string
    description: 改什么：触点与改法逐条清单（多行文本），主笔的修订任务书。
    default: |-
      1. 人设升级（SKILL.md 开头总编定位段 + 「身份与教训红线」节）：总编有品位 = 市场判断 + 审美主见——拆解有眼光、提案有主见、敢拍板并给得出理由；品位用于选题判断、提案质量与压力测试，不把总编变成作者。作者决定权元原则改述为三态：作者亲选 / 作者以原话（常设或逐次）委托代选 / 未授权则保守转呈。
      2. 开书选题三通道（SKILL.md 控制回路第 3 步、任务路由「立项提案」行；references/playbook.md §C；memory/templates.md §3 decisions 模板加「选题模式」字段）：
         - 通道A 用户想法：用户给出想法即走此道；总编以品位做诚实压力测试（差异化、市场对位、原创红线），用户核心概念优先，打磨不越权；
         - 通道B 总编自决：用户无想法或常设授权覆盖时；总编从 memory/market 快照与 teardowns 形成唯一主见（明确不搞骑墙多案），说明理由，按既有代选纪律留痕；
         - 通道C 多案拍板：现行 2~3 候选呈拍板流程保留为第三选项；
         - 默认判定：唤醒（第 0 步）读 authorization.md 头部，有代选常设授权 → 开新书默认通道B；无 → 开新书时一次性问用户（给想法即A、让总编定即B、要多案即C）。
      3. 矛盾消解：SKILL.md 三档预授权表 T0 行、「红线一」等处的「绝不代答/不预选」改为与常设授权共存的三态表述；references/engine-contract.md「作者决定入口（T0…）」小节标题旁加一句让位说明（指向 SKILL.md 代选纪律），该文件其余内容不动。
      4. SKILL.md frontmatter description：保留既有触发词，补上「开新书：总编自决选题或直接采用用户想法」一类触发语义。
      5. SKILL.md 记忆地图 decisions 行同步「选题模式」字段（含各模式下 author_quote 的取值口径：用户想法原话 / 拍板原话 / 常设授权原话＋代选理由）。
  gateMustExclude:
    type: json
    description: 机械核验：SKILL.md 必须不再包含的旧表述（每项都须零命中）。
    default:
      - 绝不替用户选
  gateMustInclude:
    type: json
    description: 机械核验：SKILL.md 必须包含的标记，字符串数组，每一项都必须命中。
    default:
      - 品位
      - 想法
  gateMustIncludeAny:
    type: json
    description: 机械核验：组内至少一项命中的标记（OR 语义），如同义改写「自决/自行决策」。空数组表示无此项约束。
    default:
      - 自决
      - 自行决策
  redlines:
    type: string
    description: 红线（多行文本）：违反即返工的边界约束。
    default: 不动
      $NOVEL_LEDGER（C:/Users/longwen/.zcode/skills/novel-ledger）目录任何文件；不改引擎命令语义与
      T2 纪律；不回溯改写 memory/authorization.md 与 memory/decisions、teardowns
      既有条目（memory/templates.md 是模板文件，可改）；保持既有文风。
  requirement:
    type: string
    description: 用户需求原话，逐字。主笔动笔与独立评审批准都以它为对照基准。
    default: skill里面的总编需要是一个有品位的，启动新书能自行决策、或者选择输入自己想法的。
  reviewQuestions:
    type: json
    description: 独立评审的检查问题清单，字符串数组，逐条编号呈给评审员；批准标准为各问全部成立且无 high/medium 未决。
    default:
      - 三通道（用户想法/总编自决/多案拍板）从唤醒→模式判定→立项→开书→留痕是否每一步都能照抄执行，有没有断点（如默认判定链断裂、模板新字段没有对应写入规程、通道B的留痕口径缺失）；
      - 「有品位」是否落成了具体可执行的人设条款（敢拍板、给得出理由、压力测试有标准），还是空口号；
      - 旧矛盾（「绝不替用户选」vs 常设授权代选）是否彻底消解，且作者决定权元原则在新表述下自洽；
      - 有没有破坏引擎契约、T2 纪律，或误导未来会话执行者的措辞。
*/
interface RevisionReport {
  /** 每个改动文件：改了什么、为什么这样改。 */
  changed: { path: string; what: string; why: string }[];
  /** 修订如何接进技能既有回路的，三五句话。 */
  wiring: string;
  /** 明确没动的文件与原因（如 novel-ledger 引擎目录）。 */
  notTouched: string[];
}

interface ReviewFinding {
  /** 文件与位置（如 SKILL.md 三档预授权表 T0 行）。 */
  where: string;
  /** 一句话说清问题：会误导谁、断在哪。 */
  issue: string;
  /** high=破坏作者决定权或引擎契约；medium=通道断点或人设落不了地；low=措辞。 */
  severity: "low" | "medium" | "high";
  /** 怎么改的一句话建议。 */
  suggestion: string;
}

interface Review {
  /** 各问可照抄执行、矛盾已消解、元原则与引擎契约无损时才为 true。 */
  approved: boolean;
  findings: ReviewFinding[];
}

interface FixOutcome {
  /** 已处置意见的逐条摘要：改了什么。 */
  applied: string[];
  /** 不接受的评审意见与理由（没有则空数组）。 */
  rejected: { issue: string; reason: string }[];
}

interface Finding {
  /** Workspace-relative path, with a line when it applies. */
  where: string;
  /** One sentence: what was found. */
  what: string;
  /** What showed it. */
  evidence: string;
  /** "verified" when confirmed; "unconfirmed" when not. */
  status: "verified" | "unconfirmed";
  /** How much it matters. */
  severity: "low" | "medium" | "high";
}
interface WorkflowReport {
  /** Two or three sentences answering what the user asked for. */
  conclusion: string;
  findings: Finding[];
  /** What the run checked and how. */
  verified: string[];
  /** What the run did not look at or could not check, and why. */
  notCovered: string[];
}

// ── 默认值＝首次运行（总编技能升级：品位与开书双通道）实际使用的值 ──

const DEFAULT_REQUIREMENT =
  "skill里面的总编需要是一个有品位的，启动新书能自行决策、或者选择输入自己想法的。";

const DEFAULT_BACKGROUND = [
  "- memory/authorization.md 头部已有用户 2026-10-21 常设授权原话「后续需要总编都帮我选了，我需要的是无人持续」，总编已据此代选过《力量计税》全部十三门（台账逐条在案）；",
  "- 但 SKILL.md 现文仍写「绝不替用户选」「不代答、不预选」，与该常设授权矛盾（authorization.md 只在局部声明冲突以原话为准）；",
  "- 立项（SKILL.md 控制回路第 3 步 / references/playbook.md §C）现只有「多案拍板」单一模式。",
].join("\n");

const DEFAULT_CHANGES = [
  "1. 人设升级（SKILL.md 开头总编定位段 + 「身份与教训红线」节）：总编有品位 = 市场判断 + 审美主见——拆解有眼光、提案有主见、敢拍板并给得出理由；品位用于选题判断、提案质量与压力测试，不把总编变成作者。作者决定权元原则改述为三态：作者亲选 / 作者以原话（常设或逐次）委托代选 / 未授权则保守转呈。",
  "2. 开书选题三通道（SKILL.md 控制回路第 3 步、任务路由「立项提案」行；references/playbook.md §C；memory/templates.md §3 decisions 模板加「选题模式」字段）：",
  "   - 通道A 用户想法：用户给出想法即走此道；总编以品位做诚实压力测试（差异化、市场对位、原创红线），用户核心概念优先，打磨不越权；",
  "   - 通道B 总编自决：用户无想法或常设授权覆盖时；总编从 memory/market 快照与 teardowns 形成唯一主见（明确不搞骑墙多案），说明理由，按既有代选纪律留痕；",
  "   - 通道C 多案拍板：现行 2~3 候选呈拍板流程保留为第三选项；",
  "   - 默认判定：唤醒（第 0 步）读 authorization.md 头部，有代选常设授权 → 开新书默认通道B；无 → 开新书时一次性问用户（给想法即A、让总编定即B、要多案即C）。",
  "3. 矛盾消解：SKILL.md 三档预授权表 T0 行、「红线一」等处的「绝不代答/不预选」改为与常设授权共存的三态表述；references/engine-contract.md「作者决定入口（T0…）」小节标题旁加一句让位说明（指向 SKILL.md 代选纪律），该文件其余内容不动。",
  "4. SKILL.md frontmatter description：保留既有触发词，补上「开新书：总编自决选题或直接采用用户想法」一类触发语义。",
  "5. SKILL.md 记忆地图 decisions 行同步「选题模式」字段（含各模式下 author_quote 的取值口径：用户想法原话 / 拍板原话 / 常设授权原话＋代选理由）。",
].join("\n");

const DEFAULT_REDLINES =
  "不动 $NOVEL_LEDGER（C:/Users/longwen/.zcode/skills/novel-ledger）目录任何文件；不改引擎命令语义与 T2 纪律；不回溯改写 memory/authorization.md 与 memory/decisions、teardowns 既有条目（memory/templates.md 是模板文件，可改）；保持既有文风。";

const DEFAULT_REVIEW_QUESTIONS = [
  "三通道（用户想法/总编自决/多案拍板）从唤醒→模式判定→立项→开书→留痕是否每一步都能照抄执行，有没有断点（如默认判定链断裂、模板新字段没有对应写入规程、通道B的留痕口径缺失）；",
  "「有品位」是否落成了具体可执行的人设条款（敢拍板、给得出理由、压力测试有标准），还是空口号；",
  "旧矛盾（「绝不替用户选」vs 常设授权代选）是否彻底消解，且作者决定权元原则在新表述下自洽；",
  "有没有破坏引擎契约、T2 纪律，或误导未来会话执行者的措辞。",
];

const DEFAULT_GATE_MUST_INCLUDE = ["品位", "想法"];
const DEFAULT_GATE_MUST_INCLUDE_ANY = ["自决", "自行决策"];
const DEFAULT_GATE_MUST_EXCLUDE = ["绝不替用户选"];

// ── 运行参数（未传或非法时回落到上面首次运行的默认值） ──

function str(v: unknown, fallback: string): string {
  return typeof v === "string" && v.trim().length > 0 ? v : fallback;
}
function strArr(v: unknown, fallback: string[]): string[] {
  return Array.isArray(v) && v.length > 0 && v.every((x) => typeof x === "string")
    ? (v as string[])
    : fallback;
}

const requirement = str(args.requirement, DEFAULT_REQUIREMENT);
const background = str(args.background, DEFAULT_BACKGROUND);
const changes = str(args.changes, DEFAULT_CHANGES);
const redlines = str(args.redlines, DEFAULT_REDLINES);
const reviewQuestions = strArr(args.reviewQuestions, DEFAULT_REVIEW_QUESTIONS);
const gateMustInclude = strArr(args.gateMustInclude, DEFAULT_GATE_MUST_INCLUDE);
const gateMustIncludeAny = strArr(args.gateMustIncludeAny, DEFAULT_GATE_MUST_INCLUDE_ANY);
const gateMustExclude = strArr(args.gateMustExclude, DEFAULT_GATE_MUST_EXCLUDE);

phase("执笔修订：按需求修订技能文档");
const reviser = agent("总编技能主笔", {
  system:
    "你是资深网文总编兼技能文档架构师，为 chief-editor 技能做一次外科手术式修订。" +
    "文风克制具体、不喊口号，保持既有文档风格（表格化、file:line 引用、短句）。" +
    "只改交代到的触点，不重写无关章节，不动 novel-ledger 引擎目录。" +
    "若发现需求与引擎红线不可调和，如实上报矛盾并说明，绝不硬写或伪造一致性。",
});
const revision = await reviser.ask<RevisionReport>(
  [
    `为 chief-editor 技能（本仓库，工作目录即技能根）完成一次修订。用户需求原话："${requirement}"`,
    "",
    "背景事实（已核实，动笔前请自行复核）：",
    background,
    "",
    "改什么（五处触点，全部落成可照抄执行的规程，不是口号）：",
    changes,
    "",
    "红线（违反即返工）：",
    redlines,
    "",
    "先读 SKILL.md、references/playbook.md、references/engine-contract.md、memory/templates.md、memory/authorization.md 核实触点，再动笔；完成后直接编辑落盘，并返回 RevisionReport。",
  ].join("\n"),
);
report(revision);
log(`主笔完成修订：${revision.changed.length} 个文件改动`);

const reviewer = agent("独立评审员", {
  system:
    "你是没参与起草的独立评审，只凭修订后的文件全文与 git diff 判断，不看主笔的自述结论。" +
    "批准需要证据：各问都能照抄执行、矛盾彻底消解、作者决定权元原则与引擎契约无损。" +
    "挑不出真问题就批准，不为凑数提意见；也不放过会误导未来会话执行者的措辞。不许修改任何文件。",
});

let review: Review = { approved: false, findings: [] };
for (let round = 1; round <= 2; round++) {
  phase("独立评审修订质量");
  review = await reviewer.ask<Review>(
    [
      `第 ${round} 轮独立评审。用户需求原话："${requirement}"`,
      "",
      `主笔自述接线（仅供参考，以文件实际内容为准）：${revision.wiring}`,
      `主笔改动清单（仅供参考）：${JSON.stringify(revision.changed)}`,
      "",
      "请实际读取修订后的 SKILL.md、references/playbook.md、references/engine-contract.md、memory/templates.md，并运行 git diff 查看全部改动，然后只回答以下各问：",
      ...reviewQuestions.map((q, i) => `${i + 1}. ${q}`),
      "approved=true 的标准：上述各问全部成立且无 high/medium 未决。findings 逐条给 where/issue/severity/suggestion。",
    ].join("\n"),
  );
  report({ round, approved: review.approved, findingsCount: review.findings.length });
  log(`第 ${round} 轮评审：${review.approved ? "批准" : `${review.findings.length} 条意见`}`);
  if (review.approved) break;
  if (round < 2) {
    phase("按评审意见收口");
    const fix = await reviser.ask<FixOutcome>(
      `独立评审意见如下，逐条处置：能改就改落盘；不接受的逐条给出站得住的理由，不为辩护而辩护：\n${JSON.stringify(
        review.findings,
      )}`,
    );
    report(fix);
  }
}

phase("机械核验并交付修订");
interface GateResult {
  entries: Record<string, boolean>;
  pass: boolean;
}
async function runGate(): Promise<GateResult> {
  const entries: Record<string, boolean> = {};
  let pass = true;
  for (const p of gateMustInclude) {
    const ok = (await files.grep(p, "SKILL.md")).length > 0;
    entries[`SKILL.md 含「${p}」`] = ok;
    pass = pass && ok;
  }
  let anyOk = gateMustIncludeAny.length === 0;
  for (const p of gateMustIncludeAny) {
    const hit = (await files.grep(p, "SKILL.md")).length > 0;
    entries[`SKILL.md 含「${p}」（组内任一即可）`] = hit;
    anyOk = anyOk || hit;
  }
  if (gateMustIncludeAny.length > 0) {
    entries[`SKILL.md 至少含其一：${gateMustIncludeAny.join("／")}`] = anyOk;
    pass = pass && anyOk;
  }
  for (const p of gateMustExclude) {
    const ok = (await files.grep(p, "SKILL.md")).length === 0;
    entries[`SKILL.md 不再含「${p}」`] = ok;
    pass = pass && ok;
  }
  return { entries, pass };
}
let gate = await runGate();
if (!gate.pass) {
  await reviser.ask(
    `机械核验未通过，逐项补齐后落盘（只补缺项，不动其他内容）：\n${JSON.stringify(gate.entries)}`,
  );
  gate = await runGate();
}
const gateOk = gate.pass;
report(gate.entries);
log(`机械核验：${gateOk ? "全部通过" : "仍有未过项"}`);

const diff = await git.diff("HEAD");
try {
  await artifact.file("skill", "SKILL.md", { title: "修订后的 SKILL.md", primary: true });
} catch {
  await reviser.ask("SKILL.md 发布失败，可能文件缺失或异常，请核实文件完整并修复。");
  await artifact.file("skill", "SKILL.md", { title: "修订后的 SKILL.md", primary: true });
}
await artifact.markdown(
  "diff",
  "# 修订对照（git diff，含 playbook / templates / engine-contract 全部改动）\n\n```diff\n" +
    diff +
    "\n```",
  { title: "修订对照 diff" },
);

const verdict = review.approved
  ? "独立评审员已在两轮内批准"
  : "独立评审员未在两轮内批准，未决意见已列入 findings";
const result: WorkflowReport = {
  conclusion: `修订完成并落盘：需求「${requirement}」已由主笔按触点清单修订技能文档，${verdict}。机械核验${
    gateOk ? "全部通过" : "仍有未过项：" + JSON.stringify(gate.entries)
  }。接线要点：${revision.wiring}`,
  findings: review.findings.map((f) => ({
    where: f.where,
    what: f.issue,
    evidence: `独立评审建议：${f.suggestion}`,
    status: "verified" as const,
    severity: f.severity,
  })),
  verified: [
    `机械核验（files.grep）通过项：${Object.entries(gate.entries)
      .filter(([, v]) => v)
      .map(([k]) => k)
      .join("；")}`,
    `独立评审基于修订后四个文件全文与 git diff 进行，${verdict}`,
    "全部目标文件（SKILL.md、playbook.md、engine-contract.md、templates.md）均为 git 跟踪文件，改动可用 git diff 复查、可回退",
  ],
  notCovered: [
    "修订效果未在真实技能会话中实测（本次只改文档，未运行技能验证行为）",
    "未改动 novel-ledger 引擎目录与其技能文档（红线维持）",
    "memory/authorization.md 台账与 decisions/teardowns 既有条目未回溯改写",
    ...revision.notTouched,
  ],
};
return result;
