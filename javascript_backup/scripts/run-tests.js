const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const root = path.resolve(__dirname, '..');
if (!process.argv.includes('--list')) {
  const archive = path.join(root, 'run-history', new Date().toISOString().replace(/[:.]/g, '-'));
  for (const name of ['allure-results', 'test-results', 'allure-report']) {
    const source = path.resolve(root, name);
    if (path.dirname(source) !== root) throw new Error('Archive path outside workspace');
    if (fs.existsSync(source)) { fs.mkdirSync(archive, { recursive: true }); fs.renameSync(source, path.join(archive, name)); }
  }
}
const args = process.argv.slice(2);
if (args.includes('--list')) args.push('--reporter=list');
const run = spawnSync(process.execPath, [require.resolve('@playwright/test/cli'), 'test', ...args], { cwd: root, stdio: 'inherit' });
process.exit(run.status ?? 1);
