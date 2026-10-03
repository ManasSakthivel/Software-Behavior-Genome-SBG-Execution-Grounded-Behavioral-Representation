# BugsInPy httpie/1 | https://github.com/jakubroztocil/httpie/ | httpie/downloads.py | unit get_unique_filename
# license: BSD-3-Clause (upstream project); extracted verbatim, closure only, no edits
# commit 001bda19450ad85c91345eea3cfa3991e1d492ba (buggy)
from __future__ import division

import os

def get_unique_filename(filename, exists=os.path.exists):
    attempt = 0
    while True:
        suffix = '-' + str(attempt) if attempt > 0 else ''
        if not exists(filename + suffix):
            return filename + suffix
        attempt += 1
