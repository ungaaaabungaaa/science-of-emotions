import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { validateReport, pairSummary, rankedLabels, splitDifference } from '../web/model.mjs';

const report = JSON.parse(await readFile(new URL('../web/assets/report.json', import.meta.url)));

test('bundled report follows the schema and all pair count invariants', () => {
  assert.equal(validateReport(report), report);
  assert.equal(report.splits.all.rows, 54263);
});
test('conditional pair rate uses the conditioning label count', () => {
  const joy = report.labels.indexOf('joy');
  const optimism = report.labels.indexOf('optimism');
  const result = pairSummary(report.splits.test, joy, optimism);
  assert.equal(result.both, 7);
  assert.equal(result.givenA, 7 / report.splits.test.counts[joy]);
  assert.equal(result.givenB, 7 / report.splits.test.counts[optimism]);
  assert.notEqual(result.givenA, result.givenB);
});
test('empty conditioning set has no estimate', () => {
  const result = pairSummary({ rows: 5, counts: [0, 2], pairCounts: [[0, 0], [0, 2]] }, 0, 1);
  assert.equal(result.givenA, null);
  assert.equal(result.givenB, 0);
});
test('ranking is deterministic and differences use percentage points', () => {
  assert.equal(rankedLabels(report, 'test')[0].label, 'neutral');
  const i = report.labels.indexOf('joy');
  assert.equal(splitDifference(report, i), (report.splits.test.rates[i] - report.splits.train.rates[i]) * 100);
});
test('changed schemas, invalid counts and asymmetric pair data are rejected', () => {
  for (const mutate of [r => r.schemaVersion = 9, r => r.splits.test.rows = 0,
    r => r.splits.test.counts[0] = -1, r => r.splits.test.pairCounts[0][1] += 1,
    r => r.splits.test.rates[0] = 1, r => r.labels[0] = '<script>']) {
    const broken = structuredClone(report); mutate(broken);
    assert.throws(() => validateReport(broken), /report/i);
  }
});
test('pooled vectors must equal split sums even when each split is internally valid', () => {
  const broken = structuredClone(report);
  const all = broken.splits.all;
  all.counts[0] += 1; all.annotations += 1;
  all.pairCounts[0][0] += 1; all.rates[0] = all.counts[0] / all.rows;
  assert.throws(() => validateReport(broken), /report/i);
});
