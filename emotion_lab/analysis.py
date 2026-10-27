"""Bounded parsing and descriptive statistics; no model or emotion inference."""

from collections import Counter
from hashlib import sha256
import math
from pathlib import Path
import re
import stat


class DataError(ValueError):
    """An input violates the documented data contract."""


def read_records(path, label_count, seen, *, max_rows=50_000, expected_sha256=None):
    """Yield label tuples, retaining IDs only to detect duplicate comments."""
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 6_000_000:
        raise DataError(f'{path.name}: expected a regular file within 6 MB')
    rows = 0
    total_bytes = 0
    digest = sha256()
    try:
        with path.open('rb') as source:
            while raw := source.readline(65_537):
                total_bytes += len(raw)
                if total_bytes > 6_000_000:
                    raise DataError(f'{path.name}: input exceeds 6 MB while processing')
                digest.update(raw)
                rows += 1
                if rows > max_rows:
                    raise DataError(f'{path.name}: row limit exceeded')
                if len(raw) > 65_536:
                    raise DataError(f'{path.name}: line size limit exceeded')
                line = raw.decode('utf-8').removesuffix('\n').removesuffix('\r')
                parts = line.split('\t')
                if len(parts) != 3 or '\x00' in line:
                    raise DataError(f'{path.name}, row {rows}: expected three TSV fields')
                text, label_text, comment_id = parts
                if not 0 < len(text) <= 16_384:
                    raise DataError(f'{path.name}, row {rows}: invalid text size')
                if not re.fullmatch(r'[A-Za-z0-9]{1,64}', comment_id):
                    raise DataError(f'{path.name}, row {rows}: invalid comment ID')
                if comment_id in seen:
                    raise DataError(f'{path.name}, row {rows}: duplicate comment ID')
                tokens = label_text.split(',')
                if not 1 <= len(tokens) <= label_count or any(not re.fullmatch(r'\d{1,2}', value, flags=re.ASCII) for value in tokens):
                    raise DataError(f'{path.name}, row {rows}: invalid labels')
                labels = tuple(int(value) for value in tokens)
                if len(set(labels)) != len(labels) or any(value >= label_count for value in labels):
                    raise DataError(f'{path.name}, row {rows}: duplicate or out-of-range label')
                seen.add(comment_id)
                yield labels
    except UnicodeDecodeError as error:
        raise DataError(f'{path.name}: invalid UTF-8') from error
    if not rows:
        raise DataError(f'{path.name}: empty input')
    if expected_sha256 is not None and digest.hexdigest() != expected_sha256:
        raise DataError(f'{path.name}: source changed while processing; hash differs from lock')


def wilson_interval(successes, total):
    """Two-sided 95% Wilson score interval, under a binomial model."""
    if total == 0:
        return None
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    spread = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, center - spread), min(1.0, center + spread)]


def summarize(records, label_count, *, neutral_index):
    counts = [0] * label_count
    pairs = [[0] * label_count for _ in range(label_count)]
    histogram = Counter()
    rows = annotations = multi_label = neutral_mixed = 0
    for labels in records:
        rows += 1
        annotations += len(labels)
        histogram[len(labels)] += 1
        multi_label += len(labels) > 1
        neutral_mixed += neutral_index in labels and len(labels) > 1
        for a in labels:
            counts[a] += 1
            for b in labels:
                pairs[a][b] += 1
    return finish_summary(rows, annotations, multi_label, neutral_mixed, histogram, counts, pairs)


def finish_summary(rows, annotations, multi_label, neutral_mixed, histogram, counts, pairs):
    return {
        'rows': rows,
        'annotations': annotations,
        'multiLabelRows': multi_label,
        'neutralWithOtherRows': neutral_mixed,
        'labelCountHistogram': {str(key): value for key, value in sorted(histogram.items(), key=lambda item: int(item[0]))},
        'counts': counts,
        'rates': [count / rows if rows else None for count in counts],
        'wilson95': [wilson_interval(count, rows) for count in counts],
        'pairCounts': pairs,
    }


def combine(splits, label_count):
    """Pool disjoint split summaries using counts, never averaged rates."""
    histogram = Counter()
    for split in splits:
        histogram.update(split['labelCountHistogram'])
    counts = [sum(split['counts'][i] for split in splits) for i in range(label_count)]
    pairs = [[sum(split['pairCounts'][i][j] for split in splits) for j in range(label_count)] for i in range(label_count)]
    return finish_summary(
        sum(split['rows'] for split in splits), sum(split['annotations'] for split in splits),
        sum(split['multiLabelRows'] for split in splits), sum(split['neutralWithOtherRows'] for split in splits),
        histogram, counts, pairs,
    )
