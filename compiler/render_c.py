"""Render scalar integer graphs as C11."""

import re

from compiler.ir import Op, UOp
from compiler.validate import validate

# Exclude leading underscores and non-ASCII names.
_IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")
_KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if", "inline",
    "int", "long", "register", "restrict", "return", "short", "signed", "sizeof",
    "static", "struct", "switch", "typedef", "union", "unsigned", "void",
    "volatile", "while", "_Alignas", "_Alignof", "_Atomic", "_Bool", "_Complex",
    "_Generic", "_Imaginary", "_Noreturn", "_Static_assert", "_Thread_local",
}
_INT32_MIN = -(2**31)
_INT32_MAX = 2**31 - 1


def _check_name(name: str, kind: str) -> None:
    reserved = _KEYWORDS | {
        "main",
        "SIZE_MAX",
        "PTRDIFF_MIN",
        "PTRDIFF_MAX",
        "SIG_ATOMIC_MIN",
        "SIG_ATOMIC_MAX",
        "WCHAR_MIN",
        "WCHAR_MAX",
        "WINT_MIN",
        "WINT_MAX",
    }
    # Avoid <stdint.h> typedefs and macros.
    header_name = isinstance(name, str) and (
        name.startswith(("INT", "UINT")) or re.fullmatch(r"u?int\w*_t", name)
    )
    if (
        not isinstance(name, str)
        or not _IDENTIFIER.fullmatch(name)
        or name in reserved
        or header_name
    ):
        raise ValueError(f"Invalid C {kind} name: {name!r}")


def _literal(value: int) -> str:
    if not _INT32_MIN <= value <= _INT32_MAX:
        raise ValueError(f"Constant {value} is outside the signed 32-bit range")
    if value == _INT32_MIN:
        return "INT32_MIN"
    if value < 0:
        return f"(-INT32_C({-value}))"
    return f"INT32_C({value})"


def render_c(root: UOp, function_name: str = "kernel") -> str:
    """Emit unoptimized C with parameters in first-encounter order.

    Inputs and intermediate results must fit in signed 32-bit range.
    """
    _check_name(function_name, "function")
    nodes = validate(root)
    parameters: list[str] = []
    for node in nodes:
        if node.op is Op.PARAM:
            _check_name(node.arg, "parameter")
            if node.arg == function_name:
                raise ValueError(
                    "A parameter cannot have the same name as the C function"
                )
            if node.arg not in parameters:
                parameters.append(node.arg)

    signature = ", ".join(f"int32_t {name}" for name in parameters) or "void"
    lines = ["#include <stdint.h>", "", f"int32_t {function_name}({signature}) {{"]
    expressions: dict[int, str] = {}
    used_names = set(parameters) | {function_name}
    next_temp = 0

    for node in nodes:
        if node.op is Op.CONST:
            expression = _literal(node.arg)
        elif node.op is Op.PARAM:
            expression = node.arg
        else:
            while f"t{next_temp}" in used_names:
                next_temp += 1
            expression = f"t{next_temp}"
            used_names.add(expression)
            next_temp += 1
            left, right = (expressions[id(source)] for source in node.src)
            operator = "+" if node.op is Op.ADD else "*"
            lines.append(f"    int32_t {expression} = ({left} {operator} {right});")
        expressions[id(node)] = expression

    lines.append(f"    return {expressions[id(root)]};")
    lines.append("}")
    return "\n".join(lines) + "\n"
