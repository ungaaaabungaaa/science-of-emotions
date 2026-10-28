import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from emotion_lab.sensitivity import count_sensitivity


class SensitivityTests(unittest.TestCase):
    def test_multilabel_assignment_fraction_keeps_comment_denominator(self):
        report = {'labels': ['rare', 'common', 'absent'],
                  'splits': {'test': {'rows': 3, 'annotations': 4, 'counts': [1, 3, 0]}}}
        result = count_sensitivity(report, [0, 1, 2, 4])['test']
        self.assertEqual(result['total_comments'], 3)
        self.assertEqual(result['total_label_assignments'], 4)
        self.assertEqual([row['retained_label_count'] for row in result['thresholds']], [3, 2, 1, 0])
        self.assertEqual([row['retained_assignment_fraction'] for row in result['thresholds']], [1, 1, .75, 0])
        self.assertEqual(result['thresholds'][2]['omitted_labels'], ['rare', 'absent'])
        self.assertEqual(result['thresholds'][2]['minimum_count'], 2)

    def test_threshold_bounds_are_explicit(self):
        for thresholds in [[], [1, 1], [True], [-1], [1_000_001], [1.5], list(range(17))]:
            with self.subTest(thresholds=thresholds), self.assertRaises(ValueError):
                count_sensitivity({'labels': [], 'splits': {}}, thresholds)

    def test_real_cli_reports_all_splits_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'sensitivity.json'
            command = [sys.executable, 'scripts/rare_label_sensitivity.py', '--minimum-counts', '1', '10', '50', '--out', str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(set(report['splits']), {'train', 'dev', 'test', 'all'})
            self.assertEqual(len(report['source_report_sha256']), 64)
            self.assertEqual(report['splits']['all']['total_comments'], 54263)
            before = output.read_bytes()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(output.read_bytes(), before)
