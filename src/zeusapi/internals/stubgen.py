import ast
from pathlib import Path
import shutil
from typing import Any, Final

from java.lang import Class

from .typedef import (
    JClsGenericDecl,
    JClsSignatureData,
    JConstructorSig,
    JFieldSig,
    JMethodSig,
    JType,
)

# from .jclassparser import JavaClassParser
# from .stubgenerator import StubGenerator

reflector: Any


def _set_reflector(o: object):
    global reflector
    reflector = o


_ = _set_reflector


class JavaToPythonAST:
    TYPE_MAPPING: Final = {
        "void": "None",
        "byte": "int",
        "short": "int",
        "int": "int",
        "long": "int",
        "float": "float",
        "double": "float",
        "char": "str",
        "char[]": "str",
        "byte[]": "bytes",
        "boolean": "bool",
        "java.lang.String": "str",
        "java.lang.Object": "object",
    }

    def __init__(self):
        pass

    def build_module(self, class_info: JClsSignatureData) -> ast.Module:
        """构建完整的Python模块AST"""
        body: list[ast.stmt] = []

        # add import statements
        body.append(
            ast.ImportFrom(
                module="typing",
                names=[
                    ast.alias(name="Final"),
                    ast.alias(name="ClassVar"),
                    ast.alias(name="overload"),
                ],
                level=0,
            )
        )

        for jtp in self._collect_member_types(class_info):
            split = self._split_java_type(jtp)
            if split is None:
                continue
            mod, name = split
            body.append(ast.ImportFrom(module=mod, names=[ast.alias(name=name)], level=0))

        # add generic typevars
        if generics := class_info.get("generics"):
            body.extend(self._build_typevars(generics))

        # build class def
        class_def = self._build_class_def(class_info)
        body.append(class_def)

        return ast.Module(body=body, type_ignores=[])

    def _collect_member_types(self, signature: JClsSignatureData) -> set[str]:
        """收集所有需要导入的成员类型"""
        types: set[str] = set()

        # 字段类型
        for field in signature.get("fields", []):
            types |= self._extract_types_from_jtype(field["type"])

        # 方法类型
        for method in signature.get("methods", []):
            types |= self._extract_types_from_jtype(method["return_type"])
            for param in method["parameters"]:
                types |= self._extract_types_from_jtype(param["type"])

        # 构造器参数类型
        for constructor in signature.get("constructors", []):
            for param in constructor["parameters"]:
                types |= self._extract_types_from_jtype(param["type"])

        return types

    def _extract_types_from_jtype(self, jtype: JType) -> set[str]:
        """递归提取JType中的所有类型"""
        types: set[str] = set()

        if raw_type := jtype.get("type"):
            types.add(raw_type)

        if generics := jtype.get("generics"):
            for generic in generics:
                types |= self._extract_types_from_jtype(generic)

        return types

    def _build_typevars(self, generics: list[JClsGenericDecl]) -> list[ast.Assign]:
        """构建类型变量定义AST"""
        assignments: list[ast.Assign] = []
        for generic in generics:
            # 示例：T = TypeVar('T', bound=Parent)
            if (bound := generic.get("super")) is None:
                continue
            target = ast.Name(id=generic["name"], ctx=ast.Store())

            args: list[ast.expr] = [ast.Constant(value=generic["name"])]
            kwds: list[ast.keyword] = [
                ast.keyword(
                    arg="bound", value=ast.Name(id=self._map_java_type(bound), ctx=ast.Load())
                ),
                ast.keyword(arg="contravariant", value=ast.Constant(True)),
            ]

            value = ast.Call(func=ast.Name(id="TypeVar", ctx=ast.Load()), args=args, keywords=kwds)

            assignments.append(ast.Assign(targets=[target], value=value))
        return assignments

    def _build_type_params(self, generics: list[JClsGenericDecl]) -> list[ast.type_param]:
        """构建 Python 3.12+ 风格的类型参数"""
        type_params: list[ast.type_param] = []

        for generic in generics:
            name = generic["name"]

            if extends := generic.get("extends"):
                bound = self._build_type_annotation(extends)
                type_param = ast.TypeVar(name, bound=bound)

            else:
                type_param = ast.TypeVar(name)

            type_params.append(type_param)

        return type_params

    def _build_class_def(self, class_info: JClsSignatureData) -> ast.ClassDef:
        """构建类定义AST"""
        # 类名处理
        class_name = class_info["class_name"].split("$")[-1]

        # 基类处理
        bases: list[ast.expr] = []
        if extends := class_info.get("extends"):
            bases.append(self._build_type_annotation(extends))

        # 接口实现
        for interface in class_info.get("implements", []):
            bases.append(self._build_type_annotation(interface))

        # 泛型参数
        type_params = self._build_type_params(class_info.get("generics", []))

        # 类体内容
        body: list[ast.stmt] = []
        if fields := class_info.get("fields"):
            for field in fields:
                body.append(self._build_field(field))

        if methods := class_info.get("methods"):
            for method in methods:
                body.extend(self._build_method(method))

        if constructors := class_info.get("constructors"):
            for constructor in constructors:
                body.extend(self._generate_constructor(constructor))

        return ast.ClassDef(
            name=class_name,
            bases=bases,
            keywords=[],
            body=body,
            decorator_list=[],
            type_params=type_params,
        )

    def _build_field(self, field_info: JFieldSig) -> ast.AnnAssign:
        """构建字段定义AST"""
        annotation = self._build_type_annotation(field_info["type"])

        # 处理修饰符
        if field_info.get("final"):
            annotation = ast.Subscript(
                value=ast.Name(id="Final", ctx=ast.Load()), slice=annotation, ctx=ast.Load()
            )
        elif field_info.get("static"):
            annotation = ast.Subscript(
                value=ast.Name(id="ClassVar", ctx=ast.Load()), slice=annotation, ctx=ast.Load()
            )

        return ast.AnnAssign(
            target=ast.Name(id=field_info["name"], ctx=ast.Store()),
            annotation=annotation,
            value=ast.Constant(value=Ellipsis)
            if "default_value" not in field_info
            else ast.Constant(value=field_info["default_value"]),
            simple=1,
        )

    def _build_method(self, method_info: JMethodSig) -> list[ast.stmt]:
        """构建方法定义AST（处理重载）"""
        nodes: list[ast.stmt] = []

        # 类型参数
        type_params = self._build_type_params(method_info.get("generics", []))

        # 修饰符
        decorators: list[ast.expr] = []
        if method_info.get("static"):
            decorators.append(ast.Name(id="staticmethod", ctx=ast.Load()))
        if method_info.get("final"):
            decorators.append(ast.Name(id="final", ctx=ast.Load()))
        if method_info.get("overload"):
            decorators.append(ast.Name(id="overload", ctx=ast.Load()))

        # 参数
        args: list[ast.arg] = []
        if not method_info.get("static"):
            args.append(ast.arg(arg="self", annotation=None))

        for param in method_info["parameters"]:
            arg = ast.arg(arg=param["name"], annotation=self._build_type_annotation(param["type"]))
            if param.get("vararg"):
                arg.arg = "*" + arg.arg
            args.append(arg)

        # 返回值
        returns = self._build_type_annotation(method_info["return_type"])

        # 构建函数定义
        func_def = ast.FunctionDef(
            name=method_info["name"],
            type_params=type_params,
            args=ast.arguments(
                posonlyargs=[], args=args, kwonlyargs=[], kw_defaults=[], defaults=[]
            ),
            body=[ast.Expr(value=ast.Constant(value=Ellipsis))],
            decorator_list=decorators,
            returns=returns,
        )

        nodes.append(func_def)

        # 处理重载
        if overload := method_info.get("overload"):
            nodes.extend(self._build_method(overload))

        return nodes

    def _generate_constructor(self, constructor: JConstructorSig) -> list[ast.stmt]:
        """生成构造函数的AST节点列表"""
        nodes: list[ast.stmt] = []

        # 1. 处理装饰器
        decorators: list[ast.expr] = []
        if constructor.get("protected"):
            decorators.append(ast.Name(id="protected", ctx=ast.Load()))

        # 2. 构建参数列表
        args: list[ast.arg] = []
        # self参数
        args.append(ast.arg(arg="self", annotation=None))

        for param in constructor["parameters"]:
            # 参数类型注解
            annotation = self._build_type_annotation(param["type"])

            # 可变参数处理（*args）
            arg_name = f"*{param['name']}" if param.get("vararg") else param["name"]

            args.append(
                ast.arg(
                    arg=arg_name,
                    annotation=annotation,
                )
            )

        # 3. 构建函数定义
        init_func = ast.FunctionDef(
            name="__init__",
            args=ast.arguments(
                posonlyargs=[],
                args=args,
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
                vararg=None,
                kwarg=None,
            ),
            body=[ast.Expr(value=ast.Constant(value=Ellipsis))],
            decorator_list=decorators,
            returns=ast.Name(id="None", ctx=ast.Load()),
            type_params=[],  # 构造函数不支持独立泛型
        )

        nodes.append(init_func)

        return nodes

    def _build_type_annotation(self, java_type: str | JType) -> ast.expr:
        """支持新类型语法的类型注解构建"""
        if isinstance(java_type, dict):
            base_type = java_type["type"]
            dim = java_type.get("dimensions", 0)
            generics = java_type.get("generics", [])
        else:
            base_type = java_type
            dim = 0
            generics = []

        # 基本类型映射
        if base_type in self.TYPE_MAPPING:
            annotation = ast.Name(id=self.TYPE_MAPPING[base_type], ctx=ast.Load())
        else:
            # 处理泛型
            if "<" in base_type or generics:
                base = base_type.split("<")[0] if "<" in base_type else base_type
                base_ast = ast.Name(id=self._map_java_type(base), ctx=ast.Load())

                generic_args = [
                    self._build_type_annotation(g)
                    for g in (generics or base_type.split("<")[1].rstrip(">").split(","))
                ]

                annotation = ast.Subscript(
                    value=base_ast,
                    slice=ast.Tuple(elts=generic_args, ctx=ast.Load())
                    if len(generic_args) > 1
                    else generic_args[0],
                    ctx=ast.Load(),
                )
            else:
                annotation = ast.Name(id=self._map_java_type(base_type), ctx=ast.Load())

        # 处理数组
        for _ in range(dim):
            annotation = ast.Subscript(
                value=ast.Name(id="list", ctx=ast.Load()), slice=annotation, ctx=ast.Load()
            )

        return annotation

    def _map_java_type(self, java_type: str) -> str:
        """映射Java类型名到Python类型名"""
        if "<" in java_type:
            return self._map_java_type(java_type.split("<")[0])
        return java_type.split(".")[-1].replace("$", ".")

    def _split_java_type(self, java_type: str) -> tuple[str, str] | None:
        """拆分Java类型为包名和类名"""
        parts = java_type.replace("$", ".").split(".")
        if len(parts) < 2:
            return None
        return (".".join(parts[:-1]), parts[-1])


