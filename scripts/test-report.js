const { spawnSync }=require('child_process');
const path=require('path');
const run=(file,args)=>spawnSync(process.execPath,[file,...args],{stdio:'inherit'});
const tests=run(path.join(__dirname,'run-tests.js'),process.argv.slice(2));
const report=run(path.join(process.cwd(),'node_modules/allure-commandline/bin/allure'),['generate','allure-results','--clean','-o','allure-report']);
run(path.join(__dirname,'report-summary.js'),[]);
process.exit(tests.status || report.status || 0);
