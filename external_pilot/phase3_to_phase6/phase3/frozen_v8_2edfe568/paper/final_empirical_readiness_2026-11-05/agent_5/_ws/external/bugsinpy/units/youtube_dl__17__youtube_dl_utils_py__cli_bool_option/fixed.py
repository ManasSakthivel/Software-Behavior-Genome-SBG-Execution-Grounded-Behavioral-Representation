# BugsInPy youtube-dl/17 | https://github.com/ytdl-org/youtube-dl | youtube_dl/utils.py | unit cli_bool_option
# license: Unlicense (upstream project); extracted verbatim, closure only, no edits
# commit 5b232f46dcbdc805507c02edd4fd598f31d544d5 (fixed)
from __future__ import unicode_literals

def cli_bool_option(params, command_option, param, true_value='true', false_value='false', separator=None):
    param = params.get(param)
    if param is None:
        return []
    assert isinstance(param, bool)
    if separator:
        return [command_option + separator + (true_value if param else false_value)]
    return [command_option, true_value if param else false_value]
