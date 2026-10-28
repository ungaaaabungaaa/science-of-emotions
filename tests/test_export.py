import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent


class ExportTests(unittest.TestCase):
    def test_export_preserves_counts_denominators_and_intervals(self):
        report = json.loads((ROOT / 'web/assets/report.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'rates.csv'
            for split in ('train', 'dev', 'test', 'all'):
                with self.subTest(split=split):
                    result = subprocess.run([sys.executable, 'scripts/export_rates.py',
                                             '--split', split, '--out', str(output)],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    with output.open(newline='') as stream:
                        rows = list(csv.DictReader(stream))
                    self.assertEqual(len(rows), len(report['labels']))
                    for index, row in enumerate(rows):
                        data = report['splits'][split]
                        self.assertEqual(row['label'], report['labels'][index])
                        self.assertEqual(row['split'], split)
                        self.assertEqual(int(row['comments_with_label']), data['counts'][index])
                        self.assertEqual(int(row['total_comments']), data['rows'])
                        self.assertEqual(float(row['rate']), data['rates'][index])
                        self.assertEqual(float(row['wilson95_low']), data['wilson95'][index][0])
                        self.assertEqual(float(row['wilson95_high']), data['wilson95'][index][1])
                    output.unlink()

    def test_existing_output_is_preserved_and_invalid_split_is_controlled(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'keep.csv'
            output.write_text('keep me')
            result = subprocess.run([sys.executable, 'scripts/export_rates.py',
                                     '--split', 'test', '--out', str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(output.read_text(), 'keep me')
            result = subprocess.run([sys.executable, 'scripts/export_rates.py',
                                     '--split', 'invalid', '--out', str(Path(folder) / 'new.csv')],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((Path(folder) / 'new.csv').exists())
