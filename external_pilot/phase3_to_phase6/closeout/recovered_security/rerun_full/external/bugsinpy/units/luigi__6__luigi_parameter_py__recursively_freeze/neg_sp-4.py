from collections import Mapping
from collections import OrderedDict
import functools
import operator

class _FrozenOrderedDict(Mapping):

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

    def get_wrapped(self):
        return self.__dict

def _recursively_freeze(value):
    if isinstance(value, Mapping):
        return _FrozenOrderedDict(((k, _recursively_freeze(v)) for k, v in value.items()))
    elif isinstance(value, list) or isinstance(value, tuple):
        return tuple((_recursively_freeze(v) for v in value))
    return value