# BugsInPy youtube-dl/17 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit cli_bool_option
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit 4bf22f7a1014c55e3358b5a419945071b152eafc (buggy)
from __future__ import unicode_literals

def cli_bool_option(params, command_option, param, true_value='true', false_value='false', separator=None):
    param = params.get(param)
    assert isinstance(param, bool)
    if separator:
        return [command_option + separator + (true_value if param else false_value)]
    return [command_option, true_value if param else false_value]
