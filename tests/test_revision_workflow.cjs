// Node 内置工具执行 TS 工作流；不安装 SDK，不运行真实 agent 或写产物。
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {stripTypeScriptTypes} = require('node:module');
const {test} = require('node:test');
const source = fs.readFileSync(path.join(__dirname, '../.zcode/workflows/chief-editor-revision.dwf.ts'), 'utf8');
const body = stripTypeScriptTypes('async function workflow(){\n'+source+'\n}');
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
const execute = new AsyncFunction('args','agent','files','git','artifact','phase','report','log',body+'\nreturn workflow();');
const sha = s => crypto.createHash('sha256').update(s).digest('hex');
const canonical = v => Array.isArray(v) ? '['+v.map(canonical).join(',')+']' : v && typeof v==='object' ? '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}' : JSON.stringify(v);
function evidence(version='品位与想法') {
  const diff = `diff --git a/SKILL.md b/SKILL.md\nnew file mode 100644\n--- /dev/null\n+++ b/SKILL.md\n@@ -0,0 +1 @@\n+${version}\n`;
  const files = [{path:'SKILL.md',sha256:sha(version+'\n'),mode:'100644',baseline_sha256:null,baseline_mode:null,change:'added',diff_sha256:sha(diff)}];
  const identity = {schemaVersion:1,repository_head:'a'.repeat(40),files,diff_sha256:sha(diff)};
  return {...identity,snapshot_id:sha(canonical(identity)),diff,skill_text:version+'\n',regression:{name:'unittest',argv:['python3','-m','unittest','discover','-s','/repo/tests'],exit_code:0,stdout:'',stderr:'OK'},repository:'/repo',content_root:'/repo',ok:true,diff_complete:true,snapshot_stable:true,checks:['check_layers.py','check_policy_coverage.py','check_anchors.py'].map(script=>({script,argv:['python3','/repo/scripts/'+script,'/repo'],exit_code:0,stdout:'[OK]\n',stderr:''}))};
}
async function run(options={}) {
  const state = {revisionCalls:0,reviews:[],evidenceCalls:0,artifacts:[],grepCalls:[],prompts:[]};
  const versions = options.evidence || [evidence()];
  const agent = name => ({ask:async prompt => {
    state.prompts.push({name,prompt});
    if(name==='只读机械验收员') { const i=state.evidenceCalls++; return structuredClone(versions[Math.min(i,versions.length-1)]); }
    if(name==='总编技能主笔') { state.revisionCalls++; return {changed:[]}; }
    const id=prompt.split('本轮准确 snapshot_id：\n')[1].split('\n')[0];
    state.reviews.push(id);
    return options.review ? options.review(state.reviews.length,id) : {snapshot_id:id,approved:true,findings:[]};
  }});
  const artifact = {markdown:async (...v)=>{state.artifacts.push(v);if(options.onArtifact)options.onArtifact(v,state);if(options.failArtifact===v[0])throw Error('artifact failed');},file:async()=>{throw Error('dynamic source path must not be delivered');}};
  const result = await execute({requirement:'修复本次需求',...(options.args||{})},agent,{grep:async p=>{state.grepCalls.push(p);return options.grep ? options.grep(p) : [];}},{diff:async()=>options.gitDiff || 'tracked diff'},artifact,()=>{},()=>{},()=>{});
  return {result,state};
}
test('explicit empty arrays disable optional markers and successful delivery binds a SHA-256 snapshot',async()=>{
  const {result,state}=await run({args:{gateMustInclude:[],gateMustIncludeAny:[],gateMustExclude:[],reviewQuestions:[]}});
  assert.equal(result.status,'approved');assert.equal(result.snapshot_id,evidence().snapshot_id);assert.equal(state.grepCalls.length,0);assert.equal(state.reviews.length,1);assert.equal(state.evidenceCalls,3);assert.equal(state.artifacts.length,2);
});
test('missing requirement performs no revision',async()=>{
  const {result,state}=await run({args:{requirement:''}});assert.equal(result.status,'blocked');assert.equal(state.revisionCalls,0);
});
test('missing or failed real checks cannot become an approval',async()=>{
  for(const mutate of [e=>{e.checks.pop();},e=>{e.checks[0].exit_code=1;},e=>{e.checks[0].stdout='';},e=>{e.diff_complete=false;},e=>{e.diff+='tamper';},e=>{e.checks[0].argv[1]='/other.py';}]){
    const e=evidence();mutate(e);const {result,state}=await run({evidence:[e]});assert.equal(result.status,'blocked');assert.equal(state.artifacts.length,0);assert.equal(state.reviews.length,0);
  }
});
test('review rejection followed by source fix requires a new snapshot and approval',async()=>{
  const a=evidence('旧版'),b=evidence('新版');
  const {result,state}=await run({evidence:[a,a,b,b,b],review:(round,id)=>({snapshot_id:id,approved:round===2,findings:round===1?[{where:'SKILL.md',issue:'需修复',severity:'medium',suggestion:'修复'}]:[]})});
  assert.equal(result.status,'approved');assert.equal(state.revisionCalls,2);assert.deepEqual(state.reviews,[a.snapshot_id,b.snapshot_id]);assert.equal(result.snapshot_id,b.snapshot_id);
});
test('changes during review invalidate approval without delivering',async()=>{
  const {result,state}=await run({evidence:[evidence('甲'),evidence('乙')]});assert.equal(result.status,'blocked');assert.equal(state.artifacts.length,0);assert.equal(state.revisionCalls,1);
});
test('artifact failure never asks writer to repair and reuse the old approval',async()=>{
  for(const failArtifact of ['diff','skill']){const {result,state}=await run({failArtifact});assert.equal(result.status,'blocked');assert.equal(state.revisionCalls,1);assert.equal(state.reviews.length,1);}
});
test('changes during artifact generation block final success',async()=>{
  const a=evidence('甲'),b=evidence('乙');const {result,state}=await run({evidence:[a,a,b]});assert.equal(result.status,'blocked');assert.equal(state.artifacts.length,2);assert.equal(state.revisionCalls,1);
});
test('a review with a wrong snapshot or unresolved medium finding cannot approve',async()=>{
  for(const review of [(round,id)=>({snapshot_id:'wrong',approved:true,findings:[]}),(round,id)=>({snapshot_id:id,approved:true,findings:[{severity:'medium'}]})]){const {result}=await run({review});assert.equal(result.status,'blocked');}
});
test('marker repairs happen before independent approval and markers are literal',async()=>{
  let seen=0;const {result,state}=await run({args:{gateMustInclude:['a.b']},grep:p=>{assert.equal(p,'a\\.b');return ++seen===1?[]:[{}];}});assert.equal(result.status,'approved');assert.equal(state.revisionCalls,2);assert.equal(state.reviews.length,1);
});
test('extra patches not accounted for in the manifest fail closed',async()=>{
  const e=evidence();e.diff+='diff --git a/hidden.py b/hidden.py\n+hidden\n';e.diff_sha256=sha(e.diff);e.snapshot_id=sha(canonical({schemaVersion:1,repository_head:e.repository_head,files:e.files,diff_sha256:e.diff_sha256}));const {result}=await run({evidence:[e]});assert.equal(result.status,'blocked');
});

