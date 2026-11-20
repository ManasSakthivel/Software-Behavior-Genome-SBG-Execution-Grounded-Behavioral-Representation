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
    g = {}
    if cfg.get("chan"):  # per-run key arrives over a pipe we drain and close here, before any user code is imported
        key = b""
        while chunk := os.read(cfg["chan"]["k"], 4096):
            key += chunk
        os.close(cfg["chan"]["k"])
        g["_SBGV7_CHAN"] = (cfg["chan"]["w"], key)  # the script must pop this into closure state (harness.py does)
    del cfg
    runpy.run_path(sys.argv[0], init_globals=g, run_name="__main__")
else:
    sys.path.insert(0, cfg["path"])
    mod, _, qual = cfg["callable"].partition(":")
    obj = importlib.import_module(mod)
    for part in qual.split("."):
        obj = getattr(obj, part)
    print(json.dumps(obj(*cfg["args"])))
