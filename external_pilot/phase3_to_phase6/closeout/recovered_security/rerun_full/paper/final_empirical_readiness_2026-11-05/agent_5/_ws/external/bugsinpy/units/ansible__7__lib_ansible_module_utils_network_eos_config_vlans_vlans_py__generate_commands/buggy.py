# BugsInPy ansible/7 | https://github.com/ansible/ansible | lib/ansible/module_utils/network/eos/config/vlans/vlans.py | unit generate_commands
# license: GPL-3.0 (upstream project); extracted verbatim, closure only, no edits
# commit cd146b836e032df785ecd9eb711c6ef23c2228b8 (buggy)
from __future__ import absolute_import, division, print_function

def generate_commands(vlan_id, to_set, to_remove):
    commands = []
    if "vlan_id" in to_remove:
        return ["no vlan {0}".format(vlan_id)]

    for key, value in to_set.items():
        if key == "vlan_id" or value is None:
            continue

        commands.append("{0} {1}".format(key, value))

    for key in to_remove:
        commands.append("no {0}".format(key))

    if commands:
        commands.insert(0, "vlan {0}".format(vlan_id))

    return commands
