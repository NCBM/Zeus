import importlib.util
import sys
from types import ModuleType
import zipimport


def zimport(modname: str, filename: str | None = None) -> ModuleType:
    filename = f"mods/{modname}.pyz" if filename is None else f"mods/{filename}"
    imp = zipimport.zipimporter(filename)
    spec = imp.find_spec(modname)
    if spec is None:
        raise ModuleNotFoundError(f"No mod module named {modname!r} in {filename!r}.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[modname] = module
    if spec.loader is None:
        raise ImportError(f"Cannot load module {modname!r}.")
    spec.loader.exec_module(module)
    return module
