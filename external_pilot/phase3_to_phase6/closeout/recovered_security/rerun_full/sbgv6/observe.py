"""Python adapter: runs a program under the V5 protocol and keeps the raw traces.

Reuses experiments.final.extraction so V5 and V6 see identical executions.
Java/C adapters: interface only (see Adapter); not implemented.
"""
from __future__ import annotations
import pathlib, sys
from dataclasses import dataclass
from typing import Any, List, Optional, Protocol

REPO = pathlib.Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from experiments.final import extraction as X   # noqa: E402
from sbgv6 import config as C                   # noqa: E402


class Adapter(Protocol):
    """Language adapter contract. Only PythonAdapter is implemented."""
    def observe(self, path: str) -> "Observation": ...


@dataclass
class Observation:
    path: str
    source: str
    ok: bool
    failure_kind: Optional[str]      # None when ok; else a reason code (never silently imputed)
    runs: List[list]                 # runs[r][i] -> ExecutionTrace (from SandboxRunner)
    record: Any                      # V5 ProgramRecord (kept so V5 can be recomputed)


class _Recorder:
    def __init__(self, inner):
        self.inner, self.last = inner, None
    def run(self, *a, **k):
        self.last = self.inner.run(*a, **k)
        return self.last
    def __getattr__(self, n):
        return getattr(self.inner, n)


_rec = _Recorder(X._runner)
X._runner = _rec


class PythonAdapter:
    def __init__(self, protocol: str = C.PROTOCOL):
        self.protocol = protocol

    def observe(self, path: str) -> Observation:
        src = pathlib.Path(path).read_text()
        _rec.last = None
        record = X.extract_program(path, {}, self.protocol)
        runs = list(_rec.last.traces) if (record.ok and _rec.last is not None) else []
        return Observation(path, src, bool(record.ok and runs),
                           None if record.ok and runs else (record.failure_kind or "no_traces"),
                           runs, record)
