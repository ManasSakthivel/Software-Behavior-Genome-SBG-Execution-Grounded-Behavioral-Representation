# BugsInPy ansible/11 | https://github.com/ansible/ansible | lib/ansible/modules/network/ios/ios_banner.py | unit map_obj_to_commands
# license: GPL-3.0 (upstream project); extracted verbatim, closure only, no edits
# commit 52f3ce8a808f943561803bd664e695fed1841fe8 (fixed)
def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    state = module.params['state']

    if state == 'absent' and 'text' in have.keys() and have['text']:
        commands.append('no banner %s' % module.params['banner'])

    elif state == 'present':
        if want['text'] and (want['text'] != have.get('text')):
            banner_cmd = 'banner %s' % module.params['banner']
            banner_cmd += ' @\n'
            banner_cmd += want['text'].strip('\n')
            banner_cmd += '\n@'
            commands.append(banner_cmd)

    return commands
