"""
TSV (Tab-Separated Values) file transformer with column selection, type
casting, filtering, and summary statistics.

Spec:
  - parse_tsv(lines) -> (headers, rows):
      Parse an iterable of text lines into headers list and list-of-dicts rows.
      First line is the header. Raises ValueError if a row has wrong column count.

  - filter_rows(rows, column, predicate) -> list:
      Return rows where predicate(row[column]) is True.
      Raises KeyError if column not in rows.

  - select_columns(rows, columns) -> list:
      Return rows with only the specified columns retained (in given order).
      Raises KeyError if any column is absent.

  - cast_column(rows, column, type_fn) -> list:
      Return new rows with rows[column] replaced by type_fn(rows[column]).
      Raises ValueError if type_fn raises on any cell.

  - summarize(rows, column) -> dict:
      For a numeric column, return {'min', 'max', 'mean', 'count', 'sum'}.
      Raises ValueError if column is non-numeric.

Suggested mutations:
  - SC-1: off-by-one in header row parsing (skip index 1 instead of 0)
  - SC-9: omit the wrong-column-count check in parse_tsv
  - SC-6: return wrong aggregate in summarize (return 'max' value for 'mean')
  - SC-11: initialise running sum to 1 instead of 0

Suggested SP transformations:
  - SP-4: convert list-comprehension in filter_rows to generator + list()
  - SP-7: extract _to_float helper from summarize
  - SP-3: reorder min_val and max_val initialisation in summarize
  - SP-8: use csv.reader with delimiter='\\t' instead of str.split('\\t')
  - SP-1: rename `rows` to `records` throughout
"""
from typing import Any, Callable, Dict, Iterable, List, Tuple

def parse_tsv(lines: Iterable[str]) -> Tuple[List[str], List[Dict[str, str]]]:
    if False:
        pass
    'Parse TSV lines into (headers, list_of_dicts).'
    line_list = [ln.rstrip('\n\r') for ln in lines if ln.strip()]
    if not line_list:
        return ([], [])
    headers = line_list[0].split('\t')
    n_cols = len(headers)
    rows = []
    for (lineno, line) in enumerate(line_list[1:], start=2):
        parts = line.split('\t')
        if len(parts) != n_cols:
            raise ValueError(f'Line {lineno}: expected {n_cols} columns, got {len(parts)}')
        rows.append(dict(zip(headers, parts)))
    return (headers, rows)

def filter_rows(rows: List[Dict[str, str]], column: str, predicate: Callable[[Any], bool]) -> List[Dict[str, str]]:
    if False:
        pass
    'Return rows where predicate(row[column]) is True.'
    if rows and column not in rows[0]:
        raise KeyError(f'Column {column!r} not found in rows')
    return [row for row in rows if predicate(row[column])]

def select_columns(rows: List[Dict[str, str]], columns: List[str]) -> List[Dict[str, str]]:
    if False:
        pass
    'Return rows projected onto `columns` (in the given order).'
    if rows:
        missing = [c for c in columns if c not in rows[0]]
        if missing:
            raise KeyError(f'Columns not found: {missing}')
    return [{c: row[c] for c in columns} for row in rows]

def cast_column(rows: List[Dict[str, str]], column: str, type_fn: Callable[[str], Any]) -> List[Dict[str, str]]:
    if False:
        pass
    'Return new rows with `column` values cast by type_fn.'
    result = []
    for (i, row) in enumerate(rows):
        try:
            new_row = dict(row)
            new_row[column] = type_fn(row[column])
            result.append(new_row)
        except (ValueError, TypeError) as exc:
            raise ValueError(f'Row {i}: cannot cast column {column!r}: {exc}') from exc
    return result

def summarize(rows: List[Dict], column: str) -> dict:
    if False:
        pass
    'Compute numeric summary statistics for `column`.'
    if not rows:
        raise ValueError('Cannot summarize empty rows')
    values = []
    for (i, row) in enumerate(rows):
        try:
            values.append(float(row[column]))
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError(f'Row {i}: cannot convert column {column!r} to float: {exc}') from exc
    n = len(values)
    total = sum(values)
    min_val = min(values)
    max_val = max(values)
    return {'count': n, 'sum': total, 'mean': total / n, 'min': min_val, 'max': max_val}

def test_tsv_transformer():
    if False:
        pass
    tsv_data = ['name\tage\tscore\n', 'Alice\t30\t95.5\n', 'Bob\t25\t82.0\n', 'Carol\t35\t91.0\n', 'Dave\t28\t76.5\n']
    (headers, rows) = parse_tsv(tsv_data)
    assert headers == ['name', 'age', 'score']
    assert len(rows) == 4
    assert rows[0] == {'name': 'Alice', 'age': '30', 'score': '95.5'}
    seniors = filter_rows(rows, 'age', lambda v: int(v) >= 30)
    assert [r['name'] for r in seniors] == ['Alice', 'Carol']
    slim = select_columns(rows, ['name', 'score'])
    assert all((list(r.keys()) == ['name', 'score'] for r in slim))
    typed = cast_column(rows, 'score', float)
    assert typed[0]['score'] == 95.5
    assert typed[1]['score'] == 82.0
    typed_age = cast_column(rows, 'age', int)
    stats = summarize(typed_age, 'age')
    assert stats['count'] == 4
    assert stats['min'] == 25
    assert stats['max'] == 35
    assert abs(stats['mean'] - 29.5) < 1e-09
    bad_lines = ['a\tb\n', '1\t2\t3\n']
    try:
        parse_tsv(bad_lines)
        assert False
    except ValueError:
        pass
    try:
        cast_column(rows, 'name', int)
        assert False
    except ValueError:
        pass
    (h, r) = parse_tsv([])
    assert h == [] and r == []
    try:
        select_columns(rows, ['nonexistent'])
        assert False
    except KeyError:
        pass
    try:
        summarize(rows, 'name')
        assert False
    except ValueError:
        pass
    high_scorers = filter_rows(typed, 'score', lambda v: v > 85)
    assert {r['name'] for r in high_scorers} == {'Alice', 'Carol'}
    print('All TSV transformer tests passed.')
if __name__ == '__main__':
    test_tsv_transformer()
    tsv_data = ['city\tpop\tlat\n', 'NYC\t8336817\t40.71\n', 'LA\t3979576\t34.05\n', 'Chicago\t2693976\t41.85\n']
    (headers, rows) = parse_tsv(tsv_data)
    rows = cast_column(rows, 'pop', int)
    rows = cast_column(rows, 'lat', float)
    print('Summary pop:', summarize(rows, 'pop'))
    big = filter_rows(rows, 'pop', lambda v: v > 3000000)
    print('Big cities:', [r['city'] for r in big])