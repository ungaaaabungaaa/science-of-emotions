import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import stat

from emotion_lab.analysis import DataError, read_records, summarize, wilson_interval


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'sample.tsv'

    def write(self, text):
        self.path.write_text(text, encoding='utf-8')
        return self.path

    def test_multilabel_counts_each_comment_once_and_keeps_denominators(self):
        path = self.write('First text\t0,1\tid1\nSecond text\t1\tid2\nThird text\t2\tid3\n')
        result = summarize(read_records(path, 3, set()), 3, neutral_index=2)
        self.assertEqual(result['rows'], 3)
        self.assertEqual(result['annotations'], 4)
        self.assertEqual(result['counts'], [1, 2, 1])
        self.assertEqual(result['pairCounts'], [[1, 1, 0], [1, 2, 0], [0, 0, 1]])
        self.assertEqual(result['rates'], [1/3, 2/3, 1/3])
        self.assertEqual(result['labelCountHistogram'], {'1': 2, '2': 1})
        self.assertEqual(result['multiLabelRows'], 1)
        self.assertNotIn('First text', json.dumps(result))
        self.assertNotIn('id1', json.dumps(result))

    def test_duplicate_ids_across_files_fail(self):
        path = self.write('Text\t0\tid1\n')
        seen = set()
        self.assertEqual(list(read_records(path, 3, seen)), [(0,)])
        with self.assertRaisesRegex(DataError, 'duplicate comment ID'):
            list(read_records(path, 3, seen))

    def test_invalid_rows_fail_without_echoing_text(self):
        cases = ['Secret\t0,0\tid1\n', 'Secret\t3\tid1\n', 'Secret\t-1\tid1\n',
                 'Secret\t\tid1\n', 'Secret\t0\t\n', 'Secret\t0\tid1\textra\n',
                 '\t0\tid1\n', 'Secret\t0\tid1\n\n', 'Secret\x00\t0\tid1\n',
                 'Secret\t0\tid1\nOther\t1\tid1\n']
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(DataError) as error:
                    list(read_records(self.write(text), 3, set()))
                self.assertNotIn('Secret', str(error.exception))

    def test_invalid_utf8_and_limits(self):
        self.path.write_bytes(b'\xff\t0\tid1\n')
        with self.assertRaises(DataError):
            list(read_records(self.path, 3, set()))
        self.write('x' * 16385 + '\t0\tid1\n')
        with self.assertRaisesRegex(DataError, 'text size'):
            list(read_records(self.path, 3, set()))
        self.write('Text\t0\tid1\nText\t0\tid2\n')
        with self.assertRaisesRegex(DataError, 'row limit'):
            list(read_records(self.path, 3, set(), max_rows=1))

    def test_empty_file_fails(self):
        self.write('')
        with self.assertRaisesRegex(DataError, 'empty'):
            list(read_records(self.path, 3, set()))

    def test_processed_bytes_must_match_the_expected_hash(self):
        self.write('Text\t0\tid1\n')
        with self.assertRaisesRegex(DataError, 'changed while processing'):
            list(read_records(self.path, 3, set(), expected_sha256='0' * 64))

    def test_byte_limit_is_enforced_while_reading_not_only_at_stat(self):
        with self.path.open('w') as stream:
            for i in range(400):
                stream.write('x' * 16000 + f'\t0\tid{i}\n')
        with patch.object(Path, 'lstat', return_value=SimpleNamespace(st_mode=stat.S_IFREG, st_size=1)):
            with self.assertRaisesRegex(DataError, '6 MB'):
                list(read_records(self.path, 3, set()))

    def test_neutral_mixed_annotations_are_reported(self):
        path = self.write('Text\t0,2\tid1\n')
        self.assertEqual(summarize(read_records(path, 3, set()), 3, neutral_index=2)['neutralWithOtherRows'], 1)

    def test_wilson_interval_known_boundary_and_empty(self):
        self.assertIsNone(wilson_interval(0, 0))
        low, high = wilson_interval(0, 10)
        self.assertAlmostEqual(low, 0)
        self.assertAlmostEqual(high, 0.2775327999, places=8)
        low, high = wilson_interval(5, 10)
        self.assertAlmostEqual(low, 0.2365930905, places=8)
        self.assertAlmostEqual(high, 0.7634069095, places=8)


if __name__ == '__main__':
    unittest.main()
