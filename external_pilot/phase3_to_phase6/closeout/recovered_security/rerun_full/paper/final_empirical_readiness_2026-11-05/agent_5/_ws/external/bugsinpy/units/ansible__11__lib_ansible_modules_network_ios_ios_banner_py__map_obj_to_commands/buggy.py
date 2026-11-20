# BugsInPy ansible/11 | https://github.com/ansible/ansible | lib/ansible/modules/network/ios/ios_banner.py | unit map_obj_to_commands
# license: GPL-3.0 (upstream project); extracted verbatim, closure only, no edits
# commit da07b98b7a433493728ddb7ac7efbd20b8988776 (buggy)
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
            banner_cmd += want['text'].strip()
            banner_cmd += '\n@'
            commands.append(banner_cmd)

    return commands
