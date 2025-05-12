import os
import sys

from zeusapi.internals.javaside import PythonRunner
from zeusapi.internals.typedef import JepInterpreter

sys.path.insert(0, "python/scripts")

runners: list[PythonRunner] = []

for mod in os.listdir("python/scripts"):
    if mod.startswith("_"):
        continue
    r = PythonRunner()
    @r.execute
    def _import(interpreter: JepInterpreter, /, mod: str = mod) -> None:
        interpreter.set("mod", mod)
        interpreter.exec("import importlib; importlib.import_module(mod)")
    _ = _import  # avoid TC complains about unused function
    runners.append(r)

pkmods = {mod[:-4] for mod in os.listdir("mods") if mod.lower().endswith(".pyz")}
pkwmods = {mod[:-5] for mod in os.listdir("mods") if mod.lower().endswith(".pyzw")}

if pkmods & pkwmods:
    ...

for m in pkmods:
    r = PythonRunner()
    @r.execute
    def _import(interpreter: JepInterpreter, /, mod: str = m) -> None:
        interpreter.set("mod", mod)
        interpreter.exec("from zeusapi.internals import zimport; zimport(mod)")
    _ = _import  # avoid TC complains about unused function
    runners.append(r)
