const fs=require('fs');
const path=require('path');
const results=fs.existsSync('allure-results') ? fs.readdirSync('allure-results').filter(f=>f.endsWith('-result.json')).map(f=>JSON.parse(fs.readFileSync(path.join('allure-results',f),'utf8'))) : [];
const latest=new Map();
for(const r of results) if(!latest.has(r.name)||r.stop>latest.get(r.name).stop) latest.set(r.name,r);
for(const r of [...latest.values()].sort((a,b)=>a.name.localeCompare(b.name))) {
  if(r.status!=='passed') console.log(JSON.stringify({name:r.name,status:r.status,error:r.statusDetails?.message?.slice(0,1800)}));
}
console.log(JSON.stringify({finishedCases:latest.size,attempts:results.length,byLatestStatus:[...latest.values()].reduce((s,r)=>(s[r.status]=(s[r.status]||0)+1,s),{})}));
