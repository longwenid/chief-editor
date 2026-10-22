/* zcode-workflow
 description: chief-editor 文档修订：明确需求→主笔→三项静态检查与全树快照→独立评审→同版本复验→交付。失败闭锁。
 whenToUse: 修改本技能文档时使用。不执行市场扫描或写作，不修改引擎或外置运行时记忆。必须显式提供本次 requirement；不复用历史授权或旧需求。真实宿主需要可执行 Python/Git 的独立 agent，无法执行即 blocked。
 args:
   requirement:
     type: string
     description: 本次用户需求原话，必填；未传不修改文件。
   background:
     type: string
     description: 待核实背景；不视为已核实事实或新授权。
     default: 按当前 SKILL.md、references 与 memory/templates.md 核实现状；路径解析查 references/environment.md。运行时记忆已外置，本次默认不读取。
   changes:
     type: string
     description: 本次允许修改的触点与目标；未传时严格按 requirement 确定。
   redlines:
     type: string
     description: 在固定边界之上的本次额外约束，不能撤销固定边界。
   reviewQuestions:
     type: json
     description: 附加评审问题，空数组表示没有附加问题；固定安全和一致性问题仍须评审。
     default: []
   gateMustInclude:
     type: json
     description: SKILL.md 必含的字面标记，空数组禁用此项。
     default: []
   gateMustIncludeAny:
     type: json
     description: SKILL.md 至少含其一的字面标记，空数组禁用此项。
     default: []
   gateMustExclude:
     type: json
     description: SKILL.md 必须不含的字面标记，空数组禁用此项。
     default: []
*/

