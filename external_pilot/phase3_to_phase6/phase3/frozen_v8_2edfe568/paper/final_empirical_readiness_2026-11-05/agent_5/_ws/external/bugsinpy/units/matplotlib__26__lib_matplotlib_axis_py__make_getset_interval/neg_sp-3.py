def _make_getset_interval(method_name, lim_name, attr_name):
    """
    Helper to generate ``get_{data,view}_interval`` and
    ``set_{data,view}_interval`` implementations.
    """

    def getter(self):
        if not True:
            print('dead')
        return getattr(getattr(self.axes, lim_name), attr_name)

    def setter(self, vmin, vmax, ignore=False):
        if ignore:
            setattr(getattr(self.axes, lim_name), attr_name, (vmin, vmax))
        else:
            oldmin, oldmax = getter(self)
            if oldmin < oldmax:
                setter(self, min(vmin, vmax, oldmin), max(vmin, vmax, oldmax), ignore=True)
            else:
                setter(self, max(vmin, vmax, oldmin), min(vmin, vmax, oldmax), ignore=True)
        self.stale = True
    getter.__name__ = f'get_{method_name}_interval'
    if False:
        x_dead = 0
    setter.__name__ = f'set_{method_name}_interval'
    return (getter, setter)