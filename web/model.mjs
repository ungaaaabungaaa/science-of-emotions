export function validateReport(report) {
  const fail = () => { throw new Error('The aggregate report is invalid or uses an unsupported schema.'); };
  if (report?.schemaVersion !== 1 || !Array.isArray(report.labels) || report.labels.length !== 28 || new Set(report.labels).size !== 28 || report.labels.some(label => !/^[a-z_]{1,40}$/.test(label))) fail();
  for (const name of ['train', 'dev', 'test', 'all']) {
    const split = report.splits?.[name];
    if (!split || !Number.isInteger(split.rows) || split.rows < 1 || split.rows > 150000) fail();
    for (const key of ['counts', 'rates', 'wilson95', 'pairCounts']) if (!Array.isArray(split[key]) || split[key].length !== 28) fail();
    for (let i = 0; i < 28; i++) {
      const count = split.counts[i];
      if (!Number.isInteger(count) || count < 0 || count > split.rows || Math.abs(split.rates[i] - count / split.rows) > 1e-12 || !Number.isFinite(split.rates[i])) fail();
      if (!Array.isArray(split.pairCounts[i]) || split.pairCounts[i].length !== 28) fail();
      for (let j = 0; j < 28; j++) {
        const both = split.pairCounts[i][j];
        if (!Number.isInteger(both) || both < 0 || both > Math.min(count, split.counts[j]) || both !== split.pairCounts[j]?.[i] || (i === j && both !== count)) fail();
      }
      const interval = split.wilson95[i];
      if (!Array.isArray(interval) || interval.length !== 2 || !interval.every(Number.isFinite) || interval[0] < 0 || interval[1] > 1 || interval[0] > interval[1]) fail();
    }
    if (split.annotations !== split.counts.reduce((a, b) => a + b, 0) || !Number.isInteger(split.multiLabelRows) || split.multiLabelRows < 0 || split.multiLabelRows > split.rows) fail();
  }
  if (report.splits.all.rows !== ['train', 'dev', 'test'].reduce((sum, name) => sum + report.splits[name].rows, 0)) fail();
  for (let i = 0; i < 28; i++) {
    if (report.splits.all.counts[i] !== ['train', 'dev', 'test'].reduce((sum, name) => sum + report.splits[name].counts[i], 0)) fail();
    for (let j = 0; j < 28; j++) if (report.splits.all.pairCounts[i][j] !== ['train', 'dev', 'test'].reduce((sum, name) => sum + report.splits[name].pairCounts[i][j], 0)) fail();
  }
  return report;
}

export function pairSummary(split, a, b) {
  const both = split.pairCounts[a][b];
  return { both, givenA: split.counts[a] ? both / split.counts[a] : null,
    givenB: split.counts[b] ? both / split.counts[b] : null,
    rate: both / split.rows, expectedUnderIndependence: split.counts[a] / split.rows * split.counts[b] / split.rows };
}

export function rankedLabels(report, split) {
  return report.labels.map((label, index) => ({ label, index, count: report.splits[split].counts[index], rate: report.splits[split].rates[index] }))
    .sort((a, b) => b.count - a.count || a.index - b.index);
}

export function splitDifference(report, index) {
  return (report.splits.test.rates[index] - report.splits.train.rates[index]) * 100;
}
