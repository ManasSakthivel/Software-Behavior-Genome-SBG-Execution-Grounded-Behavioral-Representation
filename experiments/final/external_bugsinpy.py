#!/usr/bin/env python3
"""
experiments/final/external_bugsinpy.py
======================================
BugsInPy under the corrected output-free protocol, following
docs/current/PHASE2_PREREGISTRATION.md §6.

Stages
------
fetch   (network) Enumerate every bug in a pinned BugsInPy checkout, parse its
        patch, and fetch each changed source file at the buggy and the fixed
        commit through the GitHub API. The files are cached outside the
        repository.
build   (static, no execution) For every bug, find each top-level function or
        class whose code the fix changed. Extract it at both commits as a
        self-contained *unit*, then decide eligibility by a static rule. Write
        the semantics-preserving negatives. Vendor the eligible units under
        external/bugsinpy/units/ and write external/bugsinpy/manifest.json.
        Record the SHA-256 of everything in artifacts/final/freeze_bugsinpy.json.
        All of this happens before anything is executed.
score   (offline) Verify the freeze and execute every eligible unit under the
        chosen protocol. Score the positive pair (buggy vs fixed) and the
        negatives (fixed vs SP variants of fixed). Write per-pair records and
        the summary artifact.

Unit definition
---------------
A unit is the changed top-level function, or the top-level class that contains
a changed method. It is closed over the module-level names it references, and
those names may resolve only to:

  - builtins;
  - standard-library imports;
  - other top-level functions or classes in the same file, closed recursively;
  - module-level constants whose value ``ast.literal_eval`` accepts.

Any other name makes the unit ineligible, and the manifest records the name and
its kind: project-internal import, third-party import, non-literal global, or
unresolved name.

Execution-safety exclusion
--------------------------
This rule is static and fixed before scoring. It is an addition to the
pre-registration: real code is being executed on synthetic inputs, so a unit is
ineligible if it uses a module or an ``os`` call that can act outside the
process. The modules are subprocess, socket, shutil, ctypes, multiprocessing,
signal, webbrowser, http, urllib, ftplib, smtplib, telnetlib, pty and asyncio.
The ``os`` calls are any that remove, rename or create files, spawn or kill
processes, exit, or change directory. Scoring also runs in a throwaway working
directory.

Labels
------
Positives are upstream developer fixes, the buggy/fixed commit pairs recorded
by BugsInPy. Negatives are produced by this repository's SP transformers. No
label is set or changed by hand.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import collections
import concurrent.futures
import copy
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import symtable
import sys
import tempfile
import threading
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "external" / "bugsinpy"
UNITS_DIR = OUT_DIR / "units"
MANIFEST = OUT_DIR / "manifest.json"
ARTIFACTS = REPO_ROOT / "artifacts" / "final"
FREEZE = ARTIFACTS / "freeze_bugsinpy.json"
THRESHOLD_FILE = ARTIFACTS / "THRESHOLD_FROZEN.json"

BUGSINPY_URL = "https://github.com/soarsmu/BugsInPy"

# SP negatives: fixed order and seed from the pre-registration.
SP_ORDER = ("SP-1", "SP-2", "SP-4", "SP-6", "SP-10", "SP-3", "SP-5", "SP-9")
SP_SEED = 0
MAX_NEGATIVES = 3

UNSAFE_MODULES = frozenset({
    "subprocess", "socket", "shutil", "ctypes", "multiprocessing", "signal",
    "webbrowser", "http", "urllib", "ftplib", "smtplib", "telnetlib", "pty",
    "asyncio",
})
UNSAFE_OS_ATTRS = frozenset({
    "system", "remove", "unlink", "rmdir", "removedirs", "rename", "renames",
    "replace", "kill", "killpg", "_exit", "fork", "forkpty", "chdir", "fchdir",
    "execv", "execve", "execl", "execle", "execlp", "execlpe", "execvp",
    "execvpe", "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve",
    "spawnvp", "spawnvpe", "popen", "makedirs", "mkdir", "chmod", "chown",
    "lchown", "symlink", "link", "truncate", "putenv", "unsetenv", "startfile",
    "posix_spawn", "posix_spawnp", "abort",
})

_MODULE_DUNDERS = frozenset({
    "__name__", "__file__", "__doc__", "__builtins__", "__spec__",
    "__loader__", "__package__", "__annotations__", "__debug__",
})
_BUILTIN_NAMES = frozenset(dir(builtins))

# sys.stdlib_module_names exists from 3.10. Eligibility is decided once, at build
# time, and frozen in the manifest; the fallback only lets the scoring stage be
# imported on 3.9.
_STDLIB = frozenset(getattr(sys, "stdlib_module_names", ())) | {"__future__"}

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_ADDRESS = re.compile(r"0x[0-9a-fA-F]+")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _rel(path: pathlib.Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_info(path: pathlib.Path) -> Dict[str, str]:
    info: Dict[str, str] = {}
    if not path.exists():
        return info
    for match in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', path.read_text(errors="replace")):
        info[match.group(1)] = match.group(2)
    return info


def _owner_repo(github_url: str) -> Optional[str]:
    match = re.match(r"https?://github\.com/([^/]+/[^/]+?)(?:\.git)?/?$", github_url.strip())
    return match.group(1) if match else None


def _is_test_path(path: str) -> bool:
    base = path.rsplit("/", 1)[-1]
    return (re.search(r"(^|/)(tests?|testing)/", path) is not None
            or base.startswith("test_") or base.endswith("_test.py")
            or base == "conftest.py")


# ---------------------------------------------------------------------------
# Patch parsing
# ---------------------------------------------------------------------------

def parse_patch(text: str) -> List[Dict[str, Any]]:
    """Changed line numbers per file, from a unified diff.

    ``old_lines`` are the removed lines of the buggy file and ``new_lines`` the
    added lines of the fixed file. A pure insertion anchors to the old line
    preceding it, and a pure deletion to the new line preceding it, so a change
    at the edge of a function body is still attributed to that function.
    """
    files: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    old_left = new_left = 0
    old_ln = new_ln = 0
    hunk_removed = hunk_added = False
    hunk_old_anchor = hunk_new_anchor = 0

    def close_hunk() -> None:
        if current is None:
            return
        if hunk_added and not hunk_removed and hunk_old_anchor > 0:
            current["old_lines"].add(hunk_old_anchor)
        if hunk_removed and not hunk_added and hunk_new_anchor > 0:
            current["new_lines"].add(hunk_new_anchor)

    in_hunk = False
    for line in text.splitlines():
        if in_hunk and (line.startswith("@@ ") or line.startswith("diff --git ")):
            close_hunk()             # a miscounted hunk must not swallow the next header
            in_hunk = False
        if in_hunk and (old_left > 0 or new_left > 0):
            tag = line[:1]
            if tag == "\\":
                continue
            if tag == "-":
                current["old_lines"].add(old_ln)
                hunk_removed = True
                if not hunk_new_anchor:
                    hunk_new_anchor = max(new_ln - 1, 1)
                old_ln += 1
                old_left -= 1
            elif tag == "+":
                current["new_lines"].add(new_ln)
                hunk_added = True
                if not hunk_old_anchor:
                    hunk_old_anchor = max(old_ln - 1, 1)
                new_ln += 1
                new_left -= 1
            else:
                old_ln += 1
                new_ln += 1
                old_left -= 1
                new_left -= 1
            if old_left <= 0 and new_left <= 0:
                close_hunk()
                in_hunk = False
            continue

        if line.startswith("diff --git "):
            current = {"old": None, "new": None, "old_lines": set(), "new_lines": set()}
            files.append(current)
            in_hunk = False
            continue
        if current is None:
            continue
        if line.startswith("--- "):
            target = line[4:].strip().split("\t")[0]
            current["old"] = None if target == "/dev/null" else (
                target[2:] if target.startswith("a/") else target)
            continue
        if line.startswith("+++ "):
            target = line[4:].strip().split("\t")[0]
            current["new"] = None if target == "/dev/null" else (
                target[2:] if target.startswith("b/") else target)
            continue
        match = _HUNK.match(line)
        if match:
            old_ln = int(match.group(1))
            old_left = int(match.group(2)) if match.group(2) is not None else 1
            new_ln = int(match.group(3))
            new_left = int(match.group(4)) if match.group(4) is not None else 1
            hunk_removed = hunk_added = False
            hunk_old_anchor = hunk_new_anchor = 0
            in_hunk = True
    return files


# ---------------------------------------------------------------------------
# Stage 1: enumerate and fetch
# ---------------------------------------------------------------------------

def enumerate_bugs(bugsinpy_dir: pathlib.Path) -> List[Dict[str, Any]]:
    bugs = []
    projects_dir = bugsinpy_dir / "projects"
    for project_dir in sorted(p for p in projects_dir.iterdir() if p.is_dir()):
        project_info = _read_info(project_dir / "project.info")
        bug_dirs = sorted((p for p in (project_dir / "bugs").iterdir() if p.is_dir()),
                          key=lambda p: (int(p.name) if p.name.isdigit() else 10 ** 9, p.name))
        for bug_dir in bug_dirs:
            info = _read_info(bug_dir / "bug.info")
            patch_path = bug_dir / "bug_patch.txt"
            patch = patch_path.read_text(errors="replace") if patch_path.exists() else ""
            files = parse_patch(patch)
            bugs.append({
                "project": project_dir.name,
                "bug": bug_dir.name,
                "bug_id": f"{project_dir.name}/{bug_dir.name}",
                "github_url": project_info.get("github_url", ""),
                "buggy_commit": info.get("buggy_commit_id", ""),
                "fixed_commit": info.get("fixed_commit_id", ""),
                "patch_sha256": _sha256_bytes(patch.encode()),
                "patch_files": [
                    {"old": f["old"], "new": f["new"],
                     "old_lines": sorted(f["old_lines"]), "new_lines": sorted(f["new_lines"])}
                    for f in files
                ],
            })
    return bugs


def _gh_fetch(owner_repo: str, commit: str, path: str) -> Tuple[Optional[bytes], Optional[str]]:
    cmd = ["gh", "api", "-H", "Accept: application/vnd.github.raw",
           f"repos/{owner_repo}/contents/{path}?ref={commit}"]
    for attempt in range(3):
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            continue
        if result.returncode == 0:
            return result.stdout, None
        err = result.stderr.decode(errors="replace").strip()[:200]
        if "404" in err or "Not Found" in err:
            return None, f"not_found: {err}"
    return None, "fetch_failed"


def resolve_short_commits(bugs: List[Dict[str, Any]], cache_dir: pathlib.Path) -> None:
    """Expand abbreviated commit ids (some pandas bug.info files record 7 characters).

    The id as recorded is kept alongside the resolved full SHA.
    """
    memo_path = cache_dir / "_resolved_commits.json"
    memo = json.loads(memo_path.read_text()) if memo_path.exists() else {}
    for bug in bugs:
        owner_repo = _owner_repo(bug["github_url"])
        for key in ("buggy_commit", "fixed_commit"):
            recorded = bug[key]
            bug[f"{key}_as_recorded"] = recorded
            if not owner_repo or not recorded or len(recorded) == 40:
                continue
            memo_key = f"{owner_repo}@{recorded}"
            if memo_key not in memo:
                result = subprocess.run(["gh", "api", f"repos/{owner_repo}/commits/{recorded}",
                                         "--jq", ".sha"], capture_output=True, text=True)
                memo[memo_key] = result.stdout.strip() if result.returncode == 0 else None
            if memo[memo_key]:
                bug[key] = memo[memo_key]
    cache_dir.mkdir(parents=True, exist_ok=True)
    memo_path.write_text(json.dumps(memo, indent=1))


def _cache_path(cache_dir: pathlib.Path, project: str, commit: str, path: str) -> pathlib.Path:
    return cache_dir / project / commit / path


def stage_fetch(bugsinpy_dir: pathlib.Path, cache_dir: pathlib.Path, workers: int) -> None:
    commit = subprocess.run(["git", "-C", str(bugsinpy_dir), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    bugs = enumerate_bugs(bugsinpy_dir)
    resolve_short_commits(bugs, cache_dir)
    jobs = []
    for bug in bugs:
        owner_repo = _owner_repo(bug["github_url"])
        if not owner_repo:
            continue
        for f in bug["patch_files"]:
            for side, key in (("buggy", "old"), ("fixed", "new")):
                path = f[key]
                if not path or not path.endswith(".py") or _is_test_path(path):
                    continue
                commit_id = bug["buggy_commit"] if side == "buggy" else bug["fixed_commit"]
                target = _cache_path(cache_dir, bug["project"], commit_id, path)
                if target.exists() or target.with_suffix(target.suffix + ".missing").exists():
                    continue
                jobs.append((owner_repo, commit_id, path, target))

    print(f"[fetch] {len(bugs)} bugs; {len(jobs)} files to fetch", flush=True)
    done = 0
    lock = threading.Lock()

    def run(job):
        nonlocal done
        owner_repo, commit_id, path, target = job
        data, err = _gh_fetch(owner_repo, commit_id, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if data is not None:
            target.write_bytes(data)
        else:
            target.with_suffix(target.suffix + ".missing").write_text(err or "unknown")
        with lock:
            done += 1
            if done % 50 == 0:
                print(f"[fetch] {done}/{len(jobs)}", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(run, jobs))

    licenses = {}
    for bug in bugs:
        owner_repo = _owner_repo(bug["github_url"])
        if owner_repo and bug["project"] not in licenses:
            result = subprocess.run(["gh", "api", f"repos/{owner_repo}", "--jq",
                                     ".license.spdx_id // \"NOASSERTION\""],
                                    capture_output=True, text=True)
            licenses[bug["project"]] = (result.stdout.strip() or "NOASSERTION"
                                        if result.returncode == 0 else "UNKNOWN")
    (cache_dir / "_enumeration.json").write_text(json.dumps({
        "bugsinpy_commit": commit, "bugs": bugs, "licenses": licenses,
    }, indent=1))
    print(f"[fetch] done; enumeration written to {cache_dir / '_enumeration.json'}")


# ---------------------------------------------------------------------------
# Stage 2: static unit extraction and eligibility
# ---------------------------------------------------------------------------

def _span(node: ast.AST) -> Tuple[int, int]:
    start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
    return start, node.end_lineno


def _locate(tree: ast.Module, line: int) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """(unit_top_name, changed_member, reason) for a changed line."""
    for node in tree.body:
        start, end = _span(node)
        if not (start <= line <= end):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name, node.name, None
        if isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_start, m_end = _span(member)
                    if m_start <= line <= m_end:
                        return node.name, f"{node.name}.{member.name}", None
            return None, None, "change_in_class_body_outside_methods"
        return None, None, "change_at_module_level"
    return None, None, "change_at_module_level"


class _ModuleIndex:
    """Top-level bindings of one source file."""

    def __init__(self, tree: ast.Module, source: str, file_path: str):
        self.tree = tree
        self.lines = source.splitlines()
        self.file_path = file_path
        self.defs: Dict[str, ast.AST] = {}
        self.consts: Dict[str, ast.AST] = {}
        self.imports: Dict[str, Tuple[ast.AST, ast.alias]] = {}
        self.ambiguous: Set[str] = set()
        self.futures: List[str] = []
        self.order: Dict[int, int] = {}
        counts: collections.Counter = collections.Counter()

        for index, node in enumerate(tree.body):
            self.order[id(node)] = index
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                counts[node.name] += 1
                self.defs[node.name] = node
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                names = [t.id for t in targets if isinstance(t, ast.Name)]
                literal = False
                if node.value is not None and len(names) == len(targets):
                    try:
                        ast.literal_eval(node.value)
                        literal = True
                    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
                        literal = False
                for target in targets:
                    for sub in ast.walk(target):
                        if isinstance(sub, ast.Name):
                            counts[sub.id] += 1
                            if literal and sub.id in names:
                                self.consts[sub.id] = node
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    bound = alias.asname or alias.name.split(".")[0]
                    counts[bound] += 1
                    self.imports[bound] = (node, alias)
            elif isinstance(node, ast.ImportFrom):
                if node.module == "__future__":
                    self.futures.append(ast.unparse(node))
                    continue
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    bound = alias.asname or alias.name
                    counts[bound] += 1
                    self.imports[bound] = (node, alias)
        self.ambiguous = {name for name, n in counts.items() if n > 1}

    def segment(self, node: ast.AST) -> str:
        start, end = _span(node)
        return "\n".join(self.lines[start - 1:end])


def _module_root(node: ast.AST, alias: ast.alias) -> Tuple[Optional[str], int]:
    if isinstance(node, ast.Import):
        return alias.name.split(".")[0], 0
    return (node.module or "").split(".")[0] or None, node.level


def _import_text(node: ast.AST, alias: ast.alias) -> str:
    if isinstance(node, ast.Import):
        return f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")
    return (f"from {'.' * node.level}{node.module or ''} import {alias.name}"
            + (f" as {alias.asname}" if alias.asname else ""))


def _classify_import(root: Optional[str], level: int, file_path: str) -> Optional[str]:
    """None if the import is allowed; otherwise the exclusion reason."""
    if level > 0 or root is None:
        return "project_internal_import"
    if root in UNSAFE_MODULES:
        return f"unsafe_module:{root}"
    if root in _STDLIB:
        return None
    top_dir = file_path.split("/")[0]
    if root == top_dir or root == top_dir.replace("-", "_"):
        return "project_internal_import"
    return "third_party_import"


def _table_type(table: symtable.SymbolTable) -> str:
    kind = table.get_type()
    return str(getattr(kind, "value", kind))


def _unresolved_globals(source: str) -> Set[str]:
    """Names the unit reads from module scope but does not define."""
    top = symtable.symtable(source, "<unit>", "exec")
    defined: Set[str] = set()
    referenced: Set[str] = set()

    def visit(table: symtable.SymbolTable) -> None:
        kind = _table_type(table)
        for sym in table.get_symbols():
            name = sym.get_name()
            if kind == "module":
                if sym.is_assigned() or sym.is_imported():
                    defined.add(name)
                if sym.is_referenced():
                    referenced.add(name)
            elif kind == "class":
                if sym.is_referenced() and not (sym.is_assigned() or sym.is_imported()):
                    referenced.add(name)
            else:
                if sym.is_referenced() and sym.is_global():
                    referenced.add(name)
        for child in table.get_children():
            visit(child)

    visit(top)
    return referenced - defined - _BUILTIN_NAMES - _MODULE_DUNDERS


def _safety_violation(unit_tree: ast.Module, file_path: str) -> Optional[str]:
    for node in ast.walk(unit_tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                root, level = _module_root(node, alias)
                if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                    continue
                reason = _classify_import(root, level, file_path)
                if reason:
                    return reason if reason.startswith("unsafe") else f"local_{reason}"
        if (isinstance(node, ast.Attribute) and node.attr in UNSAFE_OS_ATTRS
                and isinstance(node.value, ast.Name) and node.value.id == "os"):
            return f"unsafe_os_call:os.{node.attr}"
        if isinstance(node, ast.Name) and node.id in ("__import__", "exec", "eval", "compile"):
            return f"dynamic_code:{node.id}"
    return None


def build_unit(index: _ModuleIndex, top_name: str) -> Tuple[Optional[str], Optional[str]]:
    """(unit_source, None) or (None, exclusion_reason)."""
    if top_name in index.ambiguous:
        return None, f"ambiguous_binding:{top_name}"
    defs: Set[str] = {top_name}
    consts: Set[str] = set()
    imports: Dict[str, str] = {}

    for _ in range(200):
        parts: List[str] = list(index.futures)
        parts += [imports[name] for name in sorted(imports)]
        for name in sorted(consts, key=lambda n: index.order[id(index.consts[n])]):
            parts.append(index.segment(index.consts[name]))
        for name in sorted(defs, key=lambda n: index.order[id(index.defs[n])]):
            parts.append(index.segment(index.defs[name]))
        source = "\n\n".join(parts) + "\n"
        try:
            unresolved = _unresolved_globals(source)
        except SyntaxError as exc:
            return None, f"unit_not_parsable:{exc.msg}"
        if not unresolved:
            try:
                compile(source, "<unit>", "exec")
            except SyntaxError as exc:
                return None, f"unit_not_compilable:{exc.msg}"
            violation = _safety_violation(ast.parse(source), index.file_path)
            if violation:
                return None, violation
            return source, None
        for name in sorted(unresolved):
            if name in index.ambiguous:
                return None, f"ambiguous_binding:{name}"
            if name in index.defs:
                defs.add(name)
            elif name in index.consts:
                consts.add(name)
            elif name in index.imports:
                node, alias = index.imports[name]
                root, level = _module_root(node, alias)
                reason = _classify_import(root, level, index.file_path)
                if reason:
                    return None, f"{reason}:{name}"
                imports[name] = _import_text(node, alias)
            else:
                return None, f"non_literal_or_unresolved_global:{name}"
    return None, "closure_did_not_converge"


def _normalised(source: str) -> str:
    return ast.unparse(ast.parse(source))


def make_negatives(fixed_path: pathlib.Path) -> List[Tuple[str, str]]:
    """SP variants of the fixed unit, per the pre-registered order and seed."""
    from benchmark.transformations.preserving.transformer import apply_transformation
    base = fixed_path.read_text()
    base_norm = _normalised(base)
    kept: List[Tuple[str, str]] = []
    for kind in SP_ORDER:
        if len(kept) >= MAX_NEGATIVES:
            break
        try:
            variant, _meta = apply_transformation(str(fixed_path), kind, seed=SP_SEED)
            compile(variant, "<neg>", "exec")
            if _normalised(variant) == base_norm:
                continue
        except Exception:                               # noqa: BLE001 - rejected candidate
            continue
        kept.append((kind, variant))
    return kept


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")[:80]


def stage_build(cache_dir: pathlib.Path) -> None:
    enumeration = json.loads((cache_dir / "_enumeration.json").read_text())
    bugs = enumeration["bugs"]
    licenses = enumeration["licenses"]
    if UNITS_DIR.exists():
        for path in sorted(UNITS_DIR.rglob("*"), reverse=True):
            path.unlink() if path.is_file() else path.rmdir()
    UNITS_DIR.mkdir(parents=True, exist_ok=True)

    entries = []
    for bug in bugs:
        entry = {
            "id": bug["bug_id"], "project": bug["project"], "bug": bug["bug"],
            "source_repository": bug["github_url"],
            "buggy_commit": bug["buggy_commit"], "fixed_commit": bug["fixed_commit"],
            "buggy_commit_as_recorded": bug.get("buggy_commit_as_recorded"),
            "fixed_commit_as_recorded": bug.get("fixed_commit_as_recorded"),
            "license": licenses.get(bug["project"], "UNKNOWN"),
            "split": "external_test", "units": [], "eligible": False,
            "exclusion_reason": None, "file_notes": [],
        }
        entries.append(entry)
        if not _owner_repo(bug["github_url"]) or not bug["buggy_commit"] or not bug["fixed_commit"]:
            entry["exclusion_reason"] = "bug_metadata_incomplete"
            continue
        if len(bug["buggy_commit"]) != 40 or len(bug["fixed_commit"]) != 40:
            entry["exclusion_reason"] = "commit_not_resolvable_upstream"
            continue

        candidates: Dict[Tuple[str, str], Dict[str, Any]] = {}
        py_files = 0
        for f in bug["patch_files"]:
            old, new = f["old"], f["new"]
            path = new or old
            if not path or not path.endswith(".py"):
                entry["file_notes"].append({"file": path, "note": "non_python_file"})
                continue
            if _is_test_path(path):
                entry["file_notes"].append({"file": path, "note": "test_file"})
                continue
            py_files += 1
            if not old or not new or old != new:
                entry["file_notes"].append({"file": path, "note": "file_added_removed_or_renamed"})
                continue
            buggy_file = _cache_path(cache_dir, bug["project"], bug["buggy_commit"], path)
            fixed_file = _cache_path(cache_dir, bug["project"], bug["fixed_commit"], path)
            if not buggy_file.exists() or not fixed_file.exists():
                entry["file_notes"].append({"file": path, "note": "source_not_fetched"})
                continue
            try:
                buggy_src = buggy_file.read_text()
                fixed_src = fixed_file.read_text()
                buggy_tree = ast.parse(buggy_src)
                fixed_tree = ast.parse(fixed_src)
            except (SyntaxError, UnicodeDecodeError, ValueError) as exc:
                entry["file_notes"].append({"file": path, "note": f"not_parsable_by_python3: "
                                                                  f"{type(exc).__name__}"})
                continue
            located = collections.OrderedDict()
            outside = collections.Counter()
            for tree, lines in ((buggy_tree, f["old_lines"]), (fixed_tree, f["new_lines"])):
                for line in lines:
                    top, member, reason = _locate(tree, line)
                    if top:
                        located.setdefault(top, set()).add(member)
                    else:
                        outside[reason] += 1
            if outside:
                entry["file_notes"].append({"file": path, "note": "changes_outside_units",
                                            "counts": dict(outside)})
            for top, members in located.items():
                candidates[(path, top)] = {
                    "file": path, "unit": top, "changed_members": sorted(members),
                    "buggy_src": buggy_src, "fixed_src": fixed_src,
                    "buggy_tree": buggy_tree, "fixed_tree": fixed_tree,
                }

        if py_files == 0:
            entry["exclusion_reason"] = "no_non_test_python_file_changed"
            continue
        if not candidates:
            notes = {n["note"] for n in entry["file_notes"]}
            if "source_not_fetched" in notes:
                entry["exclusion_reason"] = "source_not_fetched"
            elif any(n.startswith("not_parsable") for n in notes):
                entry["exclusion_reason"] = "not_parsable_by_python3"
            elif "file_added_removed_or_renamed" in notes and len(notes) == 1:
                entry["exclusion_reason"] = "file_added_removed_or_renamed"
            else:
                entry["exclusion_reason"] = "change_outside_function_or_method"
            continue

        for (path, top), cand in candidates.items():
            unit = {"file": path, "unit": top, "changed_members": cand["changed_members"],
                    "kind": None, "eligible": False, "exclusion_reason": None}
            entry["units"].append(unit)
            buggy_index = _ModuleIndex(cand["buggy_tree"], cand["buggy_src"], path)
            fixed_index = _ModuleIndex(cand["fixed_tree"], cand["fixed_src"], path)
            if top not in buggy_index.defs or top not in fixed_index.defs:
                unit["exclusion_reason"] = "unit_added_or_removed_by_fix"
                continue
            node = fixed_index.defs[top]
            unit["kind"] = "class" if isinstance(node, ast.ClassDef) else "function"
            buggy_unit, reason_b = build_unit(buggy_index, top)
            fixed_unit, reason_f = build_unit(fixed_index, top)
            if buggy_unit is None or fixed_unit is None:
                unit["exclusion_reason"] = (f"buggy:{reason_b}" if buggy_unit is None
                                            else f"fixed:{reason_f}")
                continue
            if _normalised(buggy_unit) == _normalised(fixed_unit):
                unit["exclusion_reason"] = "unit_identical_after_normalisation"
                continue
            unit_dir = UNITS_DIR / f"{_slug(bug['project'])}__{bug['bug']}__{_slug(path)}__{_slug(top)}"
            unit_dir.mkdir(parents=True, exist_ok=True)
            header = (f"# BugsInPy {bug['bug_id']} | {bug['github_url']} | {path} | unit {top}\n"
                      f"# license: {entry['license']} (upstream project); extracted verbatim, "
                      f"closure only, no edits\n")
            (unit_dir / "buggy.py").write_text(
                header + f"# commit {bug['buggy_commit']} (buggy)\n" + buggy_unit)
            (unit_dir / "fixed.py").write_text(
                header + f"# commit {bug['fixed_commit']} (fixed)\n" + fixed_unit)
            negatives = make_negatives(unit_dir / "fixed.py")
            unit["negatives"] = []
            for kind, source in negatives:
                name = f"neg_{kind.lower()}.py"
                (unit_dir / name).write_text(source)
                unit["negatives"].append({"transformation": kind, "path": _rel(unit_dir / name)})
            unit["eligible"] = True
            unit["unit_dir"] = _rel(unit_dir)
            unit["buggy_path"] = _rel(unit_dir / "buggy.py")
            unit["fixed_path"] = _rel(unit_dir / "fixed.py")
            unit["interface"] = ("top-level class" if unit["kind"] == "class"
                                 else "top-level function")

        if any(u["eligible"] for u in entry["units"]):
            entry["eligible"] = True
        else:
            reasons = [u["exclusion_reason"] for u in entry["units"]]
            entry["exclusion_reason"] = "no_eligible_unit"
            entry["unit_exclusion_reasons"] = reasons

    taxonomy = collections.Counter(
        entry["exclusion_reason"] for entry in entries if not entry["eligible"])

    def reason_family(reason: str) -> str:
        parts = reason.split(":")
        if parts[0] in ("buggy", "fixed") and len(parts) > 1:
            return parts[1]
        return parts[0]

    unit_family = collections.Counter(
        reason_family(u["exclusion_reason"]) for e in entries for u in e["units"]
        if not u["eligible"])

    manifest = {
        "manifest": "BUGSINPY_REAL_PROGRAM_MANIFEST",
        "bugsinpy_repository": BUGSINPY_URL,
        "bugsinpy_commit": enumeration["bugsinpy_commit"],
        "built_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "built_with_python": sys.version.split()[0],
        "preregistration": "docs/current/PHASE2_PREREGISTRATION.md §6",
        "unit_rule": ("changed top-level function, or top-level class containing a changed "
                      "method, closed over same-file top-level defs and literal constants; "
                      "only builtins and standard-library imports allowed"),
        "safety_rule": {"unsafe_modules": sorted(UNSAFE_MODULES),
                        "unsafe_os_attrs": sorted(UNSAFE_OS_ATTRS),
                        "dynamic_code": ["__import__", "exec", "eval", "compile"]},
        "negatives_rule": {"order": list(SP_ORDER), "seed": SP_SEED, "max_per_unit": MAX_NEGATIVES},
        "counts": {
            "bugs_total": len(entries),
            "bugs_eligible": sum(e["eligible"] for e in entries),
            "units_total": sum(len(e["units"]) for e in entries),
            "units_eligible": sum(u["eligible"] for e in entries for u in e["units"]),
            "negatives_total": sum(len(u.get("negatives", [])) for e in entries
                                   for u in e["units"] if u["eligible"]),
        },
        "bug_exclusion_taxonomy": dict(sorted(taxonomy.items(), key=lambda kv: -kv[1])),
        "unit_exclusion_taxonomy": dict(sorted(unit_family.items(), key=lambda kv: -kv[1])),
        "licenses": licenses,
        "bugs": entries,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n")
    write_freeze()
    print(json.dumps(manifest["counts"], indent=1))
    print("bug exclusions:", json.dumps(manifest["bug_exclusion_taxonomy"], indent=1))
    print("unit exclusions:", json.dumps(manifest["unit_exclusion_taxonomy"], indent=1))


def _frozen_files() -> List[pathlib.Path]:
    return [MANIFEST] + sorted(p for p in UNITS_DIR.rglob("*.py"))


def _freeze_digest() -> Tuple[str, Dict[str, str]]:
    per_file = {_rel(p): _sha256_bytes(p.read_bytes()) for p in _frozen_files()}
    combined = hashlib.sha256("".join(f"{k}\0{v}\n" for k, v in sorted(per_file.items()))
                              .encode()).hexdigest()
    return combined, per_file


def write_freeze() -> None:
    combined, per_file = _freeze_digest()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FREEZE.write_text(json.dumps({
        "artifact": "FREEZE_BUGSINPY",
        "frozen_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "note": "Written by the build stage, before any unit is executed or scored.",
        "combined_sha256": combined,
        "n_files": len(per_file),
        "files": per_file,
    }, indent=1) + "\n")
    print(f"[build] freeze {combined[:16]}… over {len(per_file)} files -> {_rel(FREEZE)}")


# ---------------------------------------------------------------------------
# Stage 3: score
# ---------------------------------------------------------------------------

def _call_graph(tree: ast.Module) -> Dict[str, Set[str]]:
    """name -> names it calls, for top-level functions and methods (by bare name)."""
    graph: Dict[str, Set[str]] = collections.defaultdict(set)

    def calls_in(node: ast.AST) -> Set[str]:
        names = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                if isinstance(sub.func, ast.Name):
                    names.add(sub.func.id)
                elif isinstance(sub.func, ast.Attribute):
                    names.add(sub.func.attr)
            elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                names.add(sub.id)        # functions passed as values count as reachable
        return names

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            graph[node.name] |= calls_in(node)
        elif isinstance(node, ast.ClassDef):
            graph[node.name] |= {"__init__"}
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    graph[member.name] |= calls_in(member)
                    graph[node.name] |= set()
    return graph


def _reachable(tree: ast.Module, roots: Sequence[str]) -> Set[str]:
    graph = _call_graph(tree)
    seen: Set[str] = set()
    stack = list(roots)
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(graph.get(name, ()))
    return seen


def _positive_is_observable(source: str, entry_function: Optional[str],
                            entry_discovery: Optional[str], unit: Dict[str, Any]) -> bool:
    """Static: is a changed member reachable from the protocol's entry?"""
    tree = ast.parse(source)
    changed = set()
    for member in unit["changed_members"]:
        changed.add(member.split(".")[-1])
    if unit["kind"] == "class":
        changed.add(unit["unit"])
    roots: List[str] = []
    if entry_function:
        roots.append(entry_function)
    discovery = entry_discovery or ""
    if "class" in discovery.lower() or (entry_function and entry_function[:1].isupper()):
        # Class tier: constructors and every public method of every class are
        # candidate roots; the prereg's driver calls eligible public methods.
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                roots.append("__init__")
                for member in node.body:
                    if (isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and not member.name.startswith("_")):
                        roots.append(member.name)
    if not roots:
        return False
    return bool(_reachable(tree, roots) & changed)


