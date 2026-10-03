def create_instance(objcls, settings, crawler, *args, **kwargs):
    if settings is None:
        if crawler is None:
            raise ValueError('Specify at least one of settings and crawler.')
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
        raise TypeError('%s.%s returned None' % (objcls.__qualname__, method_name))
    return instance