def fn_match(command, settings):
    return command.script == 'ls' or (command.script.startswith('ls ') and (not 'ls -' in command.script))