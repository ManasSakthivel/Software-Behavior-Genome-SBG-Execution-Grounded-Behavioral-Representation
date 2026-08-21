"""
In-memory CSV data aggregator with GROUP BY and aggregate functions.

Spec: Given CSV data as a string (with header row), provides SQL-like
aggregation operations:
  - load_csv(text) → DataFrame (dict[column_name, list_of_values])
  - group_by(df, key_col, agg_col, agg_func) → dict[key, result]
    agg_func: 'sum' | 'count' | 'mean' | 'min' | 'max'
  - filter_rows(df, col, predicate) → new DataFrame
  - sort_by(df, col, reverse=False) → new DataFrame
  - column_stats(df, col) → dict with min/max/mean/count/sum
  - to_csv(df) → string (round-trip serialization)

DataFrame: {'col_name': [val, val, ...], ...} — all lists same length.
Numeric detection: values parseable as float become float; others stay str.
Raises DataError on missing columns, type mismatches, or empty data.
"""
import csv
import io
from typing import Any, Callable, Dict, List

class DataError(Exception):
    pass
DataFrame = Dict[str, List[Any]]

def _coerce(val: str) -> Any:
    """Coerce string to float if possible, else keep as str."""
    try:
        return float(val)
    except ValueError:
        return val

def load_csv(text: str) -> DataFrame:
    """Parse CSV text (first row = header) into a DataFrame dict."""
    reader = csv.reader(io.StringIO(text.strip()))
    rows = list(reader)
    if not rows:
        raise DataError('Empty CSV input')
    headers = rows[0]
    if not headers:
        raise DataError('CSV has no headers')
    df: DataFrame = {h: [] for h in headers}
    for (rownum, row) in enumerate(rows[1:], start=2):
        if len(row) != len(headers):
            raise DataError(f'Row {rownum} has {len(row)} columns, expected {len(headers)}')
        for (h, val) in zip(headers, row):
            df[h].append(_coerce(val.strip()))
    return df

def filter_rows(df: DataFrame, col: str, predicate: Callable[[Any], bool]) -> DataFrame:
    """Return a new DataFrame with rows where predicate(df[col][i]) is True."""
    if col not in df:
        raise DataError(f'Column {col!r} not found')
    indices = [i for (i, v) in enumerate(df[col]) if predicate(v)]
    return {c: [df[c][i] for i in indices] for c in df}

def sort_by(df: DataFrame, col: str, reverse: bool=False) -> DataFrame:
    """Return a new DataFrame sorted by the given column."""
    if col not in df:
        raise DataError(f'Column {col!r} not found')
    n = len(df[col])
    order = sorted(range(n), key=lambda i: df[col][i], reverse=reverse)
    return {c: [df[c][i] for i in order] for c in df}

def group_by(df: DataFrame, key_col: str, agg_col: str, agg_func: str) -> dict:
    """
    Group by key_col and aggregate agg_col.
    agg_func: 'sum' | 'count' | 'mean' | 'min' | 'max'
    Returns dict {key: aggregated_value}.
    """
    if key_col not in df:
        raise DataError(f'Key column {key_col!r} not found')
    if agg_col not in df and agg_func != 'count':
        raise DataError(f'Aggregate column {agg_col!r} not found')
    if agg_func not in ('sum', 'count', 'mean', 'min', 'max'):
        raise DataError(f'Unknown agg_func {agg_func!r}')
    groups: Dict[Any, List] = {}
    for (i, key) in enumerate(df[key_col]):
        val = df[agg_col][i] if agg_func != 'count' else 1
        groups.setdefault(key, []).append(val)
    result = {}
    for (key, vals) in groups.items():
        if agg_func == 'sum':
            result[key] = sum(vals)
        elif agg_func == 'count':
            result[key] = len(vals)
        elif agg_func == 'mean':
            result[key] = sum(vals) / len(vals)
        elif agg_func == 'min':
            result[key] = min(vals)
        elif agg_func == 'max':
            result[key] = max(vals)
    return result

def column_stats(df: DataFrame, col: str) -> dict:
    """Return descriptive stats for a numeric column."""
    if col not in df:
        raise DataError(f'Column {col!r} not found')
    vals = df[col]
    if not vals:
        raise DataError(f'Column {col!r} is empty')
    numeric = [v for v in vals if isinstance(v, (int, float))]
    if not numeric:
        raise DataError(f'Column {col!r} has no numeric values')
    return {'count': len(numeric), 'sum': sum(numeric), 'mean': sum(numeric) / len(numeric), 'min': min(numeric), 'max': max(numeric)}

def to_csv(df: DataFrame) -> str:
    """Serialize DataFrame back to CSV string."""
    if not df:
        return ''
    headers = list(df.keys())
    n = len(next(iter(df.values())))
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(headers)
    for i in range(n):
        writer.writerow([df[h][i] for h in headers])
    return out.getvalue()
SAMPLE_CSV = 'name,department,salary\nAlice,Engineering,95000\nBob,Marketing,72000\nCharlie,Engineering,88000\nDiana,Marketing,68000\nEve,Engineering,105000\n'

def test_csv_aggregator():
    df = load_csv(SAMPLE_CSV)
    assert set(df.keys()) == {'name', 'department', 'salary'}
    assert len(df['name']) == 5
    assert isinstance(df['salary'][0], float)
    assert df['salary'][0] == 95000.0
    total_by_dept = group_by(df, 'department', 'salary', 'sum')
    assert abs(total_by_dept['Engineering'] - 288000.0) < 1e-06
    assert abs(total_by_dept['Marketing'] - 140000.0) < 1e-06
    count_by_dept = group_by(df, 'department', 'name', 'count')
    assert count_by_dept['Engineering'] == 3
    assert count_by_dept['Marketing'] == 2
    mean_salary = group_by(df, 'department', 'salary', 'mean')
    assert abs(mean_salary['Engineering'] - 96000.0) < 1e-06
    eng_only = filter_rows(df, 'department', lambda v: v == 'Engineering')
    assert len(eng_only['name']) == 3
    sorted_df = sort_by(df, 'salary', reverse=True)
    assert sorted_df['name'][0] == 'Eve'
    stats = column_stats(df, 'salary')
    assert stats['count'] == 5
    assert stats['min'] == 68000.0
    assert stats['max'] == 105000.0
    csv_out = to_csv(df)
    df2 = load_csv(csv_out)
    assert df2['salary'] == df['salary']
    try:
        group_by(df, 'nonexistent', 'salary', 'sum')
        assert False
    except DataError:
        pass
    print('All csv_aggregator tests passed.')
if not __name__ == '__main__':
    test_csv_aggregator()
    df = load_csv(SAMPLE_CSV)
    print('Salary by department (mean):', group_by(df, 'department', 'salary', 'mean'))
    print('Stats:', column_stats(df, 'salary'))