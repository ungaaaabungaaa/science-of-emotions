from hashlib import sha256
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from emotion_lab.pipeline import build_report, fetch_file, report_text, verify_file
from emotion_lab.analysis import DataError
from emotion_lab.__main__ import main


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        names = ['calm', 'joy', 'neutral']
        content = {'emotions.txt': ('\n'.join(names) + '\n').encode(),
                   'train.tsv': b'Text\t0,1\tid1\nText\t1\tid2\n',
                   'dev.tsv': b'Text\t1\tid3\n', 'test.tsv': b'Text\t2\tid4\n'}
        self.manifest = {'revision': 'a' * 40, 'files': {}}
        for name, data in content.items():
            (self.root / name).write_bytes(data)
            self.manifest['files'][name] = {'sha256': sha256(data).hexdigest(), 'bytes': len(data),
                'url': f'https://raw.githubusercontent.com/google-research/google-research/{"a" * 40}/goemotions/data/{name}'}

    def test_report_is_deterministic_and_pools_counts(self):
        report = build_report(self.root, self.manifest)
        self.assertEqual(report['splits']['all']['rows'], 4)
        self.assertEqual(report['splits']['all']['counts'], [1, 3, 1])
        self.assertEqual(report['splits']['all']['rates'], [0.25, 0.75, 0.25])
        self.assertEqual(report_text(report), report_text(build_report(self.root, self.manifest)))
        self.assertNotIn('id1', report_text(report))
        self.assertNotIn('Text', report_text(report))

    def test_missing_changed_and_symlinked_inputs_fail(self):
        file = self.root / 'dev.tsv'
        file.write_bytes(b'changed')
        with self.assertRaisesRegex(DataError, 'hash'):
            build_report(self.root, self.manifest)
        file.unlink()
        with self.assertRaises(FileNotFoundError):
            build_report(self.root, self.manifest)
        file.symlink_to(self.root / 'train.tsv')
        with self.assertRaisesRegex(DataError, 'regular'):
            build_report(self.root, self.manifest)

    def test_verification_has_a_read_bound_even_for_growing_file(self):
        file = self.root / 'large'
        file.write_bytes(b'x' * 6_000_001)
        with self.assertRaisesRegex(DataError, '6 MB'):
            verify_file(file, {'sha256': '0' * 64, 'bytes': 6_000_001})

    def test_fetch_reuses_matching_file_and_refuses_changed_file(self):
        path = self.root / 'train.tsv'
        details = self.manifest['files']['train.tsv']
        self.assertEqual(fetch_file(path, details), 'reused')
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(DataError, 'hash'):
            fetch_file(path, details)
        self.assertEqual(path.read_bytes(), b'changed')

    def test_cross_split_id_collision_rejected_even_with_matching_hashes(self):
        data = b'Text\t0\tid1\n'
        (self.root / 'dev.tsv').write_bytes(data)
        self.manifest['files']['dev.tsv'].update(sha256=sha256(data).hexdigest(), bytes=len(data))
        with self.assertRaisesRegex(DataError, 'duplicate comment ID'):
            build_report(self.root, self.manifest)

    def test_cli_errors_are_controlled_and_do_not_create_output(self):
        out = self.root / 'report.json'
        run = subprocess.run([sys.executable, '-m', 'emotion_lab', 'analyze', '--data-dir', str(self.root), '--out', str(out)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn('hash', run.stderr)
        self.assertNotIn('Traceback', run.stderr)
        self.assertFalse(out.exists())

    def test_cli_writes_new_output_checks_it_and_never_overwrites(self):
        out = self.root / 'report.json'
        args = ['analyze', '--data-dir', str(self.root)]
        with patch('emotion_lab.__main__.source_manifest', return_value=self.manifest), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(main(args + ['--out', str(out)]), 0)
            original = out.read_bytes()
            self.assertEqual(main(args + ['--out', str(out)]), 1)
            self.assertEqual(out.read_bytes(), original)
            self.assertEqual(main(args + ['--check', str(out)]), 0)
            out.write_text('{}')
            self.assertEqual(main(args + ['--check', str(out)]), 2)


if __name__ == '__main__':
    unittest.main()
