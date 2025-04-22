from collections.abc import Callable
from typing import Any, override


class PyJObject:
    def __getattr__(self, name: str) -> Any: ...

    @override
    def __setattr__(self, name: str, value: Any, /) -> None: ...


def setJavaToPythonConverter(obj: type[PyJObject], conversion: Callable[[PyJObject], object]) -> None: ...