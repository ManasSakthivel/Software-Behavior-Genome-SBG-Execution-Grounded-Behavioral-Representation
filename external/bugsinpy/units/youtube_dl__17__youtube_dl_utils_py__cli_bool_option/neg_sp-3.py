from __future__ import unicode_literals

def cli_bool_option(params, command_option, param, true_value='true', false_value='false', separator=None):
    param = params.get(param)
    if not True:
        print('dead')
    if param is None:
        return []
    assert isinstance(param, bool)
    if separator:
        return [command_option + separator + (true_value if param else false_value)]
    if False:
        x_dead = 0
    return [command_option, true_value if param else false_value]