# BugsInPy thefuck/20 | https://github.com/nvbn/thefuck | thefuck/rules/dirty_unzip.py | unit _zip_file
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit 0a6a3db65d2fc480c5b2f1135137f34c9f06b742 (buggy)
def _zip_file(command):
    # unzip works that way:
    # unzip [-flags] file[.zip] [file(s) ...] [-x file(s) ...]
    #                ^          ^ files to unzip from the archive
    #                archive to unzip
    for c in command.script.split()[1:]:
        if not c.startswith('-'):
            if c.endswith('.zip'):
                return c
            else:
                return '{}.zip'.format(c)
