// Assemble real executions: retain unchanged cases from a full run and replace selected cases
// with their freshly executed corrected tests. Original runs stay archived for auditability.
const fs=require('fs');
const path=require('path');
const root=path.resolve(__dirname,'..');
const baseDir=path.resolve(root,process.argv[2] || '');
if(!baseDir.startsWith(path.join(root,'run-history')+path.sep)) throw new Error('Specify an archived run under run-history/');
const prior=JSON.parse(fs.readFileSync(path.join(baseDir,'test-results/execution.json'),'utf8'));
const current=JSON.parse(fs.readFileSync('test-results/execution.json','utf8'));
const selected=new Map();
function visit(suites,fn){ for(const s of suites){ for(const spec of s.specs||[])fn(spec); visit(s.suites||[],fn); } }
visit(current.suites,spec=>selected.set(spec.title,spec));
if(!selected.size) throw new Error('No rerun cases');
fs.copyFileSync('test-results/execution.json','test-results/targeted-rerun.json');
let replaced=0;
visit(prior.suites,spec=>{ if(selected.has(spec.title)){ Object.assign(spec,selected.get(spec.title)); replaced++; } });
if(replaced!==selected.size) throw new Error('Rerun case is not present in original full suite');
const raw=path.join(baseDir,'allure-results');
for(const file of fs.readdirSync(raw).filter(f=>f.endsWith('-result.json'))){
  const r=JSON.parse(fs.readFileSync(path.join(raw,file),'utf8'));
  if(selected.has(r.name))continue;
  if(!fs.existsSync(path.join('allure-results',file))) fs.copyFileSync(path.join(raw,file),path.join('allure-results',file));
  const copyAttachments=node=>{ for(const a of node.attachments||[]) { const dest=path.join('allure-results',a.source); if(!fs.existsSync(dest)) fs.copyFileSync(path.join(raw,a.source),dest); } for(const step of node.steps||[])copyAttachments(step); };
  copyAttachments(r);
}
const artifacts=path.join(baseDir,'test-results/artifacts');
const ids=[...selected.keys()].map(n=>n.split(' ')[0]);
for(const file of fs.readdirSync(artifacts)){ if(file.startsWith('.') || ids.some(id=>file.includes(id)))continue; fs.cpSync(path.join(artifacts,file),path.join('test-results/artifacts',file),{recursive:true,force:false}); }
const statuses=[]; visit(prior.suites,s=>s.tests.forEach(t=>statuses.push(t.status)));
prior.stats={...prior.stats, duration:prior.stats.duration+current.stats.duration, expected:statuses.filter(s=>s==='expected').length, unexpected:statuses.filter(s=>s==='unexpected').length, flaky:statuses.filter(s=>s==='flaky').length, skipped:statuses.filter(s=>s==='skipped').length};
prior.executionProvenance={type:'Full Chromium run plus targeted correction rerun',fullRun:baseDir,fullRunStart:prior.stats.startTime,rerunStart:current.stats.startTime,replacedCases:[...selected.keys()],note:'Original results retained for all unchanged tests. Selected cases use actual rerun results, including retry attempts. No outcomes synthesized.'};
fs.writeFileSync('test-results/execution.json',JSON.stringify(prior,null,2));
fs.writeFileSync('test-results/execution-provenance.json',JSON.stringify(prior.executionProvenance,null,2));
console.log(JSON.stringify({cases:statuses.length,replacedCases:[...selected.keys()],provenance:prior.executionProvenance},null,2));
