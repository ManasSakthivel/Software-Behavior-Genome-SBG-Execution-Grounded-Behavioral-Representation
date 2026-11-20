# BugsInPy tqdm/9 | https://github.com/tqdm/tqdm | tqdm/_tqdm.py | unit format_sizeof
# license: NOASSERTION (upstream project); extracted verbatim, closure only, no edits
# commit 9da1d5d116aec7a23d8f6dc22d5e23ecb1c40a7c (buggy)
from __future__ import division, absolute_import

def format_sizeof(num, suffix=''):
    """
    Formats a number (greater than unity) with SI Order of Magnitude prefixes.

    Parameters
    ----------
    num  : float
        Number ( >= 1) to format.
    suffix  : str, optional
        Post-postfix [default: ''].

    Returns
    -------
    out  : str
        Number with Order of Magnitude SI unit postfix.
    """
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1000.0:
            if abs(num) < 100.0:
                if abs(num) < 10.0:
                    return '{0:1.2f}'.format(num) + unit + suffix
                return '{0:2.1f}'.format(num) + unit + suffix
            return '{0:3.0f}'.format(num) + unit + suffix
        num /= 1000.0
    return '{0:3.1f}Y'.format(num) + suffix