test('Windows evidence paths are normalized without changing source paths',async()=>{
  const e=evidence();e.content_root='C:\\work\\chief-editor';e.repository=e.content_root;
  e.regression.argv[5]=e.content_root+'\\tests';
  for(const check of e.checks)check.argv=['python',e.content_root+'\\scripts\\'+check.script,e.content_root];
  const {result}=await run({evidence:[e]});assert.equal(result.status,'approved');
});
test('Python full diff and canonical hashes match the workflow verifier',async()=>{
  const {spawnSync}=require('node:child_process');
  const program=`import importlib.util,json,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('snapshot',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
current={'SKILL.md':('新版\\n'.encode(),'100644'),'new.py':(b'no newline','100755'),'binary.bin':(b'\\x00new','100644'),'unchanged.md':(b'fixed','100644')}
base={'SKILL.md':('旧版\\n'.encode(),'100644'),'gone.md':(b'old','100644'),'unchanged.md':(b'fixed','100644')}
e=m.describe(current,base,'a'*40)
e.update(ok=True,diff_complete=True,snapshot_stable=True,content_root='/repo',repository='/repo',skill_text=current['SKILL.md'][0].decode(),regression=dict(name='unittest',argv=['python3','-m','unittest','discover','-s','/repo/tests'],exit_code=0,stdout='',stderr='OK'),checks=[dict(script=x,argv=['python3','/repo/scripts/'+x,'/repo'],exit_code=0,stdout='OK',stderr='') for x in m.CHECKS])
print(json.dumps(e,ensure_ascii=False))`;
  const py=spawnSync(process.env.PYTHON || 'python3',['-c',program,path.join(__dirname,'../scripts/check_revision_snapshot.py')],{encoding:'utf8',env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'}});
  assert.equal(py.status,0,py.stderr);const {result}=await run({evidence:[JSON.parse(py.stdout)]});assert.equal(result.status,'approved');
});

test('temporary source mutation and restoration cannot alter frozen Markdown delivery',async()=>{
  let live='approved source';
  const e=evidence(live);
  const {result,state}=await run({evidence:[e],onArtifact:(args)=>{live='temporary wrong source';if(args[0]==='skill')assert.equal(args[1],e.skill_text);live='approved source';}});
  assert.equal(result.status,'approved');assert.equal(state.artifacts.find(a=>a[0]==='skill')[1],e.skill_text);
});
test('skill bytes or overall regression evidence mismatch blocks delivery',async()=>{
  for(const mutate of [e=>{e.skill_text+='wrong';},e=>{e.regression.exit_code=1;},e=>{e.regression=null;}]){const e=evidence();mutate(e);const {result,state}=await run({evidence:[e]});assert.equal(result.status,'blocked');assert.equal(state.artifacts.length,0);}
});
