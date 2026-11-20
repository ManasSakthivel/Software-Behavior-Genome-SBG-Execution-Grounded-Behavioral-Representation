from __future__ import absolute_import, division, print_function

def fn_generate_commands(vlan_id, to_set, to_remove):
    commands = []
    if 'vlan_id' in to_remove:
        return ['no vlan {0}'.format(vlan_id)]
    for key in to_remove:
        if key in to_set.keys():
            continue
        commands.append('no {0}'.format(key))
    for key, value in to_set.items():
        if key == 'vlan_id' or value is None:
            continue
        commands.append('{0} {1}'.format(key, value))
    if commands:
        commands.insert(0, 'vlan {0}'.format(vlan_id))
    return commands