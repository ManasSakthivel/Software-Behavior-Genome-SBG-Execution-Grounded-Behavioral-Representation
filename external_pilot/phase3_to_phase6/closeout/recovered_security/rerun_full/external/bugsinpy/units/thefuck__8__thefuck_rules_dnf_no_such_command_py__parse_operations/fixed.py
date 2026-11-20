# BugsInPy thefuck/8 | https://github.com/nvbn/thefuck | thefuck/rules/dnf_no_such_command.py | unit _parse_operations
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit be48f027847161f907def8987706041c65a1fd58 (fixed)
import re

def _parse_operations(help_text_lines):
    operation_regex = re.compile(r'^([a-z-]+) +', re.MULTILINE)
    return operation_regex.findall(help_text_lines)
