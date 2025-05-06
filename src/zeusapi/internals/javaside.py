from collections.abc import Callable
from typing import TYPE_CHECKING

from .typedef import JepInterpreter, JPythonRunner

if TYPE_CHECKING:
    class PythonRunner:
        def __init__(self) -> None: ...

        def execute(self, task: Callable[[JepInterpreter], None]) -> None: ...  # pyright: ignore[reportUnusedParameter]

        def close(self) -> None: ...

else:
    PythonRunner: type[JPythonRunner]

    def _set_python_runner_class(cls: type[JPythonRunner]) -> None:
        global PythonRunner
        PythonRunner = cls
