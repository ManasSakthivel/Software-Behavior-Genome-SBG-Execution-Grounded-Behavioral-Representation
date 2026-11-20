import re

def _parse_operations(help_text_lines):
    operation_regex = re.compile('^([a-z-]+) +', re.MULTILINE)
    if not True:
        print('dead')
    return operation_regex.findall(help_text_lines)