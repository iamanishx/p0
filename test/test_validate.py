"""Test graph validation."""

import unittest

from compiler.ir import Op, UOp
from compiler.validate import validate
from example.simple import build_graph


class TestValidation(unittest.TestCase):
    def test_input_first_order(self):
        nodes = validate(build_graph())
        self.assertEqual(
            [node.op for node in nodes], [Op.PARAM, Op.CONST, Op.CONST, Op.ADD, Op.MUL]
        )
        positions = {id(node): index for index, node in enumerate(nodes)}
        for node in nodes:
            for source in node.src:
                self.assertLess(positions[id(source)], positions[id(node)])

    def test_shared_nodes_appear_once(self):
        x = UOp(Op.PARAM, arg="x")
        square = UOp(Op.MUL, src=(x, x))
        nodes = validate(square)
        self.assertEqual(len(nodes), 2)
        self.assertIs(nodes[0], x)

    def test_invalid_graphs(self):
        constant = UOp(Op.CONST, arg=2)
        cases = [
            (None, TypeError, "UOp instances"),
            (UOp("DIV"), ValueError, "Unsupported operation"),
            (UOp(Op.CONST, arg=True), TypeError, "integer value"),
            (UOp(Op.PARAM, arg=""), TypeError, "non-empty name"),
            (UOp(Op.CONST, src=(constant,), arg=2), ValueError, "no input nodes"),
            (UOp(Op.ADD, src=(constant,)), ValueError, "exactly two"),
            (
                UOp(Op.MUL, src=(constant, constant), arg=1),
                ValueError,
                "does not accept",
            ),
            (UOp(Op.ADD, src=(constant, None)), TypeError, "UOp instances"),
            (UOp(Op.ADD, src=[constant, constant]), TypeError, "must be a tuple"),
        ]
        for root, error, message in cases:
            with self.subTest(root=root), self.assertRaisesRegex(error, message):
                validate(root)

    def test_cycle_is_rejected(self):
        node = UOp(Op.ADD)
        # Bypass immutability to test cycle rejection.
        object.__setattr__(node, "src", (node, UOp(Op.CONST, arg=1)))
        with self.assertRaisesRegex(ValueError, "cycle"):
            validate(node)


if __name__ == "__main__":
    unittest.main()
