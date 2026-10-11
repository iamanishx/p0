"""Validate graphs and order inputs before users."""

from compiler.ir import Op, UOp


def validate(root: UOp) -> tuple[UOp, ...]:
    """Return input-first nodes, using identity to detect sharing and cycles."""
    ordered: list[UOp] = []
    visited: set[int] = set()
    active: set[int] = set()

    def visit(node: UOp) -> None:
        if not isinstance(node, UOp):
            raise TypeError("Graph nodes must be UOp instances")
        key = id(node)
        if key in active:
            raise ValueError("Graph contains a cycle")
        if key in visited:
            return
        if not isinstance(node.src, tuple):
            raise TypeError("UOp.src must be a tuple of input nodes")

        match node.op:
            case Op.CONST | Op.PARAM:
                if node.src:
                    raise ValueError(f"{node.op.name} must have no input nodes")
                if node.op is Op.CONST and type(node.arg) is not int:
                    raise TypeError("CONST requires an integer value")
                if node.op is Op.PARAM and (
                    not isinstance(node.arg, str) or not node.arg
                ):
                    raise TypeError("PARAM requires a non-empty name")
            case Op.ADD | Op.MUL:
                if len(node.src) != 2:
                    raise ValueError(f"{node.op.name} requires exactly two input nodes")
                if node.arg is not None:
                    raise ValueError(f"{node.op.name} does not accept an arg")
            case _:
                raise ValueError(f"Unsupported operation: {node.op!r}")

        active.add(key)
        for source in node.src:
            visit(source)
        active.remove(key)
        visited.add(key)
        ordered.append(node)

    visit(root)
    return tuple(ordered)
