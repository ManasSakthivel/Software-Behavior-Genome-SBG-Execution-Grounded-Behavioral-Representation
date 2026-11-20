# BugsInPy thefuck/27 | https://github.com/nvbn/thefuck | thefuck/rules/open.py | unit get_new_command
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit bc6b107066d3f1e60b4cfcaa8cf6399e98cf1b1c (buggy)
def get_new_command(command, settings):
    return 'open http://' + command.script[5:]
