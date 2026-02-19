const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const appModalPath = path.resolve(__dirname, '../components/ui/AppModal.tsx');
const bottomSheetPath = path.resolve(__dirname, '../components/ui/BottomSheet.tsx');

test('AppModal uses motion.div and keyboard handlers on clickable overlay', () => {
  const content = fs.readFileSync(appModalPath, 'utf8');
  assert.match(content, /<motion\.div/);
  assert.match(content, /onKeyDown=\{\(event: React\.KeyboardEvent<HTMLDivElement>\)/);
  assert.match(content, /event\.key === 'Enter' \|\| event\.key === ' '/);
});

test('BottomSheet uses motion.div and keyboard handlers on clickable overlay', () => {
  const content = fs.readFileSync(bottomSheetPath, 'utf8');
  assert.match(content, /<motion\.div/);
  assert.match(content, /onKeyDown=\{\(event: React\.KeyboardEvent<HTMLDivElement>\)/);
  assert.match(content, /event\.key === 'Enter' \|\| event\.key === ' '/);
});
