"""
Tests for the SBG mutation framework (SC-1 through SC-14).
"""
import ast
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from benchmark.transformations.mutations.mutator import (
    MutatorRegistry, apply_mutation, MutantRecord,
)

# --- Simple target programs for testing ---

SORT_SOURCE = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
"""

GUARDED_SOURCE = """
def safe_div(a, b):
    if b == 0:
        return None
    return a // b
"""

EXCEPTION_SOURCE = """
def parse_num(s):
    try:
        return int(s)
    except ValueError:
        return -1
"""

STATE_SOURCE = """
STATE = 'IDLE'
def transition(event):
    global STATE
    if event == 'start':
        STATE = 'RUNNING'
    elif event == 'stop':
        STATE = 'IDLE'
    return STATE
"""

LOOP_SOURCE = """
def sum_range(n):
    total = 0
    for i in range(n):
        total += i
    return total
"""

RESOURCE_SOURCE = """
class MockFile:
    def __init__(self): self.closed = False
    def close(self): self.closed = True

def process(f):
    data = f.read() if hasattr(f, 'read') else []
    f.close()
    return data
"""


class TestMutatorRegistry(unittest.TestCase):
    def test_all_types_registered(self):
        expected = [f"SC-{i}" for i in range(1, 15)]
        for t in expected:
            self.assertIn(t, MutatorRegistry.all_types())

    def test_get_returns_instance(self):
        for t in MutatorRegistry.all_types():
            m = MutatorRegistry.get(t)
            self.assertTrue(hasattr(m, 'apply'))

    def test_unknown_type_raises(self):
        with self.assertRaises(KeyError):
            MutatorRegistry.get('SC-99')


class TestMutantRecordFields(unittest.TestCase):
    def _make_tmp_file(self, source, suffix=".py"):
        import tempfile
        f = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
        f.write(source)
        f.close()
        return f.name

    def setUp(self):
        self.tmp = self._make_tmp_file(SORT_SOURCE)

    def tearDown(self):
        os.unlink(self.tmp)

    def test_record_has_all_required_fields(self):
        _, meta = apply_mutation(self.tmp, 'SC-2', seed=42, site=0)
        required = ['base_id', 'variant_id', 'mutation_type', 'semantic_relation',
                    'generator', 'seed', 'mutation_site', 'expected_label',
                    'witness_input', 'hard_negative', 'base_hash', 'variant_hash',
                    'timestamp', 'applied']
        for field in required:
            self.assertIn(field, meta, f"Missing field: {field}")

    def test_semantic_relation_is_changed(self):
        _, meta = apply_mutation(self.tmp, 'SC-1', seed=1, site=0)
        self.assertEqual(meta['semantic_relation'], 'CHANGED')

    def test_expected_label_is_changed(self):
        _, meta = apply_mutation(self.tmp, 'SC-3', seed=1, site=0)
        self.assertEqual(meta['expected_label'], 'CHANGED')

    def test_hashes_differ_when_applied(self):
        new_src, meta = apply_mutation(self.tmp, 'SC-5', seed=0, site=0)
        if meta['applied']:
            self.assertNotEqual(meta['base_hash'], meta['variant_hash'])


class TestMutationsProduceValidPython(unittest.TestCase):
    """Every mutation must produce syntactically valid Python."""

    SOURCES = {
        'sort': SORT_SOURCE,
        'guarded': GUARDED_SOURCE,
        'exception': EXCEPTION_SOURCE,
        'state': STATE_SOURCE,
        'loop': LOOP_SOURCE,
        'resource': RESOURCE_SOURCE,
    }

    def _check_valid(self, source_name, mutation_type, seed=0, site=0):
        import tempfile
        src = self.SOURCES[source_name]
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        f.write(src); f.close()
        try:
            new_src, meta = apply_mutation(f.name, mutation_type, seed=seed, site=site)
            try:
                compile(new_src, "<test>", "exec")
            except SyntaxError as e:
                self.fail(f"{mutation_type} on {source_name} produced invalid Python: {e}\n{new_src}")
        finally:
            os.unlink(f.name)

    def test_sc1_valid(self):
        self._check_valid('loop', 'SC-1')

    def test_sc2_valid(self):
        self._check_valid('sort', 'SC-2')

    def test_sc3_valid(self):
        self._check_valid('sort', 'SC-3')

    def test_sc4_valid(self):
        self._check_valid('guarded', 'SC-4')

    def test_sc5_valid(self):
        self._check_valid('guarded', 'SC-5')

    def test_sc6_valid(self):
        self._check_valid('guarded', 'SC-6')

    def test_sc7_valid(self):
        self._check_valid('exception', 'SC-7')

    def test_sc8_valid(self):
        self._check_valid('loop', 'SC-8')

    def test_sc9_valid(self):
        self._check_valid('sort', 'SC-9')

    def test_sc10_valid(self):
        self._check_valid('loop', 'SC-10')

    def test_sc11_valid(self):
        self._check_valid('sort', 'SC-11')

    def test_sc12_valid(self):
        self._check_valid('resource', 'SC-12')

    def test_sc13_valid(self):
        self._check_valid('guarded', 'SC-13')

    def test_sc14_valid(self):
        self._check_valid('state', 'SC-14')


class TestMutationsActuallyChange(unittest.TestCase):
    """At least some mutations must actually change the source (not all no-ops)."""

    def _mutates(self, source_code, mutation_type, seeds=range(5)):
        import tempfile
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        f.write(source_code); f.close()
        try:
            for seed in seeds:
                new_src, meta = apply_mutation(f.name, mutation_type, seed=seed, site=0)
                if meta['applied']:
                    return True
            return False
        finally:
            os.unlink(f.name)

    def test_sc1_changes_loop(self):
        self.assertTrue(self._mutates(LOOP_SOURCE, 'SC-1'))

    def test_sc2_changes_sort(self):
        self.assertTrue(self._mutates(SORT_SOURCE, 'SC-2'))

    def test_sc5_changes_guard(self):
        self.assertTrue(self._mutates(GUARDED_SOURCE, 'SC-5'))

    def test_sc7_changes_exception(self):
        self.assertTrue(self._mutates(EXCEPTION_SOURCE, 'SC-7'))

    def test_sc14_changes_state(self):
        self.assertTrue(self._mutates(STATE_SOURCE, 'SC-14'))


class TestDifferentialBehavior(unittest.TestCase):
    """Confirm that SC-1 and SC-5 actually diverge on witness inputs."""

    def test_sc1_off_by_one_diverges(self):
        import tempfile
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        f.write(LOOP_SOURCE); f.close()
        try:
            new_src, meta = apply_mutation(f.name, 'SC-1', seed=0, site=0)
        finally:
            os.unlink(f.name)
        if not meta['applied']:
            self.skipTest("SC-1 found no site in LOOP_SOURCE")
        # Execute original vs mutant
        orig_ns = {}; exec(LOOP_SOURCE, orig_ns)
        mut_ns = {}; exec(new_src, mut_ns)
        orig_fn = orig_ns['sum_range']
        mut_fn = mut_ns['sum_range']
        # They should differ for at least one value
        diverged = any(orig_fn(n) != mut_fn(n) for n in range(2, 10))
        self.assertTrue(diverged, f"SC-1 did not diverge. Mutated source:\n{new_src}")

    def test_sc5_negation_diverges(self):
        import tempfile
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        f.write(GUARDED_SOURCE); f.close()
        try:
            new_src, meta = apply_mutation(f.name, 'SC-5', seed=0, site=0)
        finally:
            os.unlink(f.name)
        if not meta['applied']:
            self.skipTest("SC-5 found no site")
        orig_ns = {}; exec(GUARDED_SOURCE, orig_ns)
        mut_ns = {}; exec(new_src, mut_ns)
        orig_fn = orig_ns['safe_div']
        mut_fn = mut_ns['safe_div']
        pairs = [(4, 2), (9, 3), (6, 0), (10, 5)]
        diverged = False
        for a, b in pairs:
            try:
                r1 = orig_fn(a, b)
            except Exception:
                r1 = "__exc__"
            try:
                r2 = mut_fn(a, b)
            except Exception:
                r2 = "__exc__"
            if r1 != r2:
                diverged = True
                break
        self.assertTrue(diverged, f"SC-5 did not diverge on test pairs.\nMutated:\n{new_src}")


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_result(self):
        import tempfile
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        f.write(SORT_SOURCE); f.close()
        try:
            src1, _ = apply_mutation(f.name, 'SC-2', seed=7, site=0)
            src2, _ = apply_mutation(f.name, 'SC-2', seed=7, site=0)
            self.assertEqual(src1, src2)
        finally:
            os.unlink(f.name)

    def test_different_seeds_may_differ(self):
        import tempfile
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        f.write(SORT_SOURCE); f.close()
        try:
            src1, _ = apply_mutation(f.name, 'SC-3', seed=0, site=0)
            src2, _ = apply_mutation(f.name, 'SC-3', seed=99, site=0)
            # Not required to differ, but they can — just must both be valid
            compile(src1, "<>", "exec")
            compile(src2, "<>", "exec")
        finally:
            os.unlink(f.name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
