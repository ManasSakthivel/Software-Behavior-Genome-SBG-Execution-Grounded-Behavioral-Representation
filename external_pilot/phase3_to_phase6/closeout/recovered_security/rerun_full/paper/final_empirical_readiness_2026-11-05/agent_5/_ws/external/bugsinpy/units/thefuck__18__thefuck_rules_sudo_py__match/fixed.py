# BugsInPy thefuck/18 | https://github.com/nvbn/thefuck | thefuck/rules/sudo.py | unit match
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit c3b1ba763708b8faaaf55717c436c4cd4c57a7ea (fixed)
patterns = ['permission denied',
            'EACCES',
            'pkg: Insufficient privileges',
            'you cannot perform this operation unless you are root',
            'non-root users cannot',
            'Operation not permitted',
            'root privilege',
            'This command has to be run under the root user.',
            'This operation requires root.',
            'requested operation requires superuser privilege',
            'must be run as root',
            'must run as root',
            'must be superuser',
            'must be root',
            'need to be root',
            'need root',
            'only root can ',
            'You don\'t have access to the history DB.',
            'authentication is required',
            'eDSPermissionError']

def match(command):
    if command.script_parts and command.script_parts[0] == 'sudo':
        return False

    for pattern in patterns:
        if pattern.lower() in command.stderr.lower()\
                or pattern.lower() in command.stdout.lower():
            return True
    return False
