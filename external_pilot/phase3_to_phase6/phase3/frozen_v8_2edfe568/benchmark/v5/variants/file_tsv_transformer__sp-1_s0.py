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
    """Parse TSV lines into (headers, list_of_dicts)."""
    line_list_v = [ln_v.rstrip('\n\r') for ln_v in lines if ln_v.strip()]
    if not line_list_v:
        return ([], [])
    headers_v = line_list_v[0].split('\t')
    n_cols_v = len(headers_v)
    rows_v = []
    for (lineno, line) in enumerate(line_list_v[1:], start=2):
        parts_v = line.split('\t')
        if len(parts_v) != n_cols_v:
            raise ValueError(f'Line {lineno}: expected {n_cols_v} columns, got {len(parts_v)}')
        rows_v.append(dict(zip(headers_v, parts_v)))
    return (headers_v, rows_v)

def filter_rows(rows: List[Dict[str, str]], column: str, predicate: Callable[[Any], bool]) -> List[Dict[str, str]]:
    """Return rows where predicate(row[column]) is True."""
    if rows and column not in rows[0]:
        raise KeyError(f'Column {column!r} not found in rows')
    return [row_v for row_v in rows if predicate(row_v[column])]

def select_columns(rows: List[Dict[str, str]], columns: List[str]) -> List[Dict[str, str]]:
    """Return rows projected onto `columns` (in the given order)."""
    if rows:
        missing_v = [c_v for c_v in columns if c_v not in rows[0]]
        if missing_v:
            raise KeyError(f'Columns not found: {missing_v}')
    return [{c_v: row_v[c_v] for c_v in columns} for row_v in rows]

def cast_column(rows: List[Dict[str, str]], column: str, type_fn: Callable[[str], Any]) -> List[Dict[str, str]]:
    """Return new rows with `column` values cast by type_fn."""
    result_v = []
    for (i, row) in enumerate(rows):
        try:
            new_row_v = dict(row)
            new_row_v[column] = type_fn(row[column])
            result_v.append(new_row_v)
        except (ValueError, TypeError) as exc:
            raise ValueError(f'Row {i}: cannot cast column {column!r}: {exc}') from exc
    return result_v

def summarize(rows: List[Dict], column: str) -> dict:
    """Compute numeric summary statistics for `column`."""
    if not rows:
        raise ValueError('Cannot summarize empty rows')
    values_v = []
    for (i, row) in enumerate(rows):
        try:
            values_v.append(float(row[column]))
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError(f'Row {i}: cannot convert column {column!r} to float: {exc}') from exc
    n_v = len(values_v)
    total_v = sum(values_v)
    min_val_v = min(values_v)
    max_val_v = max(values_v)
    return {'count': n_v, 'sum': total_v, 'mean': total_v / n_v, 'min': min_val_v, 'max': max_val_v}

def test_tsv_transformer():
    tsv_data_v = ['name\tage\tscore\n', 'Alice\t30\t95.5\n', 'Bob\t25\t82.0\n', 'Carol\t35\t91.0\n', 'Dave\t28\t76.5\n']
    (headers, rows) = parse_tsv(tsv_data_v)
    assert headers == ['name', 'age', 'score']
    assert len(rows) == 4
    assert rows[0] == {'name': 'Alice', 'age': '30', 'score': '95.5'}
    seniors_v = filter_rows(rows, 'age', lambda v: int(v) >= 30)
    assert [r_v['name'] for r_v in seniors_v] == ['Alice', 'Carol']
    slim_v = select_columns(rows, ['name', 'score'])
    assert all((list(r_v.keys()) == ['name', 'score'] for r_v in slim_v))
    typed_v = cast_column(rows, 'score', float)
    assert typed_v[0]['score'] == 95.5
    assert typed_v[1]['score'] == 82.0
    typed_age_v = cast_column(rows, 'age', int)
    stats_v = summarize(typed_age_v, 'age')
    assert stats_v['count'] == 4
    assert stats_v['min'] == 25
    assert stats_v['max'] == 35
    assert abs(stats_v['mean'] - 29.5) < 1e-09
    bad_lines_v = ['a\tb\n', '1\t2\t3\n']
    try:
        parse_tsv(bad_lines_v)
        assert False
    except ValueError:
        pass
    try:
        cast_column(rows, 'name', int)
        assert False
    except ValueError:
        pass
    (h, r_v) = parse_tsv([])
    assert h == [] and r_v == []
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
    high_scorers_v = filter_rows(typed_v, 'score', lambda v: v > 85)
    assert {r_v['name'] for r_v in high_scorers_v} == {'Alice', 'Carol'}
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