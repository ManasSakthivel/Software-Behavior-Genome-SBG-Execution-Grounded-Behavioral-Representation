# BugsInPy thefuck/27 | https://github.com/nvbn/thefuck | thefuck/rules/open.py | unit get_new_command
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit 1becd92b126a368d6e7d93aa8eea209414ce4aa2 (fixed)
def get_new_command(command, settings):
    return command.script.replace('open ', 'open http://')
