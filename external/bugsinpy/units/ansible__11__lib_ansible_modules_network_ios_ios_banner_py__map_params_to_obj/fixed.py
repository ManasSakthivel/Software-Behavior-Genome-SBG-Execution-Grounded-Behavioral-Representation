# BugsInPy ansible/11 | https://github.com/ansible/ansible | lib/ansible/modules/network/ios/ios_banner.py | unit map_params_to_obj
# license: GPL-3.0 (upstream project); extracted verbatim, closure only, no edits
# commit 52f3ce8a808f943561803bd664e695fed1841fe8 (fixed)
def map_params_to_obj(module):
    text = module.params['text']
    return {
        'banner': module.params['banner'],
        'text': text,
        'state': module.params['state']
    }
