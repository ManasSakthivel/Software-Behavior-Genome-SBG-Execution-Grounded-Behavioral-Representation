"""D-01 regression: harness canonicalisation must preserve contents of dict/list subclasses, namedtuples, dataclass-like
objects and __slots__ objects, never run user code while reading them, and degrade to lossy (no S2) when not observable."""
import pytest

from .test_core import go, BASE, EQV, capabilities  # noqa: F401  (skip marker lives in test_core)

pytestmark = pytest.mark.skipif(capabilities()["network_denial"]["state"] != "ACTIVE", reason="isolation not enforced here")

CASES = {
    "ordereddict": "from collections import OrderedDict\ndef f(x):\n    return OrderedDict(a={V})\n",
    "dictsub": "class D(dict): pass\ndef f(x):\n    return D(a={V})\n",
    "defaultdict": "from collections import defaultdict\ndef f(x):\n    return defaultdict(list, a=[{V}])\n",
    "counter": "from collections import Counter\ndef f(x):\n    return Counter(a={V})\n",
    "deque": "from collections import deque\ndef f(x):\n    return deque([{V}])\n",
    "listsub": "class L(list): pass\ndef f(x):\n    return L([{V}])\n",
    "setsub": "class S(set): pass\ndef f(x):\n    return S([{V}])\n",
    "namedtuple": "from collections import namedtuple\nP = namedtuple('P', 'a')\ndef f(x):\n    return P({V})\n",
    "dataclass": "from dataclasses import dataclass\n@dataclass\nclass C:\n    a: int\ndef f(x):\n    return C({V})\n",
    "dict_obj": "class C: pass\ndef f(x):\n    c = C(); c.a = {V}\n    return c\n",
    "slots": "class C:\n    __slots__ = ('a',)\ndef f(x):\n    c = C(); c.a = {V}\n    return c\n",
    "slots_multi": "class C:\n    __slots__ = ('a', 'b')\ndef f(x):\n    c = C(); c.a = 1; c.b = {V}\n    return c\n",
    "slots_inherited": "class B:\n    __slots__ = ('a',)\nclass C(B):\n    __slots__ = ('b',)\ndef f(x):\n    c = C(); c.b = 0; c.a = {V}\n    return c\n",
    "slots_and_dict": "class B:\n    __slots__ = ('a',)\nclass C(B): pass\ndef f(x):\n    c = C(); c.a = 0; c.z = {V}\n    return c\n",
    "intsub": "class I(int): pass\ndef f(x):\n    return I({V})\n",
    "nested": "from collections import OrderedDict\ndef f(x):\n    return [{'k': (OrderedDict(a=[{V}]),)}]\n",
    "cyclic": "def f(x):\n    a = [{V}]; a.append(a)\n    return a\n",
}


@pytest.mark.parametrize("name", sorted(CASES))
def test_contents_difference_is_divergent(tmp_path, name):
    o = go(tmp_path, CASES[name].replace("{V}", "1"), CASES[name].replace("{V}", "2"), [[1]])
    assert o["verdict"] == "DIVERGENT_OBSERVABLE", o


def test_equal_contents_of_all_supported_types_reach_s2(tmp_path):
    rich = ("from collections import OrderedDict, defaultdict, Counter, deque, namedtuple\nfrom dataclasses import dataclass\n"
            "P = namedtuple('P', 'a b')\n@dataclass\nclass C:\n    a: int\nclass B:\n    __slots__ = ('a',)\nclass S(B):\n    __slots__ = ('b',)\n"
            "def f(x):\n    s = S(); s.a = 1; s.b = [2]\n    cyc = [1]; cyc.append(cyc)\n"
            "    if x > 1:\n        return [OrderedDict(a=1), defaultdict(list, a=[1]), Counter('aab'), deque([1, 2]), P(1, 2), C(3), s, cyc]\n"
            "    return [OrderedDict(a=1), defaultdict(list, a=[1]), Counter('aab'), deque([1, 2]), P(1, 2), C(3), s, cyc]\n")
    o = go(tmp_path, rich, rich.replace("x > 1", "x >= 2"), [[5], [0]])
    assert (o["verdict"], o["level"]) == ("NO_DIVERGENCE_OBSERVED", "S2"), o


@pytest.mark.parametrize("ret", [
    "(lambda: 1)", "iter([1])", "[[[[[[[[1]]]]]]]]*0 or object()",  # opaque callables / iterators / bare builtin objects
    "list(range(6000))",                                            # size cap
    "N(N(N(N(N()))))",                                              # depth cap (objects)
], ids=["lambda", "iterator", "object", "big", "deep"])
def test_unobservable_is_lossy_never_s2(tmp_path, ret):
    src = ("class N:\n    def __init__(self, n=None): self.n = n\n"
           "def f(x):\n    if x > 1:\n        return " + ret + "\n    return " + ret + "\n")
    o = go(tmp_path, src, src.replace("x > 1", "x >= 2"), [[5], [0]])
    assert not (o["verdict"] == "NO_DIVERGENCE_OBSERVED" and o["level"] == "S2"), o


def test_canonicalisation_runs_no_user_code(tmp_path):
    evil = ("import os\nclass E:\n    __slots__ = ('a',)\n    @property\n    def p(self): os._exit(3)\n"
            "    def __getattr__(self, n): os._exit(4)\n    def __repr__(self): os._exit(5)\n    def __eq__(self, o): os._exit(6)\n"
            "    def __getattribute__(self, n): os._exit(7)\n"
            "class L(list):\n    def __iter__(self): os._exit(8)\n    def __len__(self): os._exit(9)\n"
            "class D(dict):\n    def items(self): os._exit(10)\n    def keys(self): os._exit(11)\n    def __iter__(self): os._exit(12)\n"
            "def f(x):\n    e = E(); E.a.__set__(e, 1)\n    return [e, L([1]), D(a=1)]\n")
    # a user hook that exited would make both sides look like the same crash; contents differing proves the values were read
    o = go(tmp_path, evil, evil.replace("D(a=1)", "D(a=2)"), [[1]])
    assert o["verdict"] == "DIVERGENT_OBSERVABLE", o
