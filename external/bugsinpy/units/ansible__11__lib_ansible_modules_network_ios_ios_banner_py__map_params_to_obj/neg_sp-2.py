def fn_map_params_to_obj(module):
    text = module.params['text']
    return {'banner': module.params['banner'], 'text': text, 'state': module.params['state']}