def _output_reference(path: pathlib.Path, timeout_s: float = 1.0) -> Optional[List[str]]:
    """Outputs of the protocol's function entry on the protocol's inputs.

    An output-reading reference, reported only as a ceiling. It is never an
    input to any SBG distance.
    """
    import importlib.util
    import types as _types
    from experiments.final.protocol import select_entry_output_free

    source = path.read_text()
    module = _types.ModuleType(f"_bugsinpy_ref_{abs(hash(str(path)))}")
    saved = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        spec = importlib.util.spec_from_file_location(module.__name__, str(path))
        spec.loader.exec_module(module)          # type: ignore[union-attr]
        fn, _discovery, inputs = select_entry_output_free(module, source)
    except BaseException:                        # noqa: BLE001
        return None
    finally:
        sys.stdout.close()
        sys.stdout = saved
    if fn is None or inputs is None:
        return None

    outputs: List[str] = []
    for inp in inputs:
        box: Dict[str, str] = {}

        def run() -> None:
            saved_out = sys.stdout
            try:
                args = copy.deepcopy(inp)
                if inputs == [None]:
                    value = fn()
                elif isinstance(args, tuple):
                    value = fn(*args)
                else:
                    value = fn(args)
                box["out"] = "ret:" + _ADDRESS.sub("0x?", repr(value))[:2000]
            except BaseException as exc:         # noqa: BLE001
                box["out"] = f"exc:{type(exc).__name__}"
            finally:
                sys.stdout = saved_out

        worker = threading.Thread(target=run, daemon=True)
        host = sys.stdout
        worker.start()
        worker.join(timeout_s)
        if sys.stdout is not host:
            sys.stdout = host
        outputs.append(box.get("out", "timeout"))
    return outputs


