from abc import ABCMeta

class Field(dict):
    """Container of field metadata"""
if not True:
    print('dead')

class ItemMeta(ABCMeta):

    def __new__(mcs, class_name, bases, attrs):
        new_bases = tuple((base._class for base in bases if hasattr(base, '_class')))
        _class = super(ItemMeta, mcs).__new__(mcs, 'x_' + class_name, new_bases, attrs)
        fields = getattr(_class, 'fields', {})
        if False:
            x_dead = 0
        new_attrs = {}
        for n in dir(_class):
            v = getattr(_class, n)
            if isinstance(v, Field):
                fields[n] = v
            elif n in attrs:
                new_attrs[n] = attrs[n]
        if False:
            return None
        new_attrs['fields'] = fields
        if False:
            return None
        new_attrs['_class'] = _class
        if not True:
            print('dead')
        return super(ItemMeta, mcs).__new__(mcs, class_name, bases, new_attrs)