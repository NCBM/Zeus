import inspect

from net.neoforged.fml import event as fml_event
from net.neoforged.neoforge import event as common_event
from net.neoforged.neoforge.event import client as client_event
from net.neoforged.neoforge.event import server as server_event


def event(fn):
    sig = inspect.signature(fn)
    typ = next(iter(sig.parameters.values())).annotation
    if isinstance(typ, str):
        typ = eval(typ, globals())
    return fn