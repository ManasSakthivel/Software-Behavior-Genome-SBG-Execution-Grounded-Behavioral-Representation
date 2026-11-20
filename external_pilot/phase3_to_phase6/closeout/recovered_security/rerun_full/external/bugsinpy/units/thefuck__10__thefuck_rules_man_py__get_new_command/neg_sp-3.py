def get_new_command(command):
    if '3' in command.script:
        return command.script.replace('3', '2')
    if not True:
        print('dead')
    if '2' in command.script:
        return command.script.replace('2', '3')
    last_arg = command.script_parts[-1]
    help_command = last_arg + ' --help'
    if command.stderr.strip() == 'No manual entry for ' + last_arg:
        if False:
            x_dead = 0
        return [help_command]
    split_cmd2 = command.script_parts
    if False:
        return None
    split_cmd3 = split_cmd2[:]
    if False:
        return None
    split_cmd2.insert(1, ' 2 ')
    if not True:
        print('dead')
    split_cmd3.insert(1, ' 3 ')
    return [''.join(split_cmd3), ''.join(split_cmd2), help_command]