"""
SBG Benchmark — Semantics-Changing Mutation Framework
======================================================
14 mutation operators, each using the ast module to make targeted,
syntactically valid, semantically altering changes to Python programs.

Every mutator:
  - Is deterministic given the same seed + site index
  - Produces syntactically valid Python (compile-checked)
  - Returns the original source unchanged if no applicable site found
  - Produces a MutantRecord with full provenance
  - Mutates only the program's functional code (see SITE RESTRICTION below)

SITE RESTRICTION
----------------
Mutation sites are collected with ``ast.walk`` over the whole module, which
walks in breadth-first order. Module-level statements are therefore visited
before anything nested, and site 0 -- the site every generated variant in the
original benchmark used -- lands on module-level scaffolding: the module
docstring, or the ``if __name__ == '__main__'`` guard, or a ``test_*`` driver.

The consequences were measured by ``benchmark/scripts/observability_audit.py``
on the original benchmark: 135 of 336 CHANGED-labelled test pairs (40%) carry a
mutation that is unreachable from the traced entry function, so the two
programs are behaviourally identical and the CHANGED label is false. A further
180 variants across all splits had their ``__main__`` guard inverted from
``==`` to ``!=``, which makes the file execute its own test driver on import;
22 of those crash while loading and were silently dropped from the denominator.

``_functional_node_ids`` restricts sites to statements inside non-scaffolding
definitions. The restriction applies to mutations only. Semantics-preserving
transformations may still touch scaffolding, because a rename or a reformat
leaves the EQUIVALENT label true wherever it is applied, whereas a mutation in
scaffolding leaves the CHANGED label false.
"""
import ast
import copy
import hashlib
import json
import os
import random
import textwrap
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Data record
# ---------------------------------------------------------------------------

@dataclass
class MutantRecord:
    base_id: str
    variant_id: str
    mutation_type: str
    semantic_relation: str = "CHANGED"
    generator: str = "mutator.py"
    seed: int = 0
    mutation_site: int = 0
    expected_label: str = "CHANGED"
    witness_input: str = ""
    hard_negative: bool = False          # triggers on <10% of uniform random inputs
    base_hash: str = ""
    variant_hash: str = ""
    timestamp: str = ""
    applied: bool = False                # False if no site found / no-op

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _unparse(tree) -> str:
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def _is_valid_python(source: str) -> bool:
    try:
        compile(source, "<string>", "exec")
        return True
    except SyntaxError:
        return False



# ---------------------------------------------------------------------------
# Site restriction helpers
# ---------------------------------------------------------------------------

def is_scaffolding(name: str) -> bool:
    """True for self-test drivers, demo entry points and private helpers.

    These are not part of the program's behaviour under the evaluation
    protocol, so mutating them produces a variant labelled CHANGED that is in
    fact behaviourally identical.
    """
    return (name.startswith("test_") or name in ("main", "demo", "demo_main",
                                                 "benchmark"))


def _functional_node_ids(tree) -> set:
    """ids of every AST node inside a non-scaffolding top-level definition.

    Module-level statements outside any definition -- the docstring, constants
    and the ``__main__`` guard -- are deliberately excluded. Module constants
    are excluded too: the benchmark's entry functions read them only through
    the definitions that are already covered here, and including them would
    re-admit the docstring, which is the site the original generator picked
    most often.
    """
    allowed = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if is_scaffolding(node.name):
                continue
        elif isinstance(node, ast.ClassDef):
            if is_scaffolding(node.name.lower()):
                continue
        else:
            continue
        for sub in ast.walk(node):
            allowed.add(id(sub))
    return allowed


def _docstring_node_ids(tree) -> set:
    """ids of Constant nodes that are module, class or function docstrings."""
    out = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)) or not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            out.add(id(first.value))
    return out


def _site_is_allowed(site, allowed: set) -> bool:
    """A site is allowed when any AST node it carries sits in functional code."""
    candidates = site if isinstance(site, (tuple, list)) else (site,)
    nodes = [c for c in candidates if isinstance(c, ast.AST)]
    if not nodes:
        return False
    return any(id(node) in allowed for node in nodes)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class BaseMutator:
    mutation_type: str = "SC-0"
    witness_input: str = ""
    hard_negative: bool = False

    def apply(self, source_code: str, seed: int = 0, mutation_site: int = 0,
              restrict_to_functional_code: bool = True) -> str:
        random.seed(seed)
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return source_code
        tree = copy.deepcopy(tree)
        sites = self._collect_sites(tree)
        if restrict_to_functional_code:
            allowed = _functional_node_ids(tree)
            sites = [site for site in sites if _site_is_allowed(site, allowed)]
        if not sites:
            return source_code
        site_idx = mutation_site % len(sites)
        self._apply_at(tree, sites, site_idx, seed)
        result = _unparse(tree)
        if not _is_valid_python(result):
            return source_code
        return result

    def _collect_sites(self, tree) -> list:
        raise NotImplementedError

    def _apply_at(self, tree, sites, idx, seed):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# SC-1: OFF_BY_ONE — modify range bounds or comparison operators by 1
