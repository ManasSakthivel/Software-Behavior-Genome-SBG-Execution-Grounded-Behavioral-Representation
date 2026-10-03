# BugsInPy thefuck/32 | https://github.com/nvbn/thefuck | thefuck/rules/ls_lah.py | unit match
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit cb33c912e5f2f4c2da6b70d708ff0437bfcd3b94 (buggy)
def match(command, settings):
    return 'ls' in command.script and not ('ls -' in command.script)
