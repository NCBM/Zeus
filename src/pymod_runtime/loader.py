import importlib.util
import sys
from importlib import import_module as import_module
from pathlib import Path


def import_from_path(module_name: str, file_path: str | Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Cannot find a spec for importing module {module_name!r} from {file_path!r}")
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise ImportError(f"Cannot find a loader for importing module {module_name!r} from {file_path!r}")
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module