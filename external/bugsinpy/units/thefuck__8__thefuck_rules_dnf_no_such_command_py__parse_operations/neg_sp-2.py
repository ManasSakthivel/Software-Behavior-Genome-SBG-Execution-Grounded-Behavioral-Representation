import re

def fn__parse_operations(help_text_lines):
    operation_regex = re.compile('^([a-z-]+) +', re.MULTILINE)
    return operation_regex.findall(help_text_lines)