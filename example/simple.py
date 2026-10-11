import argparse

from compiler.interpret import evaluate
from compiler.ir import Op, UOp
from compiler.render_c import render_c


def build_graph() -> UOp:
    x = UOp(Op.PARAM, arg="x")
    two = UOp(Op.CONST, arg=2)
    three = UOp(Op.CONST, arg=3)

    addition = UOp(Op.ADD, src=(two, three))
    result = UOp(Op.MUL, src=(x, addition))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build, evaluate, and render a tiny UOp graph."
    )
    parser.add_argument(
        "--emit-c",
        action="store_true",
        help="Print only C source, suitable for redirecting to a file.",
    )
    args = parser.parse_args()
    graph = build_graph()
    if args.emit_c:
        print(render_c(graph), end="")
    else:
        print("Computation: x * (2 + 3)")
        print("Graph root:")
        print(graph)
        print("\nInterpreter result with x = 4:")
        print(evaluate(graph, {"x": 4}))
        print("\nGenerated C (without evaluating the graph):")
        print(render_c(graph), end="")
