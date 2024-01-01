def safe_get(a: [object], i: object, default: object = None) -> object:
    if a is None:
        return default
    elif type(a) == list:
        return a[i] if len(a) > i else default
    elif type(a) == dict:
        return a[i] if i in a else default
    else:
        raise KeyError('Can\'t safely-get from unhandled type %s (more code is needed in %s)'
                      % (type(a), __file__))
