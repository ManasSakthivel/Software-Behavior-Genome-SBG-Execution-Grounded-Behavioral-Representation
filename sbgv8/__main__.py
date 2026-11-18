"""python -m sbgv8 {compare,verify,forge-test,...}. compare = sbgv7 compare + v8_parts.json sidecar. verify = V7-B verify + sidecar consistency.
Other subcommands are registered by modules of other V8 components exposing cli_register(subparsers) (missing modules are skipped)."""
import argparse, importlib, json, sys

MODULES = ("profile", "perturb", "ers", "calibrate", "baselines", "evaluate", "manifest", "splits", "adjudication")


def _verify(d):
    from sbgv7.verify import Unverifiable, VerifyError, verify
    from .trust import check_sidecar
    try:
        out = verify(d); out["sidecar"] = check_sidecar(d)
        print(json.dumps(out)); return 0 if out["sidecar"]["status"] != "inconsistent" else 1
    except VerifyError as e:
        print(f"VERIFY FAILED: {e}", file=sys.stderr); return 1
    except Unverifiable as e:
        print(f"UNVERIFIABLE: {e}", file=sys.stderr); return 4
    except (OSError, KeyError, ValueError, TypeError) as e:
        print(f"VERIFY FAILED: malformed or missing evidence ({type(e).__name__}: {e})", file=sys.stderr); return 2


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] == "compare":
        import sbgv7.__main__ as M
        from .collect import run_capture
        M.compare_versions = run_capture  # same CLI/exit codes as sbgv7; only the engine call is swapped for the capturing wrapper
        return M.main(argv)
    ap = argparse.ArgumentParser(prog="python -m sbgv8")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("compare", help="as `python -m sbgv7 compare` plus v8_parts.json")
    sp.add_parser("verify", help="V7-B verify + sidecar consistency").add_argument("dir")
    f = sp.add_parser("forge-test", help="run the forgery suite (macOS sandbox; writes a JSON table)")
    f.add_argument("--out", default=None)
    for m in MODULES:
        try: getattr(importlib.import_module(f"sbgv8.{m}"), "cli_register")(sp)
        except (ImportError, AttributeError): pass
    a = ap.parse_args(argv)
    if a.cmd == "verify": return _verify(a.dir)
    if a.cmd == "forge-test":
        from .trust import forgery_suite
        res = forgery_suite()
        if a.out: json.dump(res, open(a.out, "w"), indent=1)
        print(json.dumps(res, indent=1)); return 0
    return a.func(a) if hasattr(a, "func") else 2


if __name__ == "__main__":
    sys.exit(main())