def _verify_freeze() -> str:
    if not FREEZE.exists():
        raise SystemExit("freeze file missing: run the build stage first")
    frozen = json.loads(FREEZE.read_text())
    combined, _ = _freeze_digest()
    if combined != frozen["combined_sha256"]:
        raise SystemExit("frozen BugsInPy inputs changed since the freeze; refusing to score")
    return combined


def _choose_protocol(requested: Optional[str]) -> str:
    from experiments.final import extraction
    if requested:
        if requested not in extraction.PROTOCOLS:
            raise SystemExit(f"protocol {requested} not available: {extraction.PROTOCOLS}")
        return requested
    return "output_free_v7" if "output_free_v7" in extraction.PROTOCOLS else "output_free_v6"


def _threshold() -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
    if not THRESHOLD_FILE.exists():
        return None, None
    data = json.loads(THRESHOLD_FILE.read_text())
    for key in ("tau_star", "tau", "threshold", "value"):
        if isinstance(data.get(key), (int, float)):
            return float(data[key]), data
    return None, data


def stage_score(protocol_arg: Optional[str]) -> None:
    from experiments.final import extraction
    from experiments.final.static_baselines import (ast_multiset, multiset_distance,
                                                    token_multiset)

    freeze_digest = _verify_freeze()
    protocol = _choose_protocol(protocol_arg)
    manifest = json.loads(MANIFEST.read_text())
    tau, tau_record = _threshold()

    workdir = tempfile.mkdtemp(prefix="sbg_bugsinpy_run_")
    original_cwd = os.getcwd()
    os.chdir(workdir)
    cache: Dict[str, Any] = {}
    rows: List[Dict[str, Any]] = []
    ref_cache: Dict[str, Optional[List[str]]] = {}
    try:
        units = [(entry, unit) for entry in manifest["bugs"] for unit in entry["units"]
                 if unit["eligible"]]
        print(f"[score] protocol={protocol} units={len(units)} freeze={freeze_digest[:12]}",
              flush=True)
        for number, (entry, unit) in enumerate(units, 1):
            fixed_path = REPO_ROOT / unit["fixed_path"]
            fixed_rec = extraction.extract_program(str(fixed_path), cache, protocol)
            fixed_src = fixed_path.read_text()
            comparisons = [("positive", 1, "real_fix", REPO_ROOT / unit["buggy_path"])]
            comparisons += [("negative", 0, neg["transformation"], REPO_ROOT / neg["path"])
                            for neg in unit.get("negatives", [])]
            if fixed_path.as_posix() not in ref_cache:
                ref_cache[fixed_path.as_posix()] = _output_reference(fixed_path)
            for role, label, transformation, other_path in comparisons:
                other_rec = extraction.extract_program(str(other_path), cache, protocol)
                other_src = other_path.read_text()
                scores = extraction.score_pair(fixed_rec, other_rec)
                failure_side = None
                if scores is None:
                    failure_side = "fixed" if not fixed_rec.ok else "other"
                if other_path.as_posix() not in ref_cache:
                    ref_cache[other_path.as_posix()] = _output_reference(other_path)
                ref_a, ref_b = ref_cache[fixed_path.as_posix()], ref_cache[other_path.as_posix()]
                reference = None if (ref_a is None or ref_b is None) else float(ref_a != ref_b)
                observable = None
                if scores is not None and label == 1:
                    observable = _positive_is_observable(
                        other_src, other_rec.entry_function, other_rec.entry_discovery, unit) or \
                        _positive_is_observable(
                            fixed_src, fixed_rec.entry_function, fixed_rec.entry_discovery, unit)
                row = {
                    "pair_id": f"{entry['id']}::{unit['file']}::{unit['unit']}::{transformation}",
                    "bug_id": entry["id"], "project": entry["project"],
                    "unit": unit["unit"], "unit_kind": unit["kind"], "file": unit["file"],
                    "role": role, "label": label, "transformation": transformation,
                    "base_path": unit["fixed_path"], "variant_path": _rel(other_path),
                    "protocol": protocol,
                    "base_entry": fixed_rec.entry_discovery, "variant_entry": other_rec.entry_discovery,
                    "evaluated": scores is not None,
                    "failure_side": failure_side,
                    "failure_kind": (None if scores is not None else
                                     (fixed_rec.failure_kind if failure_side == "fixed"
                                      else other_rec.failure_kind)),
                    "failure_detail": (None if scores is not None else
                                       (fixed_rec.failure_detail if failure_side == "fixed"
                                        else other_rec.failure_detail)),
                    "observable": observable,
                    "scores": dict(scores) if scores is not None else None,
                    "output_reading_reference": reference,
                }
                statics = {
                    "static_token": round(multiset_distance(token_multiset(fixed_src),
                                                            token_multiset(other_src)), 9),
                    "static_ast": round(multiset_distance(ast_multiset(fixed_src),
                                                          ast_multiset(other_src)), 9),
                }
                row["static_scores"] = statics
                if row["scores"] is not None:
                    row["scores"].update(statics)
                rows.append(row)
            if number % 10 == 0:
                print(f"[score] {number}/{len(units)} units", flush=True)
    finally:
        os.chdir(original_cwd)

    pairs_path = ARTIFACTS / f"pairs_bugsinpy_{protocol}.jsonl"
    with pairs_path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    summary = analyse(rows, manifest, protocol, freeze_digest, tau, tau_record)
    out_path = ARTIFACTS / f"BUGSINPY_{protocol}.json"
    out_path.write_text(json.dumps(summary, indent=1) + "\n")
    print(f"[score] wrote {_rel(pairs_path)} and {_rel(out_path)}")
    print(json.dumps(summary["headline"], indent=1))


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

