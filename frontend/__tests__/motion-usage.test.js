const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const FORBIDDEN = [
  'motion.button',
  'motion.section',
  'motion.form',
  'motion.aside',
  'motion.header',
  'motion.footer',
  'motion.nav',
  'motion.article',
  'motion.main',
  "motion('div')",
];

function collectTsx(dir, acc = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (['node_modules', '.next', '.git'].includes(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) collectTsx(full, acc);
    if (entry.isFile() && full.endsWith('.tsx')) acc.push(full);
  }
  return acc;
}

test('forbidden motion tags are not used in tsx files', () => {
  const files = collectTsx(ROOT);
  const violations = [];
  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8');
    for (const pattern of FORBIDDEN) {
      if (content.includes(pattern)) {
        violations.push(`${path.relative(ROOT, file)} contains ${pattern}`);
      }
    }
  }
  assert.equal(violations.length, 0, violations.join('\n'));
});
