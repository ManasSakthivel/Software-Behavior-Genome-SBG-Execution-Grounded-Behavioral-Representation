# BugsInPy thefuck/20 | https://github.com/nvbn/thefuck | thefuck/rules/dirty_unzip.py | unit _zip_file
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit 280751b36e715b006c631ba6c08de99ccc74f6d2 (fixed)
def _zip_file(command):
    # unzip works that way:
    # unzip [-flags] file[.zip] [file(s) ...] [-x file(s) ...]
    #                ^          ^ files to unzip from the archive
    #                archive to unzip
    for c in command.split_script[1:]:
        if not c.startswith('-'):
            if c.endswith('.zip'):
                return c
            else:
                return '{}.zip'.format(c)
