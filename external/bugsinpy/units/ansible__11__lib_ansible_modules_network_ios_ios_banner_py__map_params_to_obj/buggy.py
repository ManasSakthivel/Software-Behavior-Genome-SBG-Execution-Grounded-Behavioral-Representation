# BugsInPy ansible/11 | https://github.com/ansible/ansible | lib/ansible/modules/network/ios/ios_banner.py | unit map_params_to_obj
# license: GPL-3.0 (upstream project); extracted verbatim, closure only, no edits
# commit da07b98b7a433493728ddb7ac7efbd20b8988776 (buggy)
def map_params_to_obj(module):
    text = module.params['text']
    if text:
        text = str(text).strip()

    return {
        'banner': module.params['banner'],
        'text': text,
        'state': module.params['state']
    }
