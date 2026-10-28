"""Export the bundled measured label rates as a table, without source comments."""

import argparse
import csv
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=('train', 'dev', 'test', 'all'), required=True)
    parser.add_argument('--out', type=Path, required=True, help='New CSV file; never overwrite')
    args = parser.parse_args(argv)
    created = False
    try:
        report = json.loads((ROOT / 'web/assets/report.json').read_text(encoding='utf-8'))
        data = report['splits'][args.split]
        with args.out.open('x', encoding='utf-8', newline='') as stream:
            created = True
            writer = csv.writer(stream)
            writer.writerow(('label', 'split', 'comments_with_label', 'total_comments',
                             'rate', 'wilson95_low', 'wilson95_high'))
            for index, label in enumerate(report['labels']):
                interval = data['wilson95'][index] or ('', '')
                writer.writerow((label, args.split, data['counts'][index], data['rows'],
                                 data['rates'][index], *interval))
        print(f'Exported {len(report["labels"])} label rates from the bundled aggregate report.')
        return 0
    except OSError as error:
        if created:
            args.out.unlink(missing_ok=True)
        print(f'File error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
