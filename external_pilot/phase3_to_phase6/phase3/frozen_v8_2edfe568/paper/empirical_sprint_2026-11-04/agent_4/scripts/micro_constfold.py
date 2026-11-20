"""Exploratory: which lines emit sys.settrace line events for constant-condition constructs? stdout only. Self-contained toy."""
import sys, json
SRC = '''def f(n):
    if False:
        x = n * 999
    if 0:
        y = 1
    if True:
        z = 2
    while True:
        n += 1
        if n > 2:
            break
    return n
'''
ns = {}; exec(compile(SRC, "toy.py", "exec"), ns)
lines = []
def tr(frame, ev, arg):
    if frame.f_code.co_filename != "toy.py": return None
    if ev == "line": lines.append(frame.f_lineno)
    return tr
sys.settrace(tr); ns["f"](0); sys.settrace(None)
print(json.dumps({"python": ".".join(map(str, sys.version_info[:3])), "line_events_seq": lines}))
