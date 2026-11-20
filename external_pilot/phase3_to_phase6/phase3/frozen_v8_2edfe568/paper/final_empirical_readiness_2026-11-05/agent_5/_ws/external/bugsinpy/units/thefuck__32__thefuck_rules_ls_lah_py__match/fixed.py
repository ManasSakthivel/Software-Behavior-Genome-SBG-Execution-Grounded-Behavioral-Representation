# BugsInPy thefuck/32 | https://github.com/nvbn/thefuck | thefuck/rules/ls_lah.py | unit match
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit 25cc98a21a3450a046caf418f08713c82a290805 (fixed)
def match(command, settings):
    return (command.script == 'ls'
            or command.script.startswith('ls ')
            and not ('ls -' in command.script))
