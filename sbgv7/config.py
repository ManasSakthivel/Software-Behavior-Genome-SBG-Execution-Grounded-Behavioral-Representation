"""Strict config/inputs validation. Unknown keys, wrong types and out-of-range values raise ConfigError."""
import copy, json

CHANNELS = ("ret", "exc", "side:stdout", "side:file", "side:argmut", "side:global")


class ConfigError(ValueError):
    pass


def _num(lo=None, hi=None, integer=False, lo_open=False):
    def chk(v, path):
        ok = (type(v) is int) if integer else (type(v) in (int, float))
        if not ok: raise ConfigError(f"{path}: expected {'int' if integer else 'number'}, got {v!r}")
        if v != v or (lo is not None and (v <= lo if lo_open else v < lo)) or (hi is not None and v > hi):
            raise ConfigError(f"{path}: {v!r} out of range")
    return chk


def _bool(v, path):
    if type(v) is not bool: raise ConfigError(f"{path}: expected bool, got {v!r}")


def _enum(*opts):
    def chk(v, path):
        if v not in opts: raise ConfigError(f"{path}: must be one of {opts}, got {v!r}")
    return chk


def _channels(v, path):
    if not isinstance(v, list) or not v or any(c not in CHANNELS for c in v) or len(set(v)) != len(v):
        raise ConfigError(f"{path}: must be a non-empty duplicate-free list drawn from {CHANNELS}")


def _s3(v, path):
    _bool(v, path)
    if v: raise ConfigError(f"{path}: S3 is not implemented in this build; true is refused rather than ignored")


# (default, validator) leaves; dicts are sections
SCHEMA = {
    "harness": {"c_obs": (list(CHANNELS), _channels), "float_tol": {"rel": (0.0, _num(0)), "abs": (0.0, _num(0))},
                "ordered_mapping": (False, _bool), "exc_message": ("exact_normalised", _enum("exact_normalised", "ignore")),
                "api_break_probe": (True, _bool)},
    "repeat": {"r_det": (3, _num(1, integer=True)), "r_replay": (5, _num(1, integer=True)), "k_alt": (3, _num(0, integer=True))},
    "suff": {"s2_branch_floor": (0.80, _num(0, 1)), "s3_enabled": (False, _s3)},
    "budget": {"cpu_seconds": (60, _num(0, lo_open=True)),
               "per_run": {"cpu_s": (10, _num(0, integer=True, lo_open=True)), "wall_s": (20, _num(0, lo_open=True)),
                           "rss_mib": (2048, _num(16, integer=True))}},
}


def _fill(schema, given, path):
    if not isinstance(given, dict): raise ConfigError(f"{path or 'config'}: expected object, got {type(given).__name__}")
    bad = set(given) - set(schema)
    if bad: raise ConfigError(f"{path or 'config'}: unknown key(s) {sorted(bad)}")
    out = {}
    for k, spec in schema.items():
        p = f"{path}.{k}" if path else k
        if isinstance(spec, dict):
            out[k] = _fill(spec, given.get(k, {}), p)
        elif k in given:
            spec[1](given[k], p); out[k] = copy.deepcopy(given[k])
        else:
            out[k] = copy.deepcopy(spec[0])
    return out


def load_config(path):
    try:
        raw = json.load(open(path))
    except (OSError, ValueError) as e:
        raise ConfigError(f"cannot read config {path}: {e}")
    return _fill(SCHEMA, raw, "")


def load_inputs(path):
    """inputs.json: list of {"args": [...], "kwargs": {...}?, "id": str?}. JSON types only (no tuples/sets/objects)."""
    try:
        raw = json.load(open(path))
    except (OSError, ValueError) as e:
        raise ConfigError(f"cannot read inputs {path}: {e}")
    if not isinstance(raw, list): raise ConfigError("inputs: expected a JSON list")
    out, seen = [], set()
    for i, it in enumerate(raw):
        if not isinstance(it, dict) or not set(it) <= {"args", "kwargs", "id"} or not isinstance(it.get("args"), list):
            raise ConfigError(f"inputs[{i}]: expected object with list 'args' and optional 'kwargs','id'")
        if not isinstance(it.get("kwargs", {}), dict): raise ConfigError(f"inputs[{i}].kwargs: expected object")
        iid = it.get("id", f"i{i}")
        if not isinstance(iid, str) or not iid or iid in seen: raise ConfigError(f"inputs[{i}].id: must be a unique non-empty string")
        seen.add(iid); out.append({"id": iid, "args": it["args"], "kwargs": it.get("kwargs", {})})
    return out