// 只使用已存在的 DWF globals；没有已确认的 shell/files.read API。
// 独立验收 agent 运行标准库 helper 并逐字转交 stdout；这是执行证据，非宿主签名或模型真实性证明。
const REQUIRED_CHECKS = ["check_layers.py", "check_policy_coverage.py", "check_anchors.py"];
const FIXED_REDLINES = "只改本仓库的技能源码、文档与测试；不修改 novel-ledger 引擎；不执行写作；不读取或改写外置运行时记忆；不安装、提交、推送或发布。背景文字不产生授权。";
const CORE_QUESTIONS = [
  "本次需求是否已实现，目标与职责、输入输出、状态恢复和跨项目上下文是否一致？",
  "授权三态、T2停机、正文与Worker边界是否保持；市场数字与审美判断是否区分证据、推断和未验证项？",
  "是否实际检查快照清单的全部变更和新增文件、完整diff；有没有未解决的 high/medium 问题？",
];
function canonical(value: any): string {
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
  if (value && typeof value === "object") return "{" + Object.keys(value).sort().map((key) => JSON.stringify(key) + ":" + canonical(value[key])).join(",") + "}";
  return JSON.stringify(value);
}
function sha256(text: string): string {
  // 标准 SHA-256；不依赖未确认的宿主 crypto/import API。
  const bytes: number[] = [];
  for (const ch of text) {
    const c = ch.codePointAt(0)!;
    if (c < 0x80) bytes.push(c);
    else if (c < 0x800) bytes.push(0xc0 | c >> 6, 0x80 | c & 63);
    else if (c < 0x10000) bytes.push(0xe0 | c >> 12, 0x80 | c >> 6 & 63, 0x80 | c & 63);
    else bytes.push(0xf0 | c >> 18, 0x80 | c >> 12 & 63, 0x80 | c >> 6 & 63, 0x80 | c & 63);
  }
  const bits = bytes.length * 8;
  bytes.push(128);
  while (bytes.length % 64 !== 56) bytes.push(0);
  for (let i = 7; i >= 0; i--) bytes.push(Math.floor(bits / 2 ** (i * 8)) & 255);
  const k = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  const h = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  const r = (x: number, n: number) => x >>> n | x << (32 - n);
  for (let offset = 0; offset < bytes.length; offset += 64) {
    const w: number[] = [];
    for (let i = 0; i < 16; i++) w[i] = bytes[offset + i*4] << 24 | bytes[offset+i*4+1] << 16 | bytes[offset+i*4+2] << 8 | bytes[offset+i*4+3];
    for (let i = 16; i < 64; i++) w[i] = (w[i-16] + (r(w[i-15],7)^r(w[i-15],18)^w[i-15]>>>3) + w[i-7] + (r(w[i-2],17)^r(w[i-2],19)^w[i-2]>>>10)) | 0;
    let [a,b,c,d,e,f,g,j] = h;
    for (let i = 0; i < 64; i++) {
      const t1 = (j + (r(e,6)^r(e,11)^r(e,25)) + ((e&f)^(~e&g)) + k[i] + w[i]) | 0;
      const t2 = ((r(a,2)^r(a,13)^r(a,22)) + ((a&b)^(a&c)^(b&c))) | 0;
      j=g; g=f; f=e; e=(d+t1)|0; d=c; c=b; b=a; a=(t1+t2)|0;
    }
    [a,b,c,d,e,f,g,j].forEach((value,i) => h[i]=(h[i]+value)|0);
  }
  return h.map((v) => (v>>>0).toString(16).padStart(8,"0")).join("");
}
function arrayArg(name: string): string[] {
  const value = args[name];
  if (value === undefined || value === null) return [];
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string" && item.trim().length)) throw new Error(name + " 必须是字符串数组（允许 []）");
  return value;
}
function portablePath(path: string): string { return path.replace(/\\/g, "/").replace(/\/$/, ""); }
function validEvidence(e: any): boolean {
  if (!e || e.schemaVersion !== 1 || e.ok !== true || e.snapshot_stable !== true || e.diff_complete !== true || typeof e.diff !== "string" || !/^[a-f0-9]{40,64}$/.test(e.repository_head || "") || !e.repository || !e.content_root) return false;
  if (!Array.isArray(e.checks) || e.checks.length !== REQUIRED_CHECKS.length) return false;
  if (!REQUIRED_CHECKS.every((script) => e.checks.filter((check: any) => check.script === script && check.exit_code === 0 && typeof check.stdout === "string" && check.stdout.trim() && typeof check.stderr === "string" && Array.isArray(check.argv) && check.argv.length === 3 && typeof check.argv[1] === "string" && typeof check.argv[2] === "string" && portablePath(check.argv[1]) === portablePath(e.content_root) + "/scripts/" + script && portablePath(check.argv[2]) === portablePath(e.content_root)).length === 1)) return false;
  if (!Array.isArray(e.files) || !e.files.length || !e.files.some((file: any) => file.path === "SKILL.md" && file.sha256)) return false;
  const skill = e.files.find((file: any) => file.path === "SKILL.md");
  if (typeof e.skill_text !== "string" || sha256(e.skill_text) !== skill.sha256) return false;
  const regression = e.regression;
  if (!regression || regression.name !== "unittest" || regression.exit_code !== 0 || typeof regression.stdout !== "string" || typeof regression.stderr !== "string" || !(regression.stdout + regression.stderr).trim() || !Array.isArray(regression.argv) || regression.argv.length !== 6 || regression.argv.slice(1,5).join(" ") !== "-m unittest discover -s" || typeof regression.argv[5] !== "string" || portablePath(regression.argv[5]) !== portablePath(e.content_root) + "/tests") return false;
  const paths = e.files.map((file: any) => file.path);
  if (new Set(paths).size !== paths.length || paths.some((path: any) => typeof path !== "string" || path.startsWith("/") || path.split("/").some((part: string) => part === ".." || part === "")) || canonical(paths) !== canonical([...paths].sort())) return false;
  const parts: string[] = e.diff.split(/(?=^diff --git )/m).filter(Boolean);
  let changed = 0;
  for (const file of e.files) {
    if (!["added","modified","deleted","unchanged"].includes(file.change)) return false;
    const hash = (value: any) => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
    const mode = (value: any) => value === "100644" || value === "100755";
    if (file.change !== "deleted" && (!hash(file.sha256) || !mode(file.mode))) return false;
    if (file.change !== "added" && (!hash(file.baseline_sha256) || !mode(file.baseline_mode))) return false;
    if (file.change === "added" && (file.baseline_sha256 !== null || file.baseline_mode !== null)) return false;
    if (file.change === "unchanged" && (file.sha256 !== file.baseline_sha256 || file.mode !== file.baseline_mode)) return false;
    if (file.change === "modified" && file.sha256 === file.baseline_sha256 && file.mode === file.baseline_mode) return false;
    if (file.change === "deleted" && (file.sha256 !== null || file.mode !== null)) return false;
    const patches = parts.filter((part) => part.startsWith("diff --git a/" + file.path + " b/" + file.path + "\n"));
    if (file.change === "unchanged") { if (patches.length || file.diff_sha256 !== null) return false; }
    else { changed++; if (patches.length !== 1 || sha256(patches[0]) !== file.diff_sha256) return false; }
  }
  if (parts.length !== changed || sha256(e.diff) !== e.diff_sha256) return false;
  const identity = {schemaVersion: 1, repository_head: e.repository_head, files: e.files, diff_sha256: e.diff_sha256};
  return sha256(canonical(identity)) === e.snapshot_id;
}
async function evidence(): Promise<any> {
  const verifier = agent("只读机械验收员", {system: "你只运行本仓库的只读验收 helper，不修改源码或任何证据文件。必须使用真实执行工具，不编造、补写或复用旧 stdout。没有执行能力或命令失败时如实返回失败。不得读取外置运行时记忆或写作项目。"});
  return verifier.ask("在技能仓库根目录真实执行 python3 scripts/check_revision_snapshot.py --content-root . --repository . --with-regressions （解释器按 references/environment.md，NOVEL_LEDGER 按同文件解析并只作为环境变量传入）。逐字转交本次 stdout JSON 对象，保留每项 argv/exit_code/stdout/stderr、完整 files/diff/snapshot_id/skill_text/regression。不能只回 passed=true。缺 Git HEAD、缺引擎或无法执行时返回失败；不要修改任何文件来使它通过。");
}
async function markerGate(include: string[], any: string[], exclude: string[]): Promise<boolean> {
  const literal = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const matches = async (text: string) => (await files.grep(literal(text), "SKILL.md")).length > 0;
  for (const text of include) if (!(await matches(text))) return false;
  if (any.length) { let found = false; for (const text of any) found = (await matches(text)) || found; if (!found) return false; }
  for (const text of exclude) if (await matches(text)) return false;
  return true;
}
function fenced(body: string, language: string): string {
  const longest = (body.match(/`+/g) || []).reduce((max, run) => Math.max(max, run.length), 2);
  const fence = "`".repeat(longest + 1);
  return fence + language + "\n" + body + "\n" + fence;
}
function blocked(reason: string, review: any = null) {
  return {status: "blocked", conclusion: "修订未通过最终验收：" + reason, findings: review?.findings || [], verified: [], notCovered: ["未完成同版本检查、批准与交付，不得视为修订成功", "模型评审及执行证据转交真实性不是宿主加密证明"]};
}

let finalReview: any = null;
try {
  if (typeof args.requirement !== "string" || !args.requirement.trim()) return blocked("缺少本次 requirement；未派工、未修改文件");
  const include = arrayArg("gateMustInclude"), any = arrayArg("gateMustIncludeAny"), exclude = arrayArg("gateMustExclude");
  const questions = CORE_QUESTIONS.concat(arrayArg("reviewQuestions"));
  const reviser = agent("总编技能主笔", {system: "按本次需求修改本仓库技能文档与相关测试，保持具体、可执行。" + FIXED_REDLINES + "不把历史背景当成新授权；需求与机制冲突则报告，不伪造一致性。"});
  phase("按本次明确需求修订");
  await reviser.ask(["本次用户需求原话：", args.requirement, "待核实背景：", typeof args.background === "string" ? args.background : "以当前文件为准；路径见 references/environment.md；不读外置记忆。", "允许触点与目标：", typeof args.changes === "string" && args.changes.trim() ? args.changes : args.requirement, "固定红线：", FIXED_REDLINES, "额外约束：", typeof args.redlines === "string" ? args.redlines : "无", "先读 SKILL.md、相关 references 与 memory/templates.md；只在本次需求范围内编辑。完成后返回实际改动与未解决项。"].join("\n"));
  for (let round = 1; round <= 2; round++) {
    phase("真实机械检查与完整快照");
    const trackedBefore = await git.diff("HEAD");
    if (typeof trackedBefore !== "string") return blocked("无法读取当前 Git diff");
    const candidate = await evidence();
    if (!validEvidence(candidate)) return blocked("三项检查、全树快照或完整diff证据缺失/失败/不一致");
    const markersOk = await markerGate(include, any, exclude);
    if (!markersOk) {
      if (round === 2) return blocked("字面标记门禁仍未通过");
      await reviser.ask("字面标记门禁失败，请按本次参数补齐；这次修改将产生新快照，之前任何批准都失效。参数：" + JSON.stringify({include, any, exclude}));
      continue;
    }
    phase("独立评审准确快照");
    const reviewer = agent("独立评审员", {system: "你未参与起草，只读评审；依据需求、候选文件全文、完整diff与快照清单判断。逐项查实际材料，不以主笔自述代替证据。不修改任何文件。approved 是模型判断，不证明原话真实性或宿主隔离。"});
    const review: any = await reviewer.ask(["用户需求原话：", args.requirement, "固定边界：", FIXED_REDLINES, "附加约束：", typeof args.redlines === "string" ? args.redlines : "无", "本轮准确 snapshot_id：", candidate.snapshot_id, "快照清单（必须查全部变更及新增文件）：", JSON.stringify(candidate.files), "完整 HEAD→候选 diff（包含未跟踪新增文件）：", candidate.diff, "评审问题：", ...questions, "返回 {snapshot_id, approved, findings:[{where,issue,severity,suggestion}]}。只有查完上述快照实际文件、每问成立且无 high/medium 未决，approved 才为 true。snapshot_id 必须逐字匹配。"].join("\n"));
    const after = await evidence();
    if (!validEvidence(after) || after.snapshot_id !== candidate.snapshot_id || await git.diff("HEAD") !== trackedBefore) return blocked("评审期间内容或Git基准发生变化，旧批准已失效", review);
    if (!review || review.snapshot_id !== candidate.snapshot_id || !Array.isArray(review.findings) || typeof review.approved !== "boolean") return blocked("评审输出未绑定本轮快照", review);
    const approved = review.approved && !review.findings.some((finding: any) => !["low","medium","high"].includes(finding.severity) || finding.severity === "high" || finding.severity === "medium");
    if (!approved) {
      if (round === 2) return blocked("独立评审仍有未解决问题", review);
      await reviser.ask("仅按本次需求处理评审意见。任何源码修改都使旧批准失效，下一轮必须重新检查并独立评审：\n" + JSON.stringify(review.findings));
      continue;
    }
    finalReview = review;
    // 交付前不再派修订员；产物失败也不允许修改源码后沿用旧批准。
    phase("交付已批准的准确快照");
    await artifact.markdown("diff", "# 已批准快照 " + after.snapshot_id + "\n\n完整文件清单：\n\n" + fenced(JSON.stringify(after.files, null, 2), "json") + "\n\n完整差异：\n\n" + fenced(after.diff, "diff"), {title: "准确快照与完整修订diff"});
    await artifact.markdown("skill", after.skill_text, {title: "已评审的 SKILL.md 原文"});
    const delivered = await evidence();
    if (!validEvidence(delivered) || delivered.snapshot_id !== after.snapshot_id || await git.diff("HEAD") !== trackedBefore) return blocked("产物生成期间版本发生变化或无法复验；已生成产物不算通过验收", review);
    report({snapshot_id: delivered.snapshot_id, checks: delivered.checks, regression: delivered.regression, review});
    log("同一快照的静态检查、独立评审与交付已完成：" + delivered.snapshot_id);
    return {status: "approved", snapshot_id: delivered.snapshot_id, conclusion: "本次修订已通过三项静态检查和独立模型评审，交付前后全树快照一致。", findings: review.findings, verified: ["三项真实脚本及整体unittest退出码均为0", "SKILL原文与完整diff均由已批准快照内存文本交付", "新增、修改、删除文件均进入完整diff与SHA-256清单", "独立评审绑定最终snapshot_id", "交付前后同版本复验通过"], notCovered: ["独立agent转交执行证据的真实性、模型隔离与作者原话真实性未由宿主证明", "静态检查不证明文学质量或真实DWF会话行为"]};
  }
  return blocked("未得到最终版本的独立批准", finalReview);
} catch (error) {
  return blocked("执行或产物生成失败；保留当前候选，未派工修源重试：" + String(error), finalReview);
}