def generate_stub(java_class_name: str, output_dir: str):
    jclass = Class.forName(java_class_name)
    signature = reflector.generateClassSignature(jclass)
    stubgen = JavaToPythonAST()

    # Determine output path based on packaging rules
    output_path = _determine_output_path(java_class_name, output_dir)

    # Ensure parent directories exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Generate the stub content
    stub_content = stubgen.build_module(signature)

    # Write to file
    with open(output_path, "a" if output_path.exists() else "w", encoding="utf-8") as f:
        _ = f.write(ast.unparse(ast.fix_missing_locations(stub_content)))
        _ = f.write("\n\n")


def _determine_output_path(java_class_name: str, output_dir: str) -> Path:
    parts = java_class_name.split(".")
    if len(parts) < 2:
        raise ValueError(f"Invalid Java class name: {java_class_name}")

    base_path = Path(output_dir)
    package_parts = parts[:-1]

    target_file = base_path

    for route, r_next in zip(package_parts, package_parts[1:] + [None], strict=True):
        target_file /= route
        if r_next is None:
            if target_file.is_dir():
                return target_file / "__init__.pyi"
            return target_file.with_suffix(".pyi")
        target_file.mkdir(parents=True, exist_ok=True)
        if (old_pyi := target_file.with_suffix(".pyi")).is_file():
            _ = shutil.move(old_pyi, target_file / "__init__.pyi")

    raise RuntimeError("An unreachable end has been executed.")


# def generate_stub_for_loaded_classes(output_dir: str):
#     loader: ClassLoader = ClassLoader.getSystemClassLoader()
#     classes: list[Class] = (
#         loader.getDefinedPackages()
#         .stream()
#         .flatMap(lambda pkg: Arrays.stream(pkg.getDeclaredClasses()))
#         .toList()
#     )

#     for c in classes:
#         ...
