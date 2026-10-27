import argparse
import sys
from pathlib import Path

from .analysis import DataError
from .pipeline import source_manifest, fetch_file, build_report, report_text, FILES


def main(argv=None):
    parser = argparse.ArgumentParser(description='Inspect published GoEmotions annotations without displaying comments.')
    commands = parser.add_subparsers(dest='command', required=True)
    fetch = commands.add_parser('fetch', help='Download the four pinned official source files')
    fetch.add_argument('--data-dir', type=Path, required=True)
    analyze = commands.add_parser('analyze', help='Verify source hashes and produce deterministic aggregate JSON')
    analyze.add_argument('--data-dir', type=Path, required=True)
    output = analyze.add_mutually_exclusive_group(required=True)
    output.add_argument('--out', type=Path, help='Write a new report; never overwrite')
    output.add_argument('--check', type=Path, help='Verify an existing report matches the source run')
    args = parser.parse_args(argv)
    try:
        manifest = source_manifest()
        if args.command == 'fetch':
            args.data_dir.mkdir(parents=True, exist_ok=True)
            for name in FILES:
                status = fetch_file(args.data_dir / name, manifest['files'][name])
                print(f'{name}: {status}, SHA-256 verified')
            return 0
        report = build_report(args.data_dir, manifest)
        text = report_text(report)
        if args.check:
            if args.check.stat().st_size > 1_000_000 or args.check.read_text(encoding='utf-8') != text:
                raise DataError('Existing report differs from the verified source run')
            print('Report matches the verified source run.')
        else:
            created = False
            try:
                with args.out.open('x', encoding='utf-8', newline='\n') as target:
                    created = True
                    target.write(text)
            except OSError:
                if created:
                    args.out.unlink(missing_ok=True)
                raise
            print(f'Wrote aggregate report: {report["splits"]["all"]["rows"]:,} distinct comments, no raw text.')
        return 0
    except (DataError, UnicodeError) as error:
        print(f'Input error: {error}', file=sys.stderr)
        return 2
    except OSError as error:
        print(f'File or network error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
