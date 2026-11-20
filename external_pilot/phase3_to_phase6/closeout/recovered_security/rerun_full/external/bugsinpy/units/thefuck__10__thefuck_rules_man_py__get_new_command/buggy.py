# BugsInPy thefuck/10 | https://github.com/nvbn/thefuck | thefuck/rules/man.py | unit get_new_command
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit 8bd6c5da67e55c64257345efa4e3cc454c42475c (buggy)
def get_new_command(command):
    if '3' in command.script:
        return command.script.replace("3", "2")
    if '2' in command.script:
        return command.script.replace("2", "3")

    split_cmd2 = command.script_parts
    split_cmd3 = split_cmd2[:]

    split_cmd2.insert(1, ' 2 ')
    split_cmd3.insert(1, ' 3 ')

    last_arg = command.script_parts[-1]

    return [
        last_arg + ' --help',
        "".join(split_cmd3),
        "".join(split_cmd2),
    ]
