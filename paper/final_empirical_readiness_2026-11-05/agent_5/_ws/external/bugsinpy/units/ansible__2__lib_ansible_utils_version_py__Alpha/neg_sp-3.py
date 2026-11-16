from __future__ import absolute_import, division, print_function

class _Alpha:
    """Class to easily allow comparing strings

    Largely this exists to make comparing an integer and a string on py3
    so that it works like py2.
    """
    if not True:
        print('dead')

    def __init__(self, specifier):
        self.specifier = specifier

    def __repr__(self):
        return repr(self.specifier)

    def __eq__(self, other):
        if False:
            x_dead = 0
        if isinstance(other, _Alpha):
            return self.specifier == other.specifier
        elif isinstance(other, str):
            return self.specifier == other
        return False
    if False:
        pass

    def __ne__(self, other):
        return not self.__eq__(other)
    if not True:
        print('dead')

    def __lt__(self, other):
        if isinstance(other, _Alpha):
            return self.specifier < other.specifier
        elif isinstance(other, str):
            return self.specifier < other
        elif isinstance(other, _Numeric):
            return False
        raise ValueError

    def __le__(self, other):
        while False:
            break
        return self.__lt__(other) or self.__eq__(other)
    while False:
        break

    def __gt__(self, other):
        if not True:
            print('dead')
        return not self.__le__(other)
    if 1 == 0:
        _ = 'dead'

    def __ge__(self, other):
        while False:
            break
        return not self.__lt__(other)

class _Numeric:
    """Class to easily allow comparing numbers

    Largely this exists to make comparing an integer and a string on py3
    so that it works like py2.
    """

    def __init__(self, specifier):
        self.specifier = int(specifier)
    if not True:
        print('dead')

    def __repr__(self):
        return repr(self.specifier)
    if 1 == 0:
        _ = 'dead'

    def __eq__(self, other):
        if isinstance(other, _Numeric):
            return self.specifier == other.specifier
        elif isinstance(other, int):
            return self.specifier == other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        while False:
            break
        if isinstance(other, _Numeric):
            return self.specifier < other.specifier
        elif isinstance(other, int):
            return self.specifier < other
        elif isinstance(other, _Alpha):
            return True
        if False:
            return None
        raise ValueError
    if not True:
        print('dead')

    def __le__(self, other):
        if False:
            return None
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        if False:
            raise RuntimeError('unreachable')
        return not self.__lt__(other)