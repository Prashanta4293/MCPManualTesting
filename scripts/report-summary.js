const fs=require('fs');
const report=JSON.parse(fs.readFileSync('test-results/execution.json','utf8'));
const tests=[];
function walk(suite){ for(const spec of suite.specs||[]) for(const t of spec.tests) tests.push({ name:spec.title, status:t.status, attempts:t.results.map(r=>r.status) }); for(const s of suite.suites||[]) walk(s); }
for(const s of report.suites) walk(s);
const summary={generatedAt:new Date().toISOString(),provenance:report.executionProvenance || {type:'Single test execution',startTime:report.stats.startTime},total:tests.length,passed:tests.filter(t=>['expected','flaky'].includes(t.status)).length,failed:tests.filter(t=>t.status==='unexpected').length,skipped:tests.filter(t=>t.status==='skipped').length,flaky:tests.filter(t=>t.status==='flaky').length,failedTests:tests.filter(t=>t.status==='unexpected').map(t=>t.name),reportLocation:'allure-report/index.html',tests};
fs.writeFileSync('test-results/summary.json',JSON.stringify(summary,null,2));
fs.writeFileSync('test-results/summary.md',`# Chromium execution\n\nSummary generated: ${summary.generatedAt}\n\nExecution: ${summary.provenance.type}. See summary.json for actual run timestamps and any replaced cases.\n\nTotal: ${summary.total}; passed: ${summary.passed}; failed: ${summary.failed}; skipped: ${summary.skipped}; flaky: ${summary.flaky}.\n\nReport: allure-report/index.html\n\n## Failed tests\n\n${summary.failedTests.map(n=>'- '+n).join('\n') || 'None'}\n`);
console.log(JSON.stringify({...summary,tests:undefined},null,2));
