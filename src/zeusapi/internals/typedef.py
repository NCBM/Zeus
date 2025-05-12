from typing import Any, Callable, Final, NotRequired, Protocol, TypedDict


class JClsGenericDecl(TypedDict):
    name: str
    extends: NotRequired[str]  # e.g., "Number"
    super: NotRequired[str]    # e.g., "Comparable"


class JType(TypedDict):
    type: str
    generics: NotRequired[list["JType"]]  # For nested generics
    dimensions: NotRequired[int]


class JMethodParam(TypedDict):
    name: str
    type: JType  # Use JType to support generics in parameter types
    vararg: NotRequired[bool]  # convert to *args: T


class JMethodSig(TypedDict):
    name: str
    parameters: list[JMethodParam]
    return_type: JType  # Use JType to support generics in return types
    static: NotRequired[bool]  # convert to @staticmethod
    final: NotRequired[bool]  # convert to @final
    protected: NotRequired[bool]  # in our case only 'public' and 'protected' can be accessed
    overload: NotRequired["JMethodSig"]


class JFieldSig(TypedDict):
    name: str
    type: JType  # Use JType to support generics in field types
    static: NotRequired[bool]  # convert to ClassVar[T]
    final: NotRequired[bool]  # convert to Final[T]
    protected: NotRequired[bool]  # in our case only 'public' and 'protected' can be accessed
    default_value: NotRequired[str]  # Use "..." to represent missing default values


class JConstructorSig(TypedDict):
    parameters: list[JMethodParam]
    protected: NotRequired[bool]  # in our case only 'public' and 'protected' can be accessed


class JClsSignatureData(TypedDict):
    package: str
    class_name: str
    extends: NotRequired[str]
    implements: NotRequired[list[str]]
    methods: list[JMethodSig]
    fields: list[JFieldSig]
    constructors: list[JConstructorSig]
    generics: list[JClsGenericDecl]


class JepInterpreter(Protocol):
    def invoke(
        self, callee: str,
        arg1_kwds_args: Any | dict[str, Any] | list[Any] = None,
        arg2_unused_kwds: Any | dict[str, Any] = None, /, *args: Any
    ) -> Any: ...

    def eval(self, code: str) -> bool: ...

    def exec(self, code: str) -> None: ...

    def runScript(self, filename: str) -> None: ...

    def getValue(self, code: str) -> Any: ...

    def set(self, name: str, val: Any) -> None: ...

    def close(self) -> None: ...


class JPythonRunner(Protocol):
    def __init__(self) -> None: ...

    def execute(self, task: Callable[[JepInterpreter], None]) -> None: ...

    def close(self) -> None: ...


class SLFLogger(Protocol):
    ROOT_LOGGER_NAME: Final = "ROOT"

    def getName(self) -> str: ...

    def trace(self, arg0: str, /) -> None: ...

    def debug(self, arg0: str, /) -> None: ...

    def info(self, arg0: str, /) -> None: ...

    def warn(self, arg0: str, /) -> None: ...

    def error(self, arg0: str, /) -> None: ...
