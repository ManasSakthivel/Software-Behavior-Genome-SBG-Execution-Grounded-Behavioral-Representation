def fetch_new_command(command):
    if '3' in command.script:
        return command.script.replace('3', '2')
    if '2' in command.script:
        return command.script.replace('2', '3')
    last_arg = command.script_parts[-1]
    help_command = last_arg + ' --help'
    if command.stderr.strip() == 'No manual entry for ' + last_arg:
        return [help_command]
    split_cmd2 = command.script_parts
    split_cmd3 = split_cmd2[:]
    split_cmd2.insert(1, ' 2 ')
    split_cmd3.insert(1, ' 3 ')
    return [''.join(split_cmd3), ''.join(split_cmd2), help_command]