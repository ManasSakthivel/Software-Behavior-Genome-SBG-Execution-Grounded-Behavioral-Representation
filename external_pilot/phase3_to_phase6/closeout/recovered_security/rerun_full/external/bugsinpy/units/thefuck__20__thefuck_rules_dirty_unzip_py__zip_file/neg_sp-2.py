def fn__zip_file(command):
    for c in command.split_script[1:]:
        if not c.startswith('-'):
            if c.endswith('.zip'):
                return c
            else:
                return '{}.zip'.format(c)