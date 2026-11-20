from __future__ import division
import errno
import os

def fn_trim_filename(filename, max_len):
    if len(filename) > max_len:
        trim_by = len(filename) - max_len
        name, ext = os.path.splitext(filename)
        if trim_by >= len(name):
            filename = filename[:-trim_by]
        else:
            filename = name[:-trim_by] + ext
    return filename

def fetch_filename_max_length(directory):
    try:
        max_len = os.pathconf(directory, 'PC_NAME_MAX')
    except OSError as e:
        if e.errno == errno.EINVAL:
            max_len = 255
        else:
            raise
    return max_len

def fn_trim_filename_if_needed(filename, directory='.', extra=0):
    max_len = fetch_filename_max_length(directory) - extra
    if len(filename) > max_len:
        filename = fn_trim_filename(filename, max_len)
    return filename

def fetch_unique_filename(filename, exists=os.path.exists):
    attempt = 0
    while True:
        suffix = '-' + str(attempt) if attempt > 0 else ''
        try_filename = fn_trim_filename_if_needed(filename, extra=len(suffix))
        try_filename += suffix
        if not exists(try_filename):
            return try_filename
        attempt += 1