# V1 Behavioral Distance Integration Notes

**Location:** `sbg/v2/static_proxy.py`  
**Author:** Agent B — V1 behavioral_distance integration  
**Status:** Implemented

---

## 1. Why Full V1 `behavioral_distance`, Not Token-Overlap

The B08 hybrid (`baselines/v2/b08_hybrid_sbg_v2.py`) previously computed its
"static" signal using token-level Jaccard similarity over the whitespace-split
source text.  This is architecturally wrong for two reasons.

### 1.1 Token overlap is not structural

Token Jaccard answers *"do these two files share the same words?"*  It conflates
variable names, string literals, comments, and control-flow keywords as equally
informative tokens.  A trivial rename of every variable produces near-zero
overlap yet the program is behaviourally identical.  Conversely, two programs
that happen to use the same library names can yield high token overlap despite
completely different behaviour.

### 1.2 The v1 AUROC gap

The v1 full SBG evaluation (B08, `artifacts/B08/`) recorded **AUROC = 0.4237**
with all 8 dimensions active.  Even though this is below random chance (a known
inversion problem the v2 hybrid is designed to fix), it provides a meaningful
*dimensional decomposition* of behavioural difference.  Token overlap provides
no such decomposition and cannot be tuned per-dimension.

Using `behavioral_distance` from `sbg/distance.py` directly preserves the
formal grounding (Definitions 9–20, `docs/research/FORMAL_MODEL.md`) and keeps
the hybrid's static arm on the same theoretical footing as the dynamic arm.

---

## 2. Genome Dimensions Used

All eight dimensions from `DEFAULT_WEIGHTS` in [`sbg/distance.py`](../../sbg/distance.py):

| Key | Weight | Extractor module | Type |
|-----|--------|------------------|------|
| `CONTROL` | 0.20 | `sbg/extraction/static/extractor.py` | Static (AST) |
| `DATA` | 0.15 | `sbg/extraction/static/data_genome.py` | Static (AST) |
| `ERROR` | 0.10 | `sbg/extraction/static/error_genome.py` | Static (AST) |
| `EXECUTION` | 0.10 | `sbg/extraction/dynamic/tracer.py` | Dynamic (trace) |
| `STATE` | 0.15 | `sbg/extraction/dynamic/state_genome.py` | Dynamic (trace) |
| `RESOURCE` | 0.10 | `sbg/extraction/dynamic/resource_genome.py` | Dynamic (trace) |
| `TEMPORAL` | 0.10 | `sbg/extraction/dynamic/temporal_genome.py` | Dynamic (trace) |
| `INTERACTION` | 0.10 | `sbg/extraction/dynamic/interaction_genome.py` | Dynamic (trace) |

`DEFAULT_WEIGHTS` sums to exactly 1.00 and is imported unchanged from
`sbg/distance.py`.  It is **not** re-declared in the proxy.

### Dimension availability

Static dimensions (`CONTROL`, `DATA`, `ERROR`) are always available when the
source file is valid Python.  Dynamic dimensions require a loadable callable
entry point (`main`, `solve`, `run`, `compute`, or the single top-level
function).  `behavioral_distance` re-normalises weights over whichever
dimensions are present so partial genomes remain in [0, 1].

---

## 3. Performance Characteristics

### Static extraction cost

Static extraction calls `ast.parse()` once per file and runs three
single-pass AST visitors.  For typical competitive-programming files
(50–500 lines) this takes **< 5 ms per file** on a modern CPU.  The cost is
dominated by `ast.parse`, not the visitor logic.

### Dynamic extraction cost

Dynamic extraction uses `Tracer.trace()` with the 14 fixed canonical inputs
from `_FIXED_INPUTS` (integers, lists, strings).  Each input runs the traced
function in a dedicated `threading.Thread` with a 5-second hard wall-clock
timeout.  For typical programs the full trace pass takes **200 ms – 2 s per
file**.  When the callable cannot be loaded or tracing fails, the fast-path
returns immediately with `None` for all dynamic dimensions.

### Per-pair cost

