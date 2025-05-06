import importlib.util
import sys
import zipimport


def zimport(modname: str):
    imp = zipimport.zipimporter(f"mods/{modname}.pyz")
    spec = imp.find_spec(modname)
    if spec is None:
        raise ModuleNotFoundError(f"No mod module named {modname!r} in {modname+'.pyz'!r}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[modname] = module
    spec.loader.exec_module(module)
    return module
