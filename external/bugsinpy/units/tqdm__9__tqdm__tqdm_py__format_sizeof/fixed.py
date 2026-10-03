# BugsInPy tqdm/9 | https://github.com/tqdm/tqdm | tqdm/_tqdm.py | unit format_sizeof
# license: NOASSERTION (upstream project); extracted verbatim, closure only, no edits
# commit d877c1dfb4739852105f7b967a8fceb869ac5042 (fixed)
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
        if abs(num) < 999.95:
            if abs(num) < 99.95:
                if abs(num) < 9.995:
                    return '{0:1.2f}'.format(num) + unit + suffix
                return '{0:2.1f}'.format(num) + unit + suffix
            return '{0:3.0f}'.format(num) + unit + suffix
        num /= 1000.0
    return '{0:3.1f}Y'.format(num) + suffix