Each unique file is extracted once; the result is cached.  A pair evaluation
reduces to two genome lookups plus the `behavioral_distance` aggregation
(negligible CPU).  Expected amortised cost for a cold evaluation:

| Scenario | Cost estimate |
|----------|---------------|
| Both static-only (no callable) | ~10 ms |
| Both fully dynamic | ~2–4 s |
| One file cached | ≈ cost of the uncached file only |

> **Note on identical-content pairs:** Because dynamic dimensions include
> wall-clock timing data (RESOURCE, TEMPORAL), two independent trace runs of
> the same source will not produce bit-for-bit identical genomes.
> `behavioral_distance` of independently-extracted genomes from identical
> source is therefore small but not exactly 0 (typically < 0.05 on simple
> programs).  `behavioral_distance(g, g)` (same object) is exactly 0 per the
> formal guarantee.

---

## 4. Caching Strategy

Two independent LRU caches are used, both backed by `functools.lru_cache`.

### 4.1 Genome cache — `_genome_for_path`

```
@functools.lru_cache(maxsize=512)
def _genome_for_path(resolved_path: str) -> Optional[Dict[str, Any]]
```

- Keyed by the **resolved absolute path** (via `pathlib.Path.resolve()`).
  Relative paths, symlinks, and `./` prefixes all collapse to the same slot.
- Returns a dict of present dimensions only (dimensions that failed extraction
  are filtered out before storage so `behavioral_distance` sees a clean input).
- Returns `None` if the file cannot be read at all.
- `maxsize=512` covers a typical baseline evaluation (hundreds of unique files)
  without unbounded memory growth.

### 4.2 Distance result cache — `_cached_distance`

```
@functools.lru_cache(maxsize=4096)
def _cached_distance(path_a: str, path_b: str) -> Optional[float]
```

- Keyed by an **ordered (sorted) pair** of resolved paths so that
  `d(a, b)` and `d(b, a)` map to the same cache slot, enforcing symmetry
  without storing both orderings.
- The public function `v1_behavioral_distance` normalises the order before
  calling `_cached_distance`.
- `maxsize=4096` covers a full cross-product evaluation (e.g. 500 base ×
  500 variant = 250 000 pairs in a rolling window).

### 4.3 Cache invalidation

Both caches are module-level and live for the Python process lifetime.  They
are not invalidated on file modification.  This is intentional: baseline
evaluation pipelines load files exactly once and never modify them during a
run.  If you need to force re-extraction, call
`_genome_for_path.cache_clear()` and `_cached_distance.cache_clear()`.

---

## 5. Graceful Degradation

| Failure mode | Behaviour |
|---|---|
| File not found / unreadable | `_genome_for_path` returns `None`; public functions return `None` |
| Syntax error in source | Static extraction returns `None` per dimension; dynamic extraction returns `None` (callable cannot be compiled); `behavioral_distance` runs on 0 active dims → `total_distance = 0.0`. Public functions return `0.0`, not `None`. |
| No callable entry point found | Dynamic extraction returns `None` for all 5 dynamic dims; static dims still computed; distance over static-only subset returned |
| Dynamic trace exception | Per-dimension try/except; surviving dimensions included; failing ones skipped |
| All dimensions fail | `genome` dict is empty after filtering; public functions return `None` |

The proxy **never raises** — all exceptions are caught and result in `None`.

---

## 6. Relationship to b08_hybrid_sbg_v2.py

The hybrid baseline's `_get_static_similarity` function should be replaced by:

```python
from sbg.v2.static_proxy import v1_behavioral_similarity

def _get_static_similarity(pair: dict) -> Optional[float]:
    if "sbg_static_similarity" in pair:
        return float(pair["sbg_static_similarity"])
    base = str(REPO_ROOT / pair["base_path"])
    var  = str(REPO_ROOT / pair["variant_path"])
    return v1_behavioral_similarity(base, var)
```

This replaces the token-overlap proxy with the genuine v1 SBG similarity
without touching `DEFAULT_WEIGHTS`, `behavioral_distance`, or any upstream
module.
