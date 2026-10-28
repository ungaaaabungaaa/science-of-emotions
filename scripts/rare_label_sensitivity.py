"""Report minimum-count sensitivity from the bundled measured aggregate report."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from emotion_lab.sensitivity import count_sensitivity


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--minimum-counts', nargs='+', type=int, default=[1, 10, 50])
    parser.add_argument('--out', type=Path, required=True, help='New JSON file; never overwrite')
    args = parser.parse_args(argv)
    created = False
    try:
        raw = (ROOT / 'web/assets/report.json').read_bytes()
        report = json.loads(raw)
        result = {
            'schemaVersion': 1, 'source_report_sha256': sha256(raw).hexdigest(),
            'interpretation': 'Thresholds apply to label counts within each split. Assignment fractions are not comment coverage; labels overlap. No observations are removed from the source report.',
            'splits': count_sensitivity(report, args.minimum_counts),
        }
        text = json.dumps(result, indent=2, allow_nan=False) + '\n'
        with args.out.open('x', encoding='utf-8', newline='\n') as stream:
            created = True
            stream.write(text)
        print(f'Reported {len(args.minimum_counts)} minimum-count choices across {len(result["splits"])} splits.')
        return 0
    except ValueError as error:
        print(f'Input error: {error}', file=sys.stderr)
        return 2
    except OSError as error:
        if created:
            args.out.unlink(missing_ok=True)
        print(f'File error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
