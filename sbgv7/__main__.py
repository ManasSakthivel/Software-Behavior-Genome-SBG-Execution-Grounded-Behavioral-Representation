"""python -m sbgv7 compare BASE.py VARIANT.py --entry FUNC --inputs inputs.json --config cfg.json --out DIR
Exit codes (SD-13). compare: 0 a verdict was written (any value: read verdict.json), 1 internal error (one-line message), 2 usage/config/inputs
or output-path (OSError) error, 3 ineligible:identical. verify: 0 verified, 1 mismatch/tamper, 2 unreadable/missing, 4 evidence omitted by size cap."""
import argparse, json, os, sys

from .config import ConfigError, load_config, load_inputs
from .runner import Ineligible, compare_versions


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m sbgv7")
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("compare")
    c.add_argument("base"); c.add_argument("variant")
    for a in ("entry", "inputs", "config", "out"): c.add_argument("--" + a, required=True)
    v = sp.add_parser("verify"); v.add_argument("dir")
    a = ap.parse_args(argv)
    if a.cmd == "verify":  # exit 0 recomputed verdict equals recorded, 1 mismatch/tamper, 2 unreadable, 4 evidence omitted by size cap
        from .verify import Unverifiable, VerifyError, verify
        try:
            print(json.dumps(verify(a.dir))); return 0
        except VerifyError as e:
            print(f"VERIFY FAILED: {e}", file=sys.stderr); return 1
        except Unverifiable as e:
            print(f"UNVERIFIABLE: {e}", file=sys.stderr); return 4
        except (OSError, KeyError, ValueError, TypeError) as e:
            print(f"VERIFY FAILED: malformed or missing evidence ({type(e).__name__}: {e})", file=sys.stderr); return 2
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
    except OSError as e:  # output directory / log creation (existing file, permissions, FileExistsError from the no-overwrite policy)
        print(f"error: cannot write evidence to {a.out}: {type(e).__name__}: {e}".splitlines()[0], file=sys.stderr); return 2
    except Exception as e:  # noqa: BLE001  internal error: one line, no traceback
        print(f"internal error: {type(e).__name__}: {e}".splitlines()[0], file=sys.stderr); return 1
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
