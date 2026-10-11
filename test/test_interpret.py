"""Test graph evaluation and input errors."""

import unittest

from compiler.interpret import evaluate
from compiler.ir import Op, UOp
from example.simple import build_graph


class TestInterpreter(unittest.TestCase):
    def test_constants(self):
        for value in (0, 2, -3):
            with self.subTest(value=value):
                self.assertEqual(evaluate(UOp(Op.CONST, arg=value), {}), value)

    def test_parameter(self):
        self.assertEqual(evaluate(UOp(Op.PARAM, arg="x"), {"x": 4}), 4)

    def test_arithmetic(self):
        two = UOp(Op.CONST, arg=2)
        three = UOp(Op.CONST, arg=3)
        self.assertEqual(evaluate(UOp(Op.ADD, src=(two, three)), {}), 5)
        self.assertEqual(evaluate(UOp(Op.MUL, src=(two, three)), {}), 6)

    def test_example_with_different_inputs(self):
        # Cache values must not leak across calls.
        graph = build_graph()
        for x, expected in ((4, 20), (0, 0), (-2, -10)):
            with self.subTest(x=x):
                self.assertEqual(evaluate(graph, {"x": x}), expected)

    def test_shared_input_is_evaluated_once(self):
        class CountingInputs(dict):
            reads = 0

            def __getitem__(self, key):
                self.reads += 1
                return super().__getitem__(key)

        x = UOp(Op.PARAM, arg="x")
        shared = UOp(Op.ADD, src=(x, UOp(Op.CONST, arg=1)))
        square = UOp(Op.MUL, src=(shared, shared))
        inputs = CountingInputs(x=4)
        self.assertEqual(evaluate(square, inputs), 25)
        self.assertEqual(inputs.reads, 1)

    def test_evaluation_does_not_modify_graph_or_inputs(self):
        graph = build_graph()
        inputs = {"x": 4}
        evaluate(graph, inputs)
        self.assertEqual(graph, build_graph())
        self.assertEqual(inputs, {"x": 4})
        # Evaluation leaves the ADD intact.
        self.assertEqual(graph.src[1].op, Op.ADD)

    def test_missing_parameter(self):
        with self.assertRaisesRegex(ValueError, "Missing value for parameter 'x'"):
            evaluate(build_graph(), {})

    def test_invalid_integer_values(self):
        for value in (2.0, "2", True, None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    TypeError, "CONST requires an integer value"
                ):
                    evaluate(UOp(Op.CONST, arg=value), {})
                with self.assertRaisesRegex(TypeError, "requires an integer value"):
                    evaluate(UOp(Op.PARAM, arg="x"), {"x": value})

    def test_invalid_parameter_names(self):
        for name in (None, 2, ""):
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(TypeError, "PARAM requires a non-empty name"),
            ):
                evaluate(UOp(Op.PARAM, arg=name), {})

    def test_arithmetic_requires_two_inputs(self):
        constant = UOp(Op.CONST, arg=2)
        for op in (Op.ADD, Op.MUL):
            for inputs in ((), (constant,), (constant, constant, constant)):
                with (
                    self.subTest(op=op, inputs=inputs),
                    self.assertRaisesRegex(ValueError, "requires exactly two input nodes"),
                ):
                    evaluate(UOp(op, src=inputs), {})

    def test_arithmetic_rejects_extra_arg(self):
        constant = UOp(Op.CONST, arg=2)
        for op in (Op.ADD, Op.MUL):
            with (
                self.subTest(op=op),
                self.assertRaisesRegex(ValueError, "does not accept an arg"),
            ):
                evaluate(UOp(op, src=(constant, constant), arg=3), {})

    def test_leaf_nodes_reject_inputs(self):
        constant = UOp(Op.CONST, arg=2)
        for node in (
            UOp(Op.CONST, src=(constant,), arg=3),
            UOp(Op.PARAM, src=(constant,), arg="x"),
        ):
            with (
                self.subTest(node=node),
                self.assertRaisesRegex(ValueError, "must have no input nodes"),
            ):
                evaluate(node, {"x": 4})

    def test_unsupported_operation(self):
        with self.assertRaisesRegex(ValueError, "Unsupported operation"):
            evaluate(UOp("DIV"), {})


if __name__ == "__main__":
    unittest.main()
