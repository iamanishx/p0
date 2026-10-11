"""Evaluate scalar integer graphs in Python."""

from collections.abc import Mapping

from compiler.ir import Op, UOp


def evaluate(root: UOp, params: Mapping[str, int]) -> int:
    """Use Python integers and a per-call cache; leave the graph unchanged."""
    cache: dict[UOp, int] = {}

    def visit(node: UOp) -> int:
        if node in cache:
            return cache[node]

        if node.op in (Op.CONST, Op.PARAM) and node.src:
            raise ValueError(f"{node.op.name} must have no input nodes")

        match node.op:
            case Op.CONST:
                if type(node.arg) is not int:
                    raise TypeError("CONST requires an integer value")
                value = node.arg

            case Op.PARAM:
                if not isinstance(node.arg, str) or not node.arg:
                    raise TypeError("PARAM requires a non-empty name")
                try:
                    value = params[node.arg]
                except KeyError:
                    raise ValueError(
                        f"Missing value for parameter {node.arg!r}"
                    ) from None
                if type(value) is not int:
                    raise TypeError(f"Parameter {node.arg!r} requires an integer value")

            case Op.ADD | Op.MUL:
                if len(node.src) != 2:
                    raise ValueError(f"{node.op.name} requires exactly two input nodes")
                if node.arg is not None:
                    raise ValueError(f"{node.op.name} does not accept an arg")
                left = visit(node.src[0])
                right = visit(node.src[1])
                value = left + right if node.op is Op.ADD else left * right

            case _:
                raise ValueError(f"Unsupported operation: {node.op!r}")

        cache[node] = value
        return value

    return visit(root)
