from compiler.ir import Op, UOp


def build_graph() -> UOp:
    x = UOp(Op.PARAM, arg="x")
    two = UOp(Op.CONST, arg=2)
    three = UOp(Op.CONST, arg=3)

    addition = UOp(Op.ADD, src=(two, three))
    result = UOp(Op.MUL, src=(x, addition))
    return result


if __name__ == "__main__":
    graph = build_graph()
    print("Computation: x * (2 + 3)")
    print("Graph root:")
    print(graph)
    print("\nThis describes the computation; it has not executed it.")
