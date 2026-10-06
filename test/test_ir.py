"""Check our graph structure, not its numerical result yet."""

from dataclasses import FrozenInstanceError
import unittest

from compiler.ir import Op, UOp
from example.simple import build_graph


class TestIR(unittest.TestCase):
    def test_constant_has_no_inputs(self):
        node = UOp(Op.CONST, arg=2)
        self.assertEqual(node.op, Op.CONST)
        self.assertEqual(node.src, ())
        self.assertEqual(node.arg, 2)

    def test_example_graph_structure(self):
        graph = build_graph()
        self.assertEqual(graph.op, Op.MUL)
        x, addition = graph.src
        self.assertEqual(x, UOp(Op.PARAM, arg="x"))
        self.assertEqual(addition.op, Op.ADD)
        self.assertEqual(addition.src, (
            UOp(Op.CONST, arg=2),
            UOp(Op.CONST, arg=3),
        ))

    def test_nodes_can_share_an_input(self):
        x = UOp(Op.PARAM, arg="x")
        square = UOp(Op.MUL, src=(x, x))
        self.assertIs(square.src[0], square.src[1])

    def test_nodes_are_immutable(self):
        node = UOp(Op.CONST, arg=2)
        with self.assertRaises(FrozenInstanceError):
            node.arg = 3


if __name__ == "__main__":
    unittest.main()
