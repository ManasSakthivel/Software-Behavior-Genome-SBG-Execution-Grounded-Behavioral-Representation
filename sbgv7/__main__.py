"""python -m sbgv7 compare BASE.py VARIANT.py --entry FUNC --inputs inputs.json --config cfg.json --out DIR"""
import argparse, json, os, sys

from .config import ConfigError, load_config, load_inputs
from .runner import Ineligible, compare_versions


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m sbgv7")
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("compare")
    c.add_argument("base"); c.add_argument("variant")
    for a in ("entry", "inputs", "config", "out"): c.add_argument("--" + a, required=True)
    a = ap.parse_args(argv)
    try:
        for p in (a.base, a.variant):
            if not os.path.isfile(p) or not p.endswith(".py"): raise ConfigError(f"not a .py file: {p}")
        if not a.entry.isidentifier(): raise ConfigError(f"--entry must be a top-level function name, got {a.entry!r}")
        if os.path.exists(os.path.join(a.out, "evidence.jsonl")): raise ConfigError(f"{a.out}/evidence.jsonl exists; refusing to overwrite evidence")
        cfg, inputs = load_config(a.config), load_inputs(a.inputs)
        out = compare_versions(a.base, a.variant, a.entry, inputs, cfg, a.out)
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr); return 2
    except Ineligible as e:
        print(str(e), file=sys.stderr); return 3
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