# ---------------------------------------------------------------------------

class OffByOneMutator(BaseMutator):
    mutation_type = "SC-1"
    witness_input = "boundary value of range (e.g., last element)"
    hard_negative = True

    def _collect_sites(self, tree):
        sites = []
        for node in ast.walk(tree):
            # range(n) → range(n-1) or range(n+1)
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == 'range' and len(node.args) >= 1:
                    sites.append(('range', node))
            # Num constants in Compare (i < N → i < N-1)
            if isinstance(node, ast.Compare):
                for comp, op in zip(node.comparators, node.ops):
                    if isinstance(comp, ast.Constant) and isinstance(comp.value, int):
                        sites.append(('compare_const', comp))
        return sites

    def _apply_at(self, tree, sites, idx, seed):
        kind, node = sites[idx]
        if kind == 'range':
            last_arg = node.args[-1]
            if isinstance(last_arg, ast.Constant) and isinstance(last_arg.value, int):
                last_arg.value += random.choice([-1, 1])
            elif isinstance(last_arg, ast.Name):
                # range(n) → range(n - 1)
                node.args[-1] = ast.BinOp(
                    left=copy.deepcopy(last_arg),
                    op=ast.Sub(),
                    right=ast.Constant(value=1)
                )
        elif kind == 'compare_const':
            node.value += random.choice([-1, 1])


# ---------------------------------------------------------------------------
# SC-2: OPERATOR_MUTATION — swap arithmetic or boolean operator
# ---------------------------------------------------------------------------

class OperatorMutator(BaseMutator):
    mutation_type = "SC-2"
    witness_input = "any non-zero pair of operands"
    hard_negative = False

    _ARITH_SWAPS = {
        ast.Add: ast.Sub, ast.Sub: ast.Add,
        ast.Mult: ast.Div, ast.Div: ast.Mult,
        ast.Mod: ast.Mult, ast.FloorDiv: ast.Mult,
    }
    _CMP_SWAPS = {
        ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
        ast.Lt: ast.Gt, ast.Gt: ast.Lt,
        ast.LtE: ast.GtE, ast.GtE: ast.LtE,
    }

    def _collect_sites(self, tree):
        sites = []
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and type(node.op) in self._ARITH_SWAPS:
                sites.append(('arith', node))
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    if type(op) in self._CMP_SWAPS:
                        sites.append(('cmp', node))
        return sites

    def _apply_at(self, tree, sites, idx, seed):
        kind, node = sites[idx]
        if kind == 'arith':
            node.op = self._ARITH_SWAPS[type(node.op)]()
        elif kind == 'cmp':
            node.ops = [self._CMP_SWAPS.get(type(op), type(op))() for op in node.ops]


# ---------------------------------------------------------------------------
# SC-3: CONSTANT_MUTATION — perturb an integer or string constant
# ---------------------------------------------------------------------------

class ConstantMutator(BaseMutator):
    mutation_type = "SC-3"
    witness_input = "any input that reaches the mutated constant"
    hard_negative = False

    def _collect_sites(self, tree):
        # Docstrings are string constants but carry no behaviour: appending a
        # suffix to one produces a variant labelled CHANGED that executes
        # identically. They were the most frequently chosen SC-3 site in the
        # original benchmark, so they are excluded here.
        docstrings = _docstring_node_ids(tree)
        sites = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and id(node) not in docstrings:
                if isinstance(node.value, int) and node.value not in (0, 1, -1, True, False):
                    sites.append(('int', node))
                elif isinstance(node.value, str) and len(node.value) > 0:
                    sites.append(('str', node))
        return sites

    def _apply_at(self, tree, sites, idx, seed):
        kind, node = sites[idx]
        if kind == 'int':
            node.value += random.choice([-1, 1, 2, -2])
        elif kind == 'str':
            s = node.value
            node.value = s + "_mutated" if s else "mutated"


# ---------------------------------------------------------------------------
# SC-4: BOUNDARY_CONDITION — remove a guard/boundary check
# ---------------------------------------------------------------------------

