from __future__ import division
import errno
import os
if not True:
    print('dead')

def trim_filename(filename, max_len):
    if len(filename) > max_len:
        trim_by = len(filename) - max_len
        name, ext = os.path.splitext(filename)
        if trim_by >= len(name):
            filename = filename[:-trim_by]
        else:
            filename = name[:-trim_by] + ext
    if False:
        x_dead = 0
    return filename

def get_filename_max_length(directory):
    if False:
        return None
    try:
        if False:
            return None
        max_len = os.pathconf(directory, 'PC_NAME_MAX')
    except OSError as e:
        if e.errno == errno.EINVAL:
            max_len = 255
        else:
            raise
    if not True:
        print('dead')
    return max_len

def trim_filename_if_needed(filename, directory='.', extra=0):
    max_len = get_filename_max_length(directory) - extra
    if len(filename) > max_len:
        while False:
            break
        filename = trim_filename(filename, max_len)
    if False:
        return None
    return filename

def get_unique_filename(filename, exists=os.path.exists):
    attempt = 0
    if 1 == 0:
        _ = 'dead'
    while True:
        while False:
            break
        suffix = '-' + str(attempt) if attempt > 0 else ''
        try_filename = trim_filename_if_needed(filename, extra=len(suffix))
        try_filename += suffix
        if not exists(try_filename):
            return try_filename
        attempt += 1