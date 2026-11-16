# BugsInPy scrapy/36 | https://github.com/scrapy/scrapy | scrapy/utils/misc.py | unit create_instance
# license: BSD-3-Clause (upstream project); extracted verbatim, closure only, no edits
# commit cf9be5344a89dd8e14f8241ec69de9c984ec1e05 (fixed)
def create_instance(objcls, settings, crawler, *args, **kwargs):
    """Construct a class instance using its ``from_crawler`` or
    ``from_settings`` constructors, if available.

    At least one of ``settings`` and ``crawler`` needs to be different from
    ``None``. If ``settings `` is ``None``, ``crawler.settings`` will be used.
    If ``crawler`` is ``None``, only the ``from_settings`` constructor will be
    tried.

    ``*args`` and ``**kwargs`` are forwarded to the constructors.

    Raises ``ValueError`` if both ``settings`` and ``crawler`` are ``None``.

    Raises ``TypeError`` if the resulting instance is ``None`` (e.g. if an
    extension has not been implemented correctly).
    """
    if settings is None:
        if crawler is None:
            raise ValueError("Specify at least one of settings and crawler.")
        settings = crawler.settings
    if crawler and hasattr(objcls, 'from_crawler'):
        instance = objcls.from_crawler(crawler, *args, **kwargs)
        method_name = 'from_crawler'
    elif hasattr(objcls, 'from_settings'):
        instance = objcls.from_settings(settings, *args, **kwargs)
        method_name = 'from_settings'
    else:
        instance = objcls(*args, **kwargs)
        method_name = '__new__'
    if instance is None:
        raise TypeError("%s.%s returned None" % (objcls.__qualname__, method_name))
    return instance
