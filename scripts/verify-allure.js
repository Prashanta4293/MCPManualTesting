const fs = require('fs');
const path = require('path');
const results = fs.readdirSync('allure-results').filter(f => f.endsWith('-result.json')).map(f => JSON.parse(fs.readFileSync(path.join('allure-results', f), 'utf8')));
const problems = [];
for (const result of results) {
  const attachments=[];
  function walk(node) { attachments.push(...node.attachments || []); for(const step of node.steps || []) walk(step); }
  walk(result);
  for (const label of ['suite','feature','story','severity']) if(!result.labels.some(l=>l.name===label)) problems.push(`${result.name}: missing ${label}`);
  if(!result.description) problems.push(`${result.name}: missing description`);
  for (const name of ['Expected result','Actual result','Tested URL','Console errors','Network errors']) if(!attachments.some(a=>a.name===name)) problems.push(`${result.name}: missing ${name}`);
  for (const a of attachments) if(!fs.existsSync(path.join('allure-results',a.source))) problems.push(`${result.name}: attachment file missing ${a.source}`);
  if(['failed','broken'].includes(result.status)) {
    for(const type of ['image/png','video/webm']) if(!attachments.some(a=>a.type===type)) problems.push(`${result.name}: failure artifact missing ${type}`);
  }
}
console.log(JSON.stringify({attemptsChecked:results.length,problems},null,2));
process.exit(problems.length ? 1 : 0);
