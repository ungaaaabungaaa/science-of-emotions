# Verification record

Date: 27 October 2026. Local system: macOS arm64, Python 3.14.7, Node.js 24.18.0. The optional figure used Matplotlib 3.11.2 in an existing temporary environment; no global packages were installed.

## Data

The four official files in `data-source.json` were fetched at their locked revision. SHA-256 and byte counts matched. The full pipeline produced 54,263 unique comments across all official splits and no duplicate IDs. Repeating analysis with `--check web/assets/report.json` matched byte-for-byte. This is a real full-data run, not synthetic output.

## Automated checks

- `python3 -m unittest discover -s tests -v`: 19 tests pass. Covers multi-label/pair counting, Wilson boundaries, malformed and oversized rows/files, invalid UTF-8, within/across-split duplicate IDs, changed and missing sources, symlinks, exact processed-byte hashes, growing-file bounds, deterministic pooled reports, CLI output/check/overwrite refusal, controlled CLI failure, and local server restrictions.
- `node --test tests/viewer.test.mjs`: 6 tests pass. Covers the bundled report, conditional denominators, empty conditioning sets, deterministic ranking, percentage-point differences, malformed reports, and pooled count/pair integrity.
- `node --check web/app.mjs` and `python3 scripts/build.py`: pass. The build copies only five public viewer files.
- `git diff --check`: pass.

Tests were observed failing before the relevant implementation or correction. CI is configured to rerun checks on Python 3.11/3.14 and Node.js 22, and to independently download/reproduce the report. A local pass does not establish a CI pass; inspect the PR check results separately.

## Actual browser checks

The application ran on the loopback server. Desktop, 390px, and 320px layouts were inspected. At both narrow widths the document width equaled the viewport width. Mobile heading and overlap-label spacing were corrected after inspection. Browser sizing was reset after testing.

All-splits selection displayed 54,263 comments and 63,812 assignments. Selecting a frequency bar updated the first label and its report. Keyboard selection of both labels and the split worked. Joy/optimism in test data showed 7/161 and 7/186. Selecting neutral twice showed 1,787/1,787 (100%) in test data, with an explicit same-denominator explanation. Independent root review also checked all-splits neutral/admiration counts and the same-label case.

The screenshots in `docs/screenshots/` show the real running app. The prevalence figure was generated with Matplotlib from the real report. No generated cover is included.

## Limits

The viewer has not been deployed publicly. No model was trained; no clinical, physiological, individual mental-state, or population-wide performance is asserted. Raw source text remains outside Git. Local code cleanup follows remote backup and review, not this record alone.