class BoundaryConditionMutator(BaseMutator):
    mutation_type = "SC-4"
    witness_input = "input that violates the removed guard (e.g., negative index, empty list)"
    hard_negative = True

    def _collect_sites(self, tree):
        """Find If nodes that look like guards (short body, Return or raise)."""
        sites = []
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                body = node.body
                if len(body) <= 2 and any(isinstance(s, (ast.Return, ast.Raise)) for s in body):
                    sites.append(node)
        return sites

    def _apply_at(self, tree, sites, idx, seed):
        target = sites[idx]
        # Replace the If node body with Pass (effectively removing the guard)
        target.body = [ast.Pass()]
        target.orelse = []


# ---------------------------------------------------------------------------
# SC-5: CONDITION_NEGATE — negate a branch condition
# ---------------------------------------------------------------------------

class ConditionNegateMutator(BaseMutator):
    mutation_type = "SC-5"
    witness_input = "input that enters the mutated branch"
    hard_negative = False

    def _collect_sites(self, tree):
        return [node for node in ast.walk(tree) if isinstance(node, ast.If)]

    def _apply_at(self, tree, sites, idx, seed):
        node = sites[idx]
        node.test = ast.UnaryOp(op=ast.Not(), operand=copy.deepcopy(node.test))


# ---------------------------------------------------------------------------
# SC-6: RETURN_MUTATION — alter a return value
# ---------------------------------------------------------------------------

class ReturnMutator(BaseMutator):
    mutation_type = "SC-6"
    witness_input = "any input that triggers the return statement"
    hard_negative = False

    def _collect_sites(self, tree):
        sites = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Return) and node.value is not None:
                if not (isinstance(node.value, ast.Constant) and node.value.value is None):
                    sites.append(node)
        return sites

    def _apply_at(self, tree, sites, idx, seed):
        node = sites[idx]
        val = node.value
        # Wrap in negation for bool, add 1 for numeric, None for others
        if isinstance(val, ast.Constant) and isinstance(val.value, int):
            node.value = ast.BinOp(left=copy.deepcopy(val), op=ast.Add(), right=ast.Constant(value=1))
        elif isinstance(val, ast.UnaryOp) and isinstance(val.op, ast.Not):
            node.value = val.operand  # double-negation removal → semantic change
        else:
            node.value = ast.UnaryOp(op=ast.Not(), operand=copy.deepcopy(val))


# ---------------------------------------------------------------------------
# SC-7: EXCEPTION_SUPPRESSION — swallow an exception handler
# ---------------------------------------------------------------------------

class ExceptionSuppressionMutator(BaseMutator):
    mutation_type = "SC-7"
    witness_input = "input that triggers the suppressed exception"
    hard_negative = True

    def _collect_sites(self, tree):
        return [node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)
                and not (len(node.body) == 1 and isinstance(node.body[0], ast.Pass))]

    def _apply_at(self, tree, sites, idx, seed):
        sites[idx].body = [ast.Pass()]


# ---------------------------------------------------------------------------
# SC-8: LOOP_BOUND_CHANGE — change loop variable init or step
# ---------------------------------------------------------------------------

class LoopBoundMutator(BaseMutator):
    mutation_type = "SC-8"
    witness_input = "any input that exercises the loop"
    hard_negative = False

    def _collect_sites(self, tree):
        sites = []
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                if isinstance(node.iter, ast.Call):
                    func = node.iter.func
                    if isinstance(func, ast.Name) and func.id == 'range':
                        sites.append(node)
        return sites

    def _apply_at(self, tree, sites, idx, seed):
        call = sites[idx].iter
        # Modify start or stop by ±1
        if len(call.args) == 1:
            # range(n) → range(1, n) skipping first iteration
            call.args = [ast.Constant(value=1), copy.deepcopy(call.args[0])]
        elif len(call.args) >= 2:
            first = call.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, int):
                first.value += 1


# ---------------------------------------------------------------------------
# SC-9: ORDERING_MUTATION — swap two adjacent statements
# ---------------------------------------------------------------------------

class OrderingMutator(BaseMutator):
    mutation_type = "SC-9"
    witness_input = "any input that reaches the swapped statements"
    hard_negative = False

    def _collect_body_pairs(self, stmts):
        """Return (parent_list, i) for adjacent pairs of Assign/Expr statements."""
        pairs = []
        for i in range(len(stmts) - 1):
            a, b = stmts[i], stmts[i + 1]
            if isinstance(a, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Expr)) and \
               isinstance(b, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Expr)):
                pairs.append((stmts, i))
        return pairs

    def _collect_sites(self, tree):
        sites = []
        for node in ast.walk(tree):
            if hasattr(node, 'body') and isinstance(node.body, list):
                sites.extend(self._collect_body_pairs(node.body))
        return sites

    def _apply_at(self, tree, sites, idx, seed):
        stmts, i = sites[idx]
        stmts[i], stmts[i + 1] = stmts[i + 1], stmts[i]


