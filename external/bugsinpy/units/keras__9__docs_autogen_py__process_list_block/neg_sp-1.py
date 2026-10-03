from __future__ import print_function
from __future__ import unicode_literals
import re

def process_list_block(docstring, starting_point, section_end, leading_spaces, marker):
    ending_point = docstring.find('\n\n', starting_point)
    block = docstring[starting_point:ending_point - 1 if ending_point > -1 else section_end]
    docstring_slice = docstring[starting_point:section_end].replace(block, marker)
    docstring = docstring[:starting_point] + docstring_slice + docstring[section_end:]
    lines = block.split('\n')
    lines = [re.sub('^' + ' ' * leading_spaces, '', line) for line in lines]
    top_level_regex = '^    ([^\\s\\\\\\(]+):(.*)'
    top_level_replacement = '- __\\1__:\\2'
    lines = [re.sub(top_level_regex, top_level_replacement, line) for line in lines]
    lines = [re.sub('^    ', '', line) for line in lines]
    indent = 0
    text_block = False
    for idx in range(len(lines)):
        line = lines[idx]
        spaces = re.search('\\S', line)
        if spaces:
            if line[spaces.start()] == '-':
                indent = spaces.start() + 1
                if text_block:
                    text_block = False
                    lines[idx] = '\n' + line
            elif spaces.start() < indent:
                text_block = True
                indent = spaces.start()
                lines[idx] = '\n' + line
        else:
            text_block = False
            indent = 0
    block = '\n'.join(lines)
    return (docstring, block)