# Methods and measured results

## Question and source

How often do published emotion labels occur together, and how stable are their rates across the released data splits? This is a descriptive annotation experiment, not a test of emotion biology or an evaluation of a prediction model.

The pipeline reads four official Google Research files at revision `700de9630a39cf1c0ded1ea7d1092ec0f467c7a7`. Exact URLs, sizes, and SHA-256 hashes are in `data-source.json`. That revision was checked on 27 October 2026; this does not change the original data collection date.

The paper describes a larger corpus and a filtered subset based on annotator agreement. This experiment uses only the released filtered train, development, and test TSV files. The paper's corpus size and model scores are not new results of this project. [Primary paper](https://aclanthology.org/2020.acl-main.372/), [official source and model card](https://github.com/google-research/google-research/tree/700de9630a39cf1c0ded1ea7d1092ec0f467c7a7/goemotions).

All four hashes are verified before parsing. The parser rejects malformed columns, invalid UTF-8, repeated/out-of-range labels, invalid or repeated comment IDs, and documented size limits. IDs were unique across all three splits in this run. Text is validated and discarded; no text or IDs enter the aggregate report.

## Counting rules

For a split containing N comments, prevalence is the number carrying a label divided by N. Labels can overlap, so their prevalences need not sum to 100%. Each comment contributes once to each of its labels.

The symmetric pair matrix counts comments carrying both labels. Its diagonal equals each label's count. The conditional rate for B given A divides their intersection by A's count; the reverse rate divides by B's count. A zero denominator gives no estimate. Selecting the same label twice gives its count, with a 100% conditional rate when present.

The pooled report sums counts and pair matrices, then recomputes rates; it does not average split percentages. Wilson 95% intervals use z = 1.959963984540054 and a binomial counting model. Dependence, selection bias, and population generalization are outside that model.

## Full-run results

| Split | Comments | Assignments | Multiple labels | Neutral with another label |
| --- | ---: | ---: | ---: | ---: |
| Training | 43,410 | 51,103 | 7,102 | 1,396 |
| Development | 5,426 | 6,380 | 878 | 174 |
| Test | 5,427 | 6,329 | 837 | 181 |
| All | 54,263 | 63,812 | 8,817 | 1,751 |

The released data contains neutral with other labels. This pipeline reports those rows rather than removing or changing them.

In test data, joy appears on 161 comments and optimism on 186; their intersection is 7. Thus **4.35%** of joy-labeled comments also carry optimism, and **3.76%** of optimism-labeled comments also carry joy. Their intersection is **0.13%** of all test comments. These associations do not establish causes.

Joy prevalence is **3.3449%** in training data and **2.9666%** in test data: **−0.3782 percentage points**. The viewer repeats this descriptive comparison for every label. No hypothesis tests or multiple-comparison corrections are performed; do not present these differences as statistically significant shifts.

## Reproduction and limits

The README commands fetch and check the exact committed report. Deterministic ordering and no clock timestamps make repeated JSON byte-identical. `scripts/figure.py` renders the measured prevalences with Matplotlib. Fonts and rendering versions can change figure bytes; the JSON counts are the reproducibility target.

These are observers' judgments of selected short English Reddit comments. They do not directly measure writers' experienced emotions. Platform demographics, filtering, annotator background, and ambiguity affect the labels. This lab neither resolves theories of emotion nor estimates wider population prevalence. It has no diagnostic, biometric, employment-screening, or individual mental-state function.
