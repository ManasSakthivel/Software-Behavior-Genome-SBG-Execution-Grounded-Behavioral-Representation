"""
Structured exception hierarchy with custom exception types, context chaining,
and a validation pipeline that reports all errors (not just the first).

Spec:
  - ValidationError, ParseError, RangeError, TypeError_ — custom exceptions
    organised in a hierarchy. All are subclasses of AppError.

  - validate_record(record) -> dict:
      Validate a dict record with fields: 'name' (str, non-empty),
      'age' (int, 0-100), 'score' (float, 0.0-1.0).
      Returns the record if valid.
      Raises ValidationError with a list of all field errors if any fail.

  - parse_record(raw) -> dict:
      Parse a dict of string values into typed fields.
      Raises ParseError (chaining ValueError) if a field cannot be parsed.

  - safe_divide(a, b) -> float:
      Return a/b. Raises RangeError if b==0 (wrapping ZeroDivisionError).

  - run_pipeline(raw_records) -> (list[dict], list[AppError]):
      Process a list of raw records through parse + validate.
      Returns (successful_records, errors_list).
      Never raises; errors are accumulated.

Suggested mutations:
  - SC-10: swallow ValidationError in run_pipeline (empty except block)
  - SC-7: remove the b==0 guard in safe_divide (missing guard)
  - SC-3: negate the age range check (accept ages outside 0-100)
  - SC-11: initialise errors list to [None] instead of []

Suggested SP transformations:
  - SP-11: restructure parse_record try/except to use explicit ValueError chain
  - SP-7: extract _validate_age and _validate_score as helpers
  - SP-3: reorder name/age/score validation checks (no data dependency)
  - SP-4: replace list-comprehension error collection with for-loop
  - SP-1: rename AppError to BaseAppError throughout
"""
from typing import Any, Dict, List, Tuple

class AppError(Exception):
    """Base class for all application errors."""
    pass

class ValidationError(AppError):
    """One or more fields failed validation."""

    def __init__(self, field_errors: List[str]):
        self.field_errors = field_errors
        super().__init__(f"Validation failed: {'; '.join(field_errors)}")

class ParseError(AppError):
    """A field could not be parsed to the expected type."""
    pass

class RangeError(AppError):
    """A numeric value is outside its legal range."""
    pass

class TypeError_(AppError):
    """Unexpected type for a field (different from built-in TypeError)."""
    pass

def validate_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a typed record. Raises ValidationError with all field errors.
    """
    errors_v = []
    name_v = record.get('name')
    if not isinstance(name_v, str):
        errors_v.append('name: must be a string')
    elif not name_v.strip():
        errors_v.append('name: must be non-empty')
    age_v = record.get('age')
    if not isinstance(age_v, int) or isinstance(age_v, bool):
        errors_v.append('age: must be an integer')
    elif not 0 <= age_v <= 100:
        errors_v.append(f'age: must be in [0, 100], got {age_v}')
    score_v = record.get('score')
    if not isinstance(score_v, (int, float)) or isinstance(score_v, bool):
        errors_v.append('score: must be a float')
    elif not 0.0 <= score_v <= 1.0:
        errors_v.append(f'score: must be in [0.0, 1.0], got {score_v}')
    if errors_v:
        raise ValidationError(errors_v)
    return record

def parse_record(raw: Dict[str, str]) -> Dict[str, Any]:
    """Parse a dict of string fields into typed fields."""
    try:
        name_v = str(raw.get('name', ''))
        age_v = int(raw['age'])
        score_v = float(raw['score'])
    except (KeyError, ValueError) as exc:
        raise ParseError(f'Cannot parse record: {exc}') from exc
    return {'name': name_v, 'age': age_v, 'score': score_v}

def safe_divide(a: float, b: float) -> float:
    """Return a/b. Raises RangeError if b==0."""
    if b == 0:
        raise RangeError('Division by zero') from ZeroDivisionError()
    return a / b

def run_pipeline(raw_records: List[Dict[str, str]]) -> Tuple[List[Dict[str, Any]], List[AppError]]:
    """
    Parse and validate a list of raw string-dict records.
    Returns (successful_records, accumulated_errors).
    """
    successes_v: List[Dict[str, Any]] = []
    errors_v: List[AppError] = []
    for raw_v in raw_records:
        try:
            typed_v = parse_record(raw_v)
            valid_v = validate_record(typed_v)
            successes_v.append(valid_v)
        except AppError as exc:
            errors_v.append(exc)
    return (successes_v, errors_v)

def test_exception_hierarchy():
    rec_v = validate_record({'name': 'Alice', 'age': 30, 'score': 0.95})
    assert rec_v['name'] == 'Alice'
    try:
        validate_record({'name': '', 'age': 150, 'score': -0.1})
        assert False
    except ValidationError as e:
        assert len(e.field_errors) == 3
    try:
        validate_record({'name': 'Bob', 'age': -1, 'score': 0.5})
        assert False
    except ValidationError as e:
        assert len(e.field_errors) == 1
        assert 'age' in e.field_errors[0]
    parsed_v = parse_record({'name': 'Carol', 'age': '25', 'score': '0.8'})
    assert parsed_v['age'] == 25
    assert abs(parsed_v['score'] - 0.8) < 1e-09
    try:
        parse_record({'name': 'X', 'age': 'notanint', 'score': '0.5'})
        assert False
    except ParseError:
        pass
    try:
        parse_record({'name': 'X', 'age': 'bad', 'score': '0.1'})
    except ParseError as e:
        assert e.__cause__ is not None
    assert abs(safe_divide(10, 3) - 10 / 3) < 1e-09
    try:
        safe_divide(5.0, 0)
        assert False
    except RangeError:
        pass
    raw_data_v = [{'name': 'Alice', 'age': '30', 'score': '0.9'}, {'name': '', 'age': '25', 'score': '0.5'}, {'name': 'Bob', 'age': 'abc', 'score': '0.7'}, {'name': 'Carol', 'age': '28', 'score': '0.8'}]
    (ok, errs) = run_pipeline(raw_data_v)
    assert len(ok) == 2
    assert len(errs) == 2
    (ok2, errs2) = run_pipeline([{'name': 'X', 'age': '20', 'score': '0.5'}])
    assert len(ok2) == 1 and len(errs2) == 0
    (ok3, errs3) = run_pipeline([])
    assert ok3 == [] and errs3 == []
    try:
        validate_record({'name': 42, 'age': 25, 'score': 0.5})
    except ValidationError as e:
        assert isinstance(e, AppError)
    print('All exception hierarchy tests passed.')
if __name__ == '__main__':
    test_exception_hierarchy()
    raw = [{'name': 'Alice', 'age': '30', 'score': '0.9'}, {'name': '', 'age': '200', 'score': '1.5'}]
    (ok, errs) = run_pipeline(raw)
    print('OK:', ok)
    print('Errors:', [str(e) for e in errs])