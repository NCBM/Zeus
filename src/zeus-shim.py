import os
import sys

from zeusapi.internals.javaside import PythonRunner
from zeusapi.internals.typedef import JepInterpreter

sys.path.insert(0, "python/mods")

runners: list[PythonRunner] = []

for mod in os.listdir("python/mods"):
    if mod.startswith("_"):
        continue
    r = PythonRunner()
    @r.execute
    def _import(interpreter: JepInterpreter) -> None:
        interpreter.set("mod", mod)  # noqa: B023
        interpreter.exec("import importlib; importlib.import_module(mod)")
    _ = _import  # avoid TC complains about unused function
    runners.append(r)

pkmods = {mod[:-4] for mod in os.listdir("mods") if mod.lower().endswith(".pyz")}
pkwmods = {mod[:-5] for mod in os.listdir("mods") if mod.lower().endswith(".pyzw")}

for m in pkmods:
    r = PythonRunner()
    @r.execute
    def _import(interpreter: JepInterpreter) -> None:
        interpreter.set("mod", m)  # noqa: B023
        interpreter.exec("from zeusapi.internals import zimport; zimport(mod)")
    _ = _import  # avoid TC complains about unused function
    runners.append(r)
