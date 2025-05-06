from pathlib import Path
import re
from typing import Any, Final

from java.lang import Class

from .typedef import (
    JClsGenericDecl,
    JClsSignatureData,
    JConstructorSig,
    JFieldSig,
    JMethodParam,
    JMethodSig,
    JType,
)

# from .jclassparser import JavaClassParser
# from .stubgenerator import StubGenerator

reflector: Any


def _set_reflector(o: object):
    global reflector
    reflector = o


class PythonStubGenerator:
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
        # "java.lang.Object": "Any",
    }

    def generate_stub(self, signature: JClsSignatureData, output_path: str) -> None:
        """生成最终的.pyi文件"""
        stub_content = self._convert_to_stub(signature)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            _ = f.write(stub_content)

    def _convert_to_stub(self, signature: JClsSignatureData) -> str:
        """将Java签名转换为Python类型存根内容"""
        lines: list[str] = []

        # 1. 生成导入部分
        lines.extend(self._generate_imports(signature))
        lines.append("")

        # 2. 生成泛型类型变量
        lines.extend(self._generate_generics(signature.get("generics", [])))
        if signature.get("generics"):
            lines.append("")

        # 3. 生成类定义
        lines.append(self._generate_class_declaration(signature))
        lines.append("")

        # 4. 生成字段
        if fields := signature.get("fields"):
            lines.append("    # Fields")
            for field in fields:
                lines.append(self._generate_field(field))
            lines.append("")

        # 5. 生成构造器
        if constructors := signature.get("constructors"):
            lines.append("    # Constructors")
            for constructor in constructors:
                if len(constructors) > 1:
                    lines.append("    @overload")
                lines.append(self._generate_constructor(constructor))
            lines.append("")

        # 6. 生成方法
        if methods := signature.get("methods"):
            lines.append("    # Methods")
            for method in methods:
                lines.extend(self._generate_method(method))
            lines.append("")

        return "\n".join(lines)

    def _generate_imports(self, signature: JClsSignatureData) -> list[str]:
        """生成必要的导入语句"""
        imports = {"from typing import Any, ClassVar, Final, Generic, TypeVar, overload"}

        # 添加父类导入
        if extends := signature.get("extends"):  # noqa: SIM102
            if pkg := self._get_package_from_type(extends):
                imports.add(f"import {pkg}")

        # 添加接口导入
        for interface in signature.get("implements", []):
            if pkg := self._get_package_from_type(interface):
                imports.add(f"import {pkg}")

        # 添加字段/方法类型导入
        for member_type in self._collect_member_types(signature):
            if pkg := self._get_package_from_type(member_type):
                imports.add(f"import {pkg}")

        return sorted(imports)

    def _collect_member_types(self, signature: JClsSignatureData) -> list[str]:
        """收集所有需要导入的成员类型"""
        types: set[str] = set()

        # 字段类型
        for field in signature.get("fields", []):
            self._extract_types_from_jtype(field["type"], types)

        # 方法类型
        for method in signature.get("methods", []):
            self._extract_types_from_jtype(method["return_type"], types)
            for param in method["parameters"]:
                self._extract_types_from_jtype(param["type"], types)

        # 构造器参数类型
        for constructor in signature.get("constructors", []):
            for param in constructor["parameters"]:
                self._extract_types_from_jtype(param["type"], types)

        return list(types)

    def _extract_types_from_jtype(self, jtype: JType, types: set[str]) -> None:
        """递归提取JType中的所有类型"""
        if raw_type := jtype.get("type"):
            types.add(raw_type)
        if generics := jtype.get("generics"):
            for generic in generics:
                self._extract_types_from_jtype(generic, types)

    def _generate_generics(self, generics: list[JClsGenericDecl]) -> list[str]:
        """生成泛型类型变量声明"""
        lines: list[str] = []
        for generic in generics:
            line = f"{generic['name']} = TypeVar('{generic['name']}'"
            if extends := generic.get("extends"):
                line += f", bound={self._map_java_type(extends)}"
            lines.append(line + ")")
        return lines

    def _generate_class_declaration(self, signature: JClsSignatureData) -> str:
        """生成类定义行"""
        parts: list[str] = ["class ", signature["class_name"]]

        # 添加泛型参数
        if generics := signature.get("generics"):
            generic_params = ", ".join(g["name"] for g in generics)
            parts.append(f"[{generic_params}]")

        # 添加继承关系
        extends: list[str] = []
        if superclass := signature.get("extends"):
            extends.append(self._map_java_type(superclass))
        if interfaces := signature.get("implements"):
            extends.extend(self._map_java_type(i) for i in interfaces)

        if extends:
            parts.append(f"({', '.join(extends)})")

        parts.append(":")
        return "".join(parts)

    def _generate_field(self, field: JFieldSig) -> str:
        """生成字段定义"""
        field_type = self._convert_jtype_to_py(field["type"])
        modifiers: list[str] = []

        if field.get("static"):
            modifiers.append("ClassVar")
        if field.get("final"):
            modifiers.append("Final")

        if modifiers:
            field_type = f"{'['.join(modifiers)}[{field_type}]]"

        line = f"    {field['name']}: {field_type}"

        if "default_value" in field:
            line += f" = {field['default_value']}"

        return line

    def _generate_constructor(self, constructor: JConstructorSig) -> str:
        """生成构造器定义"""
        params = self._format_parameters(constructor["parameters"])
        params = ("self, " + params) if params else "self"
        return f"    def __init__({params}) -> None: ..."

    def _generate_method(self, method: JMethodSig, *, _overload: bool = False) -> list[str]:
        """生成方法定义（处理重载）"""
        lines: list[str] = []

        # 方法修饰符
        decorators: list[str] = []
        if method.get("static"):
            decorators.append("@staticmethod")
        if method.get("final"):
            decorators.append("@final")
        if _overload or method.get("overload"):
            decorators.append("@overload")

        # 方法签名
        return_type = self._convert_jtype_to_py(method["return_type"])
        params = self._format_parameters(method["parameters"])
        if not method.get("static"):
            params = ("self, " + params) if params else "self"

        method_line = f"    def {method['name']}({params}) -> {return_type}: ..."

        # 组装完整方法
        for decorator in decorators:
            lines.append(f"    {decorator}")
        lines.append(method_line)

        # 处理重载
        if overload := method.get("overload"):
            lines.extend(self._generate_method(overload, _overload=True))

        return lines

    def _format_parameters(self, parameters: list[JMethodParam]) -> str:
        """格式化参数列表"""
        param_strs: list[str] = []
        for param in parameters:
            param_type = self._convert_jtype_to_py(param["type"])
            if param.get("vararg"):
                param_strs.append(f"*{param['name']}: {param_type}")
            else:
                param_strs.append(f"{param['name']}: {param_type}")
        return ", ".join(param_strs)

    def _convert_jtype_to_py(self, jtype: JType) -> str:
        """将JType转换为Python类型表达式"""
        java_type = jtype["type"]
        py_type = self._map_java_type(java_type)

        # 处理泛型
        if generics := jtype.get("generics"):
            generic_args = ", ".join(self._convert_jtype_to_py(g) for g in generics)
            py_type = f"{py_type}[{generic_args}]"

        # 处理数组
        if dim := jtype.get("dimensions", 0):
            py_type = "list[" * dim + py_type + "]" * dim

        return py_type

    def _map_java_type(self, java_type: str) -> str:
        """映射Java类型到Python类型"""
        # 处理内部类(替换$为.)
        normalized_type = java_type.replace("$", ".")

        # 基本类型映射
        if normalized_type in self.TYPE_MAPPING:
            return self.TYPE_MAPPING[normalized_type]

        # 保留其他Java类型不变
        return normalized_type

    def _get_package_from_type(self, java_type: str) -> str | None:
        """从完整类型名中提取包名"""
        if "." not in java_type:
            return None

        # 处理泛型类型(如List<String>)
        clean_type = re.sub(r"<.*>", "", java_type)
        return ".".join(clean_type.split(".")[:-1])


def generate_stub(java_class_name: str, output_path: str):
    jclass = Class.forName(java_class_name)
    signature = reflector.generateClassSignature(jclass)
    stubgen = PythonStubGenerator()

    stubgen.generate_stub(signature, output_path)


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
