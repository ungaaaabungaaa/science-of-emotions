import { validateReport, pairSummary, rankedLabels, splitDifference } from './model.mjs';

const $ = id => document.getElementById(id);
const format = number => number.toLocaleString('en-US');
const percent = number => number === null ? 'No estimate' : `${(number * 100).toFixed(2)}%`;
const title = value => value.charAt(0).toUpperCase() + value.slice(1);

async function start() {
  const response = await fetch('assets/report.json');
  if (!response.ok) throw new Error('The measured aggregate report could not be loaded.');
  const text = await response.text();
  if (text.length > 1000000) throw new Error('The aggregate report exceeds the supported size.');
  const report = validateReport(JSON.parse(text));
  $('hero-total').textContent = format(report.splits.all.rows);
  for (const id of ['label-a', 'label-b']) {
    for (const [index, label] of report.labels.entries()) {
      const option = document.createElement('option'); option.value = index; option.textContent = title(label); $(id).append(option);
    }
  }
  $('label-a').value = report.labels.indexOf('joy');
  $('label-b').value = report.labels.indexOf('optimism');
  function render() {
    const name = $('split').value;
    const split = report.splits[name];
    const a = Number($('label-a').value), b = Number($('label-b').value);
    const label = report.labels[a], second = report.labels[b];
    $('split-context').replaceChildren();
    const strong = document.createElement('strong'); strong.textContent = format(split.rows);
    $('split-context').append(strong, document.createTextNode(' distinct comments · ' + format(split.annotations) + ' label assignments'));
    const bars = $('frequency-bars'); bars.replaceChildren();
    const ranked = rankedLabels(report, name);
    const max = ranked[0].rate;
    for (const row of ranked) {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'label-row';
      button.setAttribute('aria-pressed', String(a === row.index));
      button.setAttribute('aria-label', `${title(row.label)}: ${percent(row.rate)}, ${format(row.count)} of ${format(split.rows)} comments. Inspect label.`);
      const label = document.createElement('span'); label.className = 'label-name'; label.textContent = title(row.label);
      const track = document.createElement('span'); track.className = 'bar-track'; track.setAttribute('aria-hidden', 'true');
      const fill = document.createElement('span'); fill.className = 'bar-fill'; fill.style.width = `${row.rate / max * 100}%`; track.append(fill);
      const value = document.createElement('span'); value.className = 'row-rate'; value.textContent = `${(row.rate * 100).toFixed(1)}%`;
      button.append(label, track, value);
      button.addEventListener('click', () => { $('label-a').value = row.index; render(); $('label-a').focus(); });
      bars.append(button);
    }
    $('selected-title').textContent = title(label);
    $('selected-rate').textContent = percent(split.rates[a]);
    $('selected-count').textContent = `${format(split.counts[a])} of ${format(split.rows)} comments carry this label.`;
    $('selected-interval').textContent = split.wilson95[a].map(percent).join(' – ');
    const pair = pairSummary(split, a, b);
    $('pair-count').textContent = format(pair.both);
    $('pair-rate').textContent = `${percent(pair.rate)} of the selected split${a === b ? '; the same label was selected twice.' : '.'}`;
    $('given-a').textContent = `Among ${label}-labeled comments, ${percent(pair.givenA)} also carry ${second}. (${format(pair.both)}/${format(split.counts[a])})`;
    $('given-b').textContent = `Among ${second}-labeled comments, ${percent(pair.givenB)} also carry ${label}. (${format(pair.both)}/${format(split.counts[b])})`;
    $('given-a-bar').style.width = `${(pair.givenA ?? 0) * 100}%`;
    $('given-b-bar').style.width = `${(pair.givenB ?? 0) * 100}%`;
    $('pair-note').textContent = a === b ? 'The same label was selected twice. Its overlap with itself equals its count; both conditional rates use the same denominator.' : "Each percentage uses its named label's count as the denominator. Association does not establish a cause.";
    $('split-selected').textContent = title(label);
    $('train-rate').textContent = `${percent(report.splits.train.rates[a])} (${format(report.splits.train.counts[a])}/${format(report.splits.train.rows)})`;
    $('test-rate').textContent = `${percent(report.splits.test.rates[a])} (${format(report.splits.test.counts[a])}/${format(report.splits.test.rows)})`;
    const difference = splitDifference(report, a);
    $('split-difference').textContent = `${difference >= 0 ? '+' : ''}${difference.toFixed(2)} percentage points`;
    $('multi-note').textContent = `${format(split.multiLabelRows)} of ${format(split.rows)} comments have multiple labels. ${format(split.neutralWithOtherRows)} include neutral together with another label. Neutral is not treated as mutually exclusive.`;
  }
  for (const id of ['split', 'label-a', 'label-b']) $(id).addEventListener('change', render);
  render(); $('lab-content').hidden = false;
}

start().catch(error => { $('load-error').hidden = false; $('load-error').textContent = `${error.message} Start the local server with “python3 scripts/serve.py” and reload this page.`; });
