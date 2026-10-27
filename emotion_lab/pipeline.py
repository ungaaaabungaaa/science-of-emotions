"""Fetch and verify pinned source files; publish only aggregate annotations."""

from hashlib import sha256
import json
from pathlib import Path
import re
import stat
from urllib.request import build_opener, HTTPRedirectHandler

from . import __version__
from .analysis import DataError, read_records, summarize, combine

FILES = ('emotions.txt', 'train.tsv', 'dev.tsv', 'test.tsv')
ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 6_000_000


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def source_manifest():
    manifest = json.loads((ROOT / 'data-source.json').read_text(encoding='utf-8'))
    revision = manifest.get('revision', '')
    if not re.fullmatch(r'[0-9a-f]{40}', revision) or set(manifest.get('files', {})) != set(FILES):
        raise DataError('Invalid source manifest')
    for name, details in manifest['files'].items():
        expected = f'https://raw.githubusercontent.com/google-research/google-research/{revision}/goemotions/data/{name}'
        if details.get('url') != expected or not re.fullmatch(r'[0-9a-f]{64}', details.get('sha256', '')):
            raise DataError('Invalid source manifest URL or hash')
        if type(details.get('bytes')) is not int or not 0 < details['bytes'] <= MAX_BYTES:
            raise DataError('Invalid source manifest size')
    return manifest


def verify_file(path, details):
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise DataError(f'{path.name}: expected a regular file')
    if info.st_size > MAX_BYTES:
        raise DataError(f'{path.name}: file exceeds 6 MB')
    with path.open('rb') as source:
        data = source.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise DataError(f'{path.name}: file exceeds 6 MB')
    if len(data) != details['bytes'] or sha256(data).hexdigest() != details['sha256']:
        raise DataError(f'{path.name}: source size/hash does not match the lock')
    return data


def fetch_file(path, details):
    path = Path(path)
    if path.exists() or path.is_symlink():
        verify_file(path, details)
        return 'reused'
    request = build_opener(NoRedirect())
    with request.open(details['url'], timeout=30) as response:
        if response.status != 200:
            raise OSError(f'{path.name}: source returned HTTP {response.status}')
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise DataError(f'{path.name}: download exceeds 6 MB')
    if len(data) != details['bytes'] or sha256(data).hexdigest() != details['sha256']:
        raise DataError(f'{path.name}: download size/hash does not match the lock')
    created = False
    try:
        with path.open('xb') as target:
            created = True
            target.write(data)
    except OSError:
        if created:
            path.unlink(missing_ok=True)
        raise
    return 'downloaded'


def build_report(data_dir, manifest):
    data_dir = Path(data_dir)
    # Complete source verification before analyzing any split.
    label_data = None
    for name in FILES:
        data = verify_file(data_dir / name, manifest['files'][name])
        if name == 'emotions.txt':
            label_data = data
    labels = label_data.decode('utf-8').splitlines()
    if not 1 <= len(labels) <= 28 or len(set(labels)) != len(labels) or 'neutral' not in labels or any(not re.fullmatch(r'[a-z_]{1,40}', label) for label in labels):
        raise DataError('Invalid emotion label list')
    seen = set()
    splits = {}
    for split in ('train', 'dev', 'test'):
        records = read_records(data_dir / f'{split}.tsv', len(labels), seen, expected_sha256=manifest['files'][f'{split}.tsv']['sha256'])
        splits[split] = summarize(records, len(labels), neutral_index=labels.index('neutral'))
    splits['all'] = combine(list(splits.values()), len(labels))
    return {'schemaVersion': 1, 'analysisVersion': __version__, 'source': manifest,
            'labels': labels, 'splits': splits}


def report_text(report):
    return json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False) + '\n'
