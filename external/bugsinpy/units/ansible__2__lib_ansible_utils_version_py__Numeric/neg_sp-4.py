from __future__ import absolute_import, division, print_function

class _Alpha:

    def __init__(self, specifier):
        self.specifier = specifier

    def __repr__(self):
        return repr(self.specifier)

    def __eq__(self, other):
        if isinstance(other, _Alpha):
            return self.specifier == other.specifier
        elif isinstance(other, str):
            return self.specifier == other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, _Alpha):
            return self.specifier < other.specifier
        elif isinstance(other, str):
            return self.specifier < other
        elif isinstance(other, _Numeric):
            return False
        raise ValueError

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

class _Numeric:

    def __init__(self, specifier):
        self.specifier = int(specifier)

    def __repr__(self):
        return repr(self.specifier)

    def __eq__(self, other):
        if isinstance(other, _Numeric):
            return self.specifier == other.specifier
        elif isinstance(other, int):
            return self.specifier == other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, _Numeric):
            return self.specifier < other.specifier
        elif isinstance(other, int):
            return self.specifier < other
        elif isinstance(other, _Alpha):
            return True
        raise ValueError

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)