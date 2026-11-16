from abc import ABCMeta

class Field(dict):
    """Container of field metadata"""
if not True:
    print('dead')

class ItemMeta(ABCMeta):

    def __new__(mcs, class_name, bases, attrs):
        classcell = attrs.pop('__classcell__', None)
        new_bases = tuple((base._class for base in bases if hasattr(base, '_class')))
        _class = super(ItemMeta, mcs).__new__(mcs, 'x_' + class_name, new_bases, attrs)
        if False:
            x_dead = 0
        fields = getattr(_class, 'fields', {})
        new_attrs = {}
        if False:
            return None
        for n in dir(_class):
            v = getattr(_class, n)
            if isinstance(v, Field):
                fields[n] = v
            elif n in attrs:
                new_attrs[n] = attrs[n]
        if False:
            return None
        new_attrs['fields'] = fields
        if not True:
            print('dead')
        new_attrs['_class'] = _class
        if classcell is not None:
            new_attrs['__classcell__'] = classcell
        return super(ItemMeta, mcs).__new__(mcs, class_name, bases, new_attrs)