HOLM_COMPARATORS = ("static_ast", "static_token", "exception_fraction", "call_count", "sbg_v3")


def _metrics(rows: List[Dict[str, Any]], predictor: str) -> Dict[str, Any]:
    from sbg.statistics import auroc, cluster_bootstrap_ci, cluster_permutation_p
    d = [r["scores"][predictor] for r in rows]
    y = [r["label"] for r in rows]
    c = [r["bug_id"] for r in rows]
    n_pos, n_neg = sum(y), len(y) - sum(y)
    if n_pos == 0 or n_neg == 0:
        return {"auroc": None, "reason": "needs both classes", "n_pos": n_pos, "n_neg": n_neg}
    lower, upper, n_eff = cluster_bootstrap_ci(d, y, c)
    return {"auroc": round(auroc(d, y), 6), "ci_lower": lower, "ci_upper": upper,
            "ci_n_effective": n_eff, "p_permutation": cluster_permutation_p(d, y, c),
            "n_pairs": len(y), "n_pos": n_pos, "n_neg": n_neg,
            "n_clusters": len(set(c))}


def analyse(rows: List[Dict[str, Any]], manifest: Dict[str, Any], protocol: str,
            freeze_digest: str, tau: Optional[float],
            tau_record: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    from sbg.statistics import (holm_bonferroni, label_shuffle_noise_floor,
                                paired_cluster_bootstrap_delta, wilson_interval)
    from experiments.final.extraction import PREDICTORS

    evaluable = [r for r in rows if r["evaluated"]]
    valid = [r for r in evaluable if r["label"] == 0 or r["observable"]]
    all_rows = []
    for r in rows:
        if r["evaluated"]:
            all_rows.append(r)
        else:
            filler = {p: 0.0 for p in PREDICTORS}
            filler.update(r["static_scores"])
            all_rows.append(dict(r, scores=filler))

    sets = {"ALL": all_rows, "EVALUABLE": evaluable, "VALID": valid}
    predictors = [p for p in PREDICTORS]
    results: Dict[str, Any] = {}
    for name, subset in sets.items():
        results[name] = {"n_pairs": len(subset),
                         "n_pos": sum(r["label"] for r in subset),
                         "n_neg": sum(1 - r["label"] for r in subset),
                         "n_bugs": len({r["bug_id"] for r in subset}),
                         "n_bugs_with_positive": len({r["bug_id"] for r in subset if r["label"]}),
                         "predictors": {p: _metrics(subset, p) for p in predictors}}

    primary = valid
    comparisons, raw_p = {}, {}
    if primary and 0 < sum(r["label"] for r in primary) < len(primary):
        y = [r["label"] for r in primary]
        c = [r["bug_id"] for r in primary]
        a = [r["scores"]["sbg_v5"] for r in primary]
        for comp in HOLM_COMPARATORS:
            res = paired_cluster_bootstrap_delta(a, [r["scores"][comp] for r in primary], y, c)
            comparisons[comp] = res
            if res.get("p_two_sided") is not None:
                raw_p[comp] = res["p_two_sided"]
        noise = label_shuffle_noise_floor(a, y, c)
    else:
        noise = None
    holm = holm_bonferroni(raw_p) if raw_p else {}

    threshold_block: Dict[str, Any]
    if tau is None:
        threshold_block = {"computed": False,
                           "reason": "artifacts/final/THRESHOLD_FROZEN.json not present when "
                                     "this artifact was produced; τ*-dependent metrics not computed"}
    else:
        pos = [r for r in primary if r["label"] == 1]
        neg = [r for r in primary if r["label"] == 0]
        tp = sum(r["scores"]["sbg_v5"] > tau for r in pos)
        fp = sum(r["scores"]["sbg_v5"] > tau for r in neg)
        threshold_block = {
            "computed": True, "tau_star": tau,
            "tau_source": _rel(THRESHOLD_FILE),
            "tau_record_sha256": _sha256_bytes(THRESHOLD_FILE.read_bytes()),
            "rule": "detected iff sbg_v5 > τ*",
            "tau_protocol": (tau_record or {}).get("protocol"),
            "tau_protocol_matches_run": (tau_record or {}).get("protocol") == protocol,
            "detection_rate": {"k": tp, "n": len(pos),
                               "rate": round(tp / len(pos), 6) if pos else None,
                               "wilson_95": list(wilson_interval(tp, len(pos))) if pos else None},
            "false_positive_rate": {"k": fp, "n": len(neg),
                                    "rate": round(fp / len(neg), 6) if neg else None,
                                    "wilson_95": list(wilson_interval(fp, len(neg))) if neg else None},
        }

    ref_pos = [r for r in primary if r["label"] == 1 and r["output_reading_reference"] is not None]
    ref_neg = [r for r in primary if r["label"] == 0 and r["output_reading_reference"] is not None]
    reference = {
        "label": "OUTPUT-READING REFERENCE — reads return values; not SBG, not output-free",
        "rule": "flags a pair iff the function entry's return values or exception types differ "
                "on the protocol's inputs",
        "positives_flagged": {"k": int(sum(r["output_reading_reference"] for r in ref_pos)),
                              "n": len(ref_pos)},
        "negatives_flagged": {"k": int(sum(r["output_reading_reference"] for r in ref_neg)),
                              "n": len(ref_neg)},
        "note": "computed only where the protocol selects a function entry",
    }

    failures = collections.Counter(
        f"{r['failure_side']}:{r['failure_kind']}" for r in rows if not r["evaluated"])
    unobservable = sum(1 for r in evaluable if r["label"] == 1 and not r["observable"])
    counts = manifest["counts"]
    v5 = results["VALID"]["predictors"]["sbg_v5"]
    headline = {
        "protocol": protocol,
        "bugs_total": counts["bugs_total"],
        "bugs_with_eligible_unit": counts["bugs_eligible"],
        "units_eligible": counts["units_eligible"],
        "pairs_total": len(rows),
        "pairs_evaluable": len(evaluable),
        "pairs_valid": len(valid),
        "bugs_evaluated_with_valid_positive": results["VALID"]["n_bugs_with_positive"],
        "sbg_v5_auroc_valid": v5.get("auroc"),
        "sbg_v5_ci_valid": [v5.get("ci_lower"), v5.get("ci_upper")],
        "tau_metrics_computed": threshold_block["computed"],
    }
    return {
        "experiment": "BUGSINPY_OUTPUT_FREE_EVALUATION",
        "produced_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "produced_with_python": sys.version.split()[0],
        "protocol": protocol,
        "preregistration": "docs/current/PHASE2_PREREGISTRATION.md §6 (BugsInPy)",
        "bugsinpy_commit": manifest["bugsinpy_commit"],
        "manifest": _rel(MANIFEST),
        "freeze": {"file": _rel(FREEZE), "combined_sha256": freeze_digest},
        "input_regime": "canonical (protocol-synthesised inputs only)",
        "cluster_unit": "bug (project/bug id)",
        "labels": ("positives: upstream developer fixes recorded by BugsInPy (buggy vs fixed "
                   "commit); negatives: repository SP transformers applied to the fixed unit; "
                   "no label set or edited by hand"),
        "headline": headline,
        "stage_counts": {
            "bugs_total": counts["bugs_total"],
            "bugs_excluded_before_scoring": counts["bugs_total"] - counts["bugs_eligible"],
            "bug_exclusion_taxonomy": manifest["bug_exclusion_taxonomy"],
            "units_total": counts["units_total"],
            "units_eligible": counts["units_eligible"],
            "unit_exclusion_taxonomy": manifest["unit_exclusion_taxonomy"],
            "negatives_generated": counts["negatives_total"],
            "pairs_total": len(rows),
            "pairs_failed_at_execution": dict(failures),
            "positives_unobservable_from_entry": unobservable,
        },
        "set_definitions": {
            "ALL": "every pair; unevaluable pairs scored at distance 0 (static baselines kept)",
            "EVALUABLE": "both sides executed under the protocol",
            "VALID": "EVALUABLE, and for positives a changed member statically reachable from "
                     "the protocol's entry (primary set)",
        },
        "sets": results,
        "primary_set": "VALID",
        "holm_comparisons_sbg_v5_vs": {"raw": comparisons, "holm": holm},
        "label_shuffle_noise_floor": noise,
        "threshold": threshold_block,
        "output_reading_reference": reference,
    }


# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="stage", required=True)
    fetch = sub.add_parser("fetch")
    fetch.add_argument("--bugsinpy-dir", type=pathlib.Path, required=True)
    fetch.add_argument("--cache-dir", type=pathlib.Path, required=True)
    fetch.add_argument("--workers", type=int, default=8)
    build = sub.add_parser("build")
    build.add_argument("--cache-dir", type=pathlib.Path, required=True)
    score = sub.add_parser("score")
    score.add_argument("--protocol", default=None)
    args = parser.parse_args()
    if args.stage == "fetch":
        stage_fetch(args.bugsinpy_dir, args.cache_dir, args.workers)
    elif args.stage == "build":
        stage_build(args.cache_dir)
    else:
        stage_score(args.protocol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
