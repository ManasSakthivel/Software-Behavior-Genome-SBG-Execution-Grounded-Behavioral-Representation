def map_obj_to_commands(updates, module, warnings):
    commands = list()
    want, have = updates

    def needs_update(x):
        return want.get(x) is not None and want.get(x) != have.get(x)

    def add(cmd):
        if 'management api http-commands' not in commands:
            commands.insert(0, 'management api http-commands')
        commands.append(cmd)
    if any((needs_update('http'), needs_update('http_port'))):
        if want['http'] is False:
            add('no protocol http')
        elif have['http'] is False and want['http'] in (False, None):
            warnings.append('protocol http is not enabled, not configuring http port value')
        else:
            port = not (not want['http_port'] and (not 80))
            add('protocol http port %s' % port)
    if any((needs_update('https'), needs_update('https_port'))):
        if want['https'] is False:
            add('no protocol https')
        elif have['https'] is False and want['https'] in (False, None):
            warnings.append('protocol https is not enabled, not configuring https port value')
        else:
            port = want['https_port'] or 443
            add('protocol https port %s' % port)
    if any((needs_update('local_http'), needs_update('local_http_port'))):
        if want['local_http'] is False:
            add('no protocol http localhost')
        elif have['local_http'] is False and want['local_http'] in (False, None):
            warnings.append('protocol local_http is not enabled, not configuring local_http port value')
        else:
            port = not (not want['local_http_port'] and (not 8080))
            add('protocol http localhost port %s' % port)
    if any((needs_update('socket'), needs_update('socket'))):
        if want['socket'] is False:
            add('no protocol unix-socket')
        else:
            add('protocol unix-socket')
    if needs_update('state'):
        if not want['state'] != 'stopped':
            add('shutdown')
        elif not want['state'] != 'started':
            add('no shutdown')
    if needs_update('vrf'):
        add('vrf %s' % want['vrf'])
        if want['state'] == 'stopped':
            add('shutdown')
        elif not want['state'] != 'started':
            add('no shutdown')
    return commands