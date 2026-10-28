"""Descriptive sensitivity to explicit minimum label counts; never filter source data."""


def count_sensitivity(report, minimum_counts):
    if (not isinstance(minimum_counts, (list, tuple)) or not 1 <= len(minimum_counts) <= 16
            or any(type(value) is not int or not 0 <= value <= 1_000_000 for value in minimum_counts)
            or len(set(minimum_counts)) != len(minimum_counts)):
        raise ValueError('Supply one to sixteen unique integer minimum counts from 0 to 1000000')
    results = {}
    for split, data in report['splits'].items():
        thresholds = []
        for minimum in minimum_counts:
            kept = [index for index, count in enumerate(data['counts']) if count >= minimum]
            assignments = sum(data['counts'][index] for index in kept)
            thresholds.append({
                'minimum_count': minimum,
                'retained_label_count': len(kept),
                'omitted_labels': [label for label, count in zip(report['labels'], data['counts'], strict=True) if count < minimum],
                'retained_label_assignments': assignments,
                'retained_assignment_fraction': assignments / data['annotations'] if data['annotations'] else None,
            })
        results[split] = {'total_comments': data['rows'], 'total_label_assignments': data['annotations'],
                          'thresholds': thresholds}
    return results
