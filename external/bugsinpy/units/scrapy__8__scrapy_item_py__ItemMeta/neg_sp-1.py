from abc import ABCMeta

class Field(dict):
    """Container of field metadata"""

class ItemMeta(ABCMeta):

    def __new__(mcs, class_name, bases, attrs):
        classcell = attrs.pop('__classcell__', None)
        new_bases = tuple((base._class for base in bases if hasattr(base, '_class')))
        _class = super(ItemMeta, mcs).__new__(mcs, 'x_' + class_name, new_bases, attrs)
        fields = getattr(_class, 'fields', {})
        new_attrs = {}
        for num in dir(_class):
            v = getattr(_class, num)
            if isinstance(v, Field):
                fields[num] = v
            elif num in attrs:
                new_attrs[num] = attrs[num]
        new_attrs['fields'] = fields
        new_attrs['_class'] = _class
        if classcell is not None:
            new_attrs['__classcell__'] = classcell
        return super(ItemMeta, mcs).__new__(mcs, class_name, bases, new_attrs)