const test = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const path = require('node:path');

test('typescript typecheck passes', () => {
  const projectRoot = path.resolve(__dirname, '..');
  const result = spawnSync('npm', ['run', 'typecheck'], {
    cwd: projectRoot,
    encoding: 'utf8',
  });

  if (result.status !== 0) {
    throw new Error(`Typecheck failed.\nSTDOUT:\n${result.stdout}\nSTDERR:\n${result.stderr}`);
  }

  assert.equal(result.status, 0);
});
