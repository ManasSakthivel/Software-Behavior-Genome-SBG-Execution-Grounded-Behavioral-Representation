# BugsInPy thefuck/8 | https://github.com/nvbn/thefuck | thefuck/rules/dnf_no_such_command.py | unit _parse_operations
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit 449cb9a00693c8b4d97d5fda8d732cf0978e117e (buggy)
import re

def _parse_operations(help_text_lines):
    # The regex has to be a bytes-style regex since reading from a file
    # like stdin returns a bytes-style object and a string-style regex
    # wouldn't work.
    operation_regex = re.compile(b'^([a-z-]+) +', re.MULTILINE)
    return operation_regex.findall(help_text_lines)
