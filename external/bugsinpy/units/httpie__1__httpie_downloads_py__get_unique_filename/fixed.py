# BugsInPy httpie/1 | https://github.com/jakubroztocil/httpie/ | httpie/downloads.py | unit get_unique_filename
# license: BSD-3-Clause (upstream project); extracted verbatim, closure only, no edits
# commit 5300b0b490b8db48fac30b5e32164be93dc574b7 (fixed)
from __future__ import division

import errno

import os

def trim_filename(filename, max_len):
    if len(filename) > max_len:
        trim_by = len(filename) - max_len
        name, ext = os.path.splitext(filename)
        if trim_by >= len(name):
            filename = filename[:-trim_by]
        else:
            filename = name[:-trim_by] + ext
    return filename

def get_filename_max_length(directory):
    try:
        max_len = os.pathconf(directory, 'PC_NAME_MAX')
    except OSError as e:
        if e.errno == errno.EINVAL:
            max_len = 255
        else:
            raise
    return max_len

def trim_filename_if_needed(filename, directory='.', extra=0):
    max_len = get_filename_max_length(directory) - extra
    if len(filename) > max_len:
        filename = trim_filename(filename, max_len)
    return filename

def get_unique_filename(filename, exists=os.path.exists):
    attempt = 0
    while True:
        suffix = '-' + str(attempt) if attempt > 0 else ''
        try_filename = trim_filename_if_needed(filename, extra=len(suffix))
        try_filename += suffix
        if not exists(try_filename):
            return try_filename
        attempt += 1