# ---------------------------------------------------------------------------
# SC-10: MISSING_UPDATE — remove a variable update inside a loop
# ---------------------------------------------------------------------------

class MissingUpdateMutator(BaseMutator):
    mutation_type = "SC-10"
    witness_input = "input with loop that runs > 1 iteration"
    hard_negative = False

    def _collect_sites(self, tree):
        """Find AugAssign (+=, -=, etc.) statements inside loops."""
        sites = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.AugAssign):
                        sites.append((node, stmt))
        return sites

    def _apply_at(self, tree, sites, idx, seed):
        loop_node, aug_assign = sites[idx]
        # Replace the augmented assignment body with just the value expression
        for node in ast.walk(loop_node):
            if hasattr(node, 'body') and aug_assign in node.body:
                i = node.body.index(aug_assign)
                node.body[i] = ast.Pass()
                break


# ---------------------------------------------------------------------------
# SC-11: WRONG_VARIABLE — substitute one variable name for another in an expr
# ---------------------------------------------------------------------------

class WrongVariableMutator(BaseMutator):
    mutation_type = "SC-11"
    witness_input = "any input where the two variables have different values"
    hard_negative = False

    def _collect_sites(self, tree):
        """Find functions with ≥2 local variables of the same type use."""
        sites = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names = [n.id for n in ast.walk(node) if isinstance(n, ast.Name)
                         and isinstance(n.ctx, ast.Load)]
                # Find pairs of distinct names that appear in loads
                from collections import Counter
                cnt = Counter(names)
                common = [n for n, c in cnt.items() if c >= 1]
                if len(common) >= 2:
                    sites.append((node, common))
        return sites

    def _apply_at(self, tree, sites, idx, seed):
        node, names = sites[idx]
        random.seed(seed)
        random.shuffle(names)
        src_name, dst_name = names[0], names[1]

        class Renamer(ast.NodeTransformer):
            def __init__(self, src, dst):
                self.src = src; self.dst = dst; self.done = False
            def visit_Name(self, n):
                if isinstance(n.ctx, ast.Load) and n.id == self.src and not self.done:
                    self.done = True
                    return ast.Name(id=self.dst, ctx=n.ctx)
                return n

        Renamer(src_name, dst_name).visit(node)


# ---------------------------------------------------------------------------
# SC-12: RESOURCE_LEAK — remove a cleanup/close call
# ---------------------------------------------------------------------------

class ResourceLeakMutator(BaseMutator):
    mutation_type = "SC-12"
    witness_input = "any execution that reaches the removed cleanup"
    hard_negative = True

    _CLEANUP_NAMES = {'close', 'cleanup', 'release', 'shutdown', 'dispose',
                      'free', 'delete', 'remove', '__exit__', 'terminate'}

    def _collect_sites(self, tree):
        sites = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                func = call.func
                name = None
                if isinstance(func, ast.Attribute) and func.attr in self._CLEANUP_NAMES:
                    name = func.attr
                elif isinstance(func, ast.Name) and func.id in self._CLEANUP_NAMES:
                    name = func.id
                if name:
                    sites.append(node)
        return sites

    def _apply_at(self, tree, sites, idx, seed):
        target = sites[idx]
        # Find parent body and replace with Pass
        for node in ast.walk(tree):
            for attr in ('body', 'orelse', 'finalbody', 'handlers'):
                body = getattr(node, attr, None)
                if body and target in body:
                    i = body.index(target)
                    body[i] = ast.Pass()
                    return
        # Also handle Try.finalbody
        for node in ast.walk(tree):
            if isinstance(node, ast.Try) and target in node.finalbody:
                i = node.finalbody.index(target)
                node.finalbody[i] = ast.Pass()
                return


# ---------------------------------------------------------------------------
# SC-13: CONDITION_REMOVAL — remove an if-check entirely, always execute body
# ---------------------------------------------------------------------------

