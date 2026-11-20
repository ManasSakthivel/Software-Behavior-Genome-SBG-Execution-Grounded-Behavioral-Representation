# BugsInPy scrapy/8 | https://github.com/scrapy/scrapy | scrapy/item.py | unit ItemMeta
# license: BSD-3-Clause (upstream project); extracted verbatim, closure only, no edits
# commit f2f9350c47db73bdfb60773601b59b0633e1595a (buggy)
from abc import ABCMeta

class Field(dict):
    """Container of field metadata"""

class ItemMeta(ABCMeta):

    def __new__(mcs, class_name, bases, attrs):
        new_bases = tuple(base._class for base in bases if hasattr(base, '_class'))
        _class = super(ItemMeta, mcs).__new__(mcs, 'x_' + class_name, new_bases, attrs)

        fields = getattr(_class, 'fields', {})
        new_attrs = {}
        for n in dir(_class):
            v = getattr(_class, n)
            if isinstance(v, Field):
                fields[n] = v
            elif n in attrs:
                new_attrs[n] = attrs[n]

        new_attrs['fields'] = fields
        new_attrs['_class'] = _class
        return super(ItemMeta, mcs).__new__(mcs, class_name, bases, new_attrs)
