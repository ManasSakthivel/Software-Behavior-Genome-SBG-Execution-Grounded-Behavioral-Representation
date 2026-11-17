"""Child bootstrap: apply rlimits (fail loudly), then run a script or callable. argv[1] = JSON config."""
import json, os, runpy, sys, resource, importlib

cfg = json.loads(sys.argv[1])
for name, val in cfg["limits"].items():
    try:
        resource.setrlimit(getattr(resource, name), (val, val))
    except (ValueError, OSError) as e:
        sys.stderr.write(f"SBGV7_LIMIT_FAIL {name} {e}\n"); sys.stderr.flush(); os._exit(97)
if cfg.get("script"):
    sys.argv = [cfg["script"], *cfg["args"]]
    runpy.run_path(cfg["script"], run_name="__main__")
else:
    sys.path.insert(0, cfg["path"])
    mod, _, qual = cfg["callable"].partition(":")
    obj = importlib.import_module(mod)
    for part in qual.split("."):
        obj = getattr(obj, part)
    print(json.dumps(obj(*cfg["args"])))