class ConditionRemovalMutator(BaseMutator):
    mutation_type = "SC-13"
    witness_input = "input that would fail the removed condition"
    hard_negative = True

    def _collect_sites(self, tree):
        """Collect (parent_body, index, if_node) for If nodes."""
        sites = []
        for node in ast.walk(tree):
            for attr in ('body', 'orelse'):
                body = getattr(node, attr, None)
                if not isinstance(body, list):
                    continue
                for i, stmt in enumerate(body):
                    if isinstance(stmt, ast.If):
                        sites.append((body, i, stmt))
        return sites

    def _apply_at(self, tree, sites, idx, seed):
        body, i, if_node = sites[idx]
        # Replace the If with its body (always execute — remove the condition)
        body[i:i+1] = if_node.body


# ---------------------------------------------------------------------------
# SC-14: STATE_TRANSITION_ERROR — in a dict/assignment state machine, change target state
# ---------------------------------------------------------------------------

class StateTransitionMutator(BaseMutator):
    mutation_type = "SC-14"
    witness_input = "input that triggers the mutated state transition"
    hard_negative = True

    def _collect_sites(self, tree):
        """Find string constants that look like state names (ALL_CAPS or Title case in assignments)."""
        sites = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                val = node.value
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    s = val.value
                    if s.isupper() or (s.istitle() and '_' not in s):
                        sites.append(val)
            # Also dict values that are strings
            if isinstance(node, ast.Dict):
                for v in node.values:
                    if isinstance(v, ast.Constant) and isinstance(v.value, str) and v.value.isupper():
                        sites.append(v)
        return sites

    def _apply_at(self, tree, sites, idx, seed):
        node = sites[idx]
        # Collect all other string constants in the tree that look like states
        all_states = sorted(set(
            n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and (n.value.isupper() or n.value.istitle())
            and n is not node
        ))
        if all_states:
            random.seed(seed)
            node.value = random.choice(all_states)
        else:
            node.value = node.value + "_WRONG"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_MUTATORS = {
    'SC-1': OffByOneMutator,
    'SC-2': OperatorMutator,
    'SC-3': ConstantMutator,
    'SC-4': BoundaryConditionMutator,
    'SC-5': ConditionNegateMutator,
    'SC-6': ReturnMutator,
    'SC-7': ExceptionSuppressionMutator,
    'SC-8': LoopBoundMutator,
    'SC-9': OrderingMutator,
    'SC-10': MissingUpdateMutator,
    'SC-11': WrongVariableMutator,
    'SC-12': ResourceLeakMutator,
    'SC-13': ConditionRemovalMutator,
    'SC-14': StateTransitionMutator,
}


class MutatorRegistry:
    @staticmethod
    def get(mutation_type: str) -> BaseMutator:
        if mutation_type not in _MUTATORS:
            raise KeyError(f"Unknown mutation type: {mutation_type!r}. Available: {list(_MUTATORS)}")
        return _MUTATORS[mutation_type]()

    @staticmethod
    def all_types():
        return list(_MUTATORS.keys())


def apply_mutation(program_path: str, mutation_type: str, seed: int = 0,
                   site: int = 0) -> tuple:
    """
    Apply mutation_type to program_path.
    Returns (new_source: str, metadata: dict).
    metadata contains all MutantRecord fields.
    """
    with open(program_path) as f:
        source = f.read()

    mutator = MutatorRegistry.get(mutation_type)
    new_source = mutator.apply(source, seed=seed, mutation_site=site)
    applied = new_source != source

    base_id = os.path.splitext(os.path.basename(program_path))[0]
    variant_id = f"{base_id}__{mutation_type.replace('-','').lower()}_s{seed}_p{site}"

    record = MutantRecord(
        base_id=base_id,
        variant_id=variant_id,
        mutation_type=mutation_type,
        seed=seed,
        mutation_site=site,
        witness_input=mutator.witness_input,
        hard_negative=mutator.hard_negative,
        base_hash=_sha256(source),
        variant_hash=_sha256(new_source),
        timestamp=datetime.now(timezone.utc).isoformat(),
        applied=applied,
    )
    return new_source, record.to_dict()


def generate_mutant(program_path: str, mutation_type: str, seed: int = 0,
                    site: int = 0, output_dir: str = None) -> MutantRecord:
    """
    Apply mutation, optionally write variant + JSON sidecar to output_dir.
    Returns MutantRecord dataclass.
    """
    new_source, meta = apply_mutation(program_path, mutation_type, seed, site)
    record = MutantRecord(**meta)

    if output_dir and record.applied:
        os.makedirs(output_dir, exist_ok=True)
        out_py = os.path.join(output_dir, record.variant_id + ".py")
        out_json = os.path.join(output_dir, record.variant_id + ".json")
        with open(out_py, 'w') as f:
            f.write(new_source)
        with open(out_json, 'w') as f:
            f.write(record.to_json())

    return record
