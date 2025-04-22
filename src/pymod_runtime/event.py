import inspect


def event(fn):
    sig = inspect.signature(fn)
    typ = next(iter(sig.parameters.values())).annotation
    if not isinstance(typ, str):
        typ = typ.__name__
    return fn