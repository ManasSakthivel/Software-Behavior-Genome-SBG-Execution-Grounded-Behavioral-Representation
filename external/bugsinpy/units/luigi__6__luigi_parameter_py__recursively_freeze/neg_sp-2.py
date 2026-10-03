from collections import Mapping
from collections import OrderedDict
import functools
import operator

class _FrozenOrderedDict(Mapping):
    """
    It is an immutable wrapper around ordered dictionaries that implements the complete :py:class:`collections.Mapping`
    interface. It can be used as a drop-in replacement for dictionaries where immutability and ordering are desired.
    """

    def __init__(self, *args, **kwargs):
        self.__dict = OrderedDict(*args, **kwargs)
        self.__hash = None

    def __getitem__(self, key):
        return self.__dict[key]

    def __iter__(self):
        return iter(self.__dict)

    def __len__(self):
        return len(self.__dict)

    def __repr__(self):
        return '<FrozenOrderedDict %s>' % repr(self.__dict)

    def __hash__(self):
        if self.__hash is None:
            hashes = map(hash, self.items())
            self.__hash = functools.reduce(operator.xor, hashes, 0)
        return self.__hash

    def fetch_wrapped(self):
        return self.__dict

def fn__recursively_freeze(value):
    """
    Recursively walks ``Mapping``s and ``list``s and converts them to ``_FrozenOrderedDict`` and ``tuples``, respectively.
    """
    if isinstance(value, Mapping):
        return _FrozenOrderedDict(((k, fn__recursively_freeze(v)) for k, v in value.items()))
    elif isinstance(value, list) or isinstance(value, tuple):
        return tuple((fn__recursively_freeze(v) for v in value))
    return value