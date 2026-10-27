"""Optional publication figure. Requires Matplotlib; analysis/viewer do not."""

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
report = json.loads((ROOT / 'web/assets/report.json').read_text())
labels = report['labels']
order = sorted(range(len(labels)), key=lambda index: report['splits']['test']['rates'][index])
fig, ax = plt.subplots(figsize=(9, 10), layout='constrained')
fig.set_facecolor('#f3f0e8')
ax.set_facecolor('#f3f0e8')
for split, offset, color, label in [('train', -0.16, '#778b7b', 'Training'), ('test', 0.16, '#b64b32', 'Test')]:
    data = report['splits'][split]
    ax.barh([i + offset for i in range(len(labels))], [data['rates'][j] * 100 for j in order],
            height=0.29, color=color, label=f'{label} (n = {data["rows"]:,})')
ax.set_yticks(range(len(labels)), [labels[i] for i in order])
ax.set_xlabel('Comments carrying label (%)')
ax.set_ylabel('Published annotation label')
ax.set_title('GoEmotions: label prevalence across released splits', loc='left', fontsize=14, pad=18)
ax.spines[['top', 'right']].set_visible(False)
ax.grid(axis='x', alpha=0.18)
ax.set_axisbelow(True)
ax.legend(loc='lower right', frameon=False)
fig.text(0.02, -0.025, 'Measured from pinned GoEmotions TSVs. Labels can overlap; rates need not sum to 100%.\nDataset selection and annotator bias remain. This is not a population estimate or a model evaluation.', fontsize=9)
(ROOT / 'figures').mkdir(exist_ok=True)
fig.savefig(ROOT / 'figures/label-prevalence.png', dpi=150, bbox_inches='tight', metadata={'Software': 'Matplotlib'})
fig.savefig(ROOT / 'figures/label-prevalence.svg', bbox_inches='tight', metadata={'Date': None})
svg = ROOT / 'figures/label-prevalence.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
plt.close(fig)
print('Generated figures/label-prevalence.png and .svg from the bundled measured report.')
