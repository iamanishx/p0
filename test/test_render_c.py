"""Test C generation and native execution."""

import ctypes
import random
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.interpret import evaluate
from compiler.ir import Op, UOp
from compiler.render_c import render_c
from example.simple import build_graph

CC = shutil.which("clang") or shutil.which("gcc")


class TestCRenderer(unittest.TestCase):
    def test_example_source(self):
        self.assertEqual(
            render_c(build_graph()),
            "#include <stdint.h>\n\n"
            "int32_t kernel(int32_t x) {\n"
            "    int32_t t0 = (INT32_C(2) + INT32_C(3));\n"
            "    int32_t t1 = (x * t0);\n"
            "    return t1;\n}\n",
        )

    def test_no_runtime_values_needed(self):
        self.assertIn("int32_t x", render_c(UOp(Op.PARAM, arg="x")))

    def test_constant_function(self):
        self.assertIn("kernel(void)", render_c(UOp(Op.CONST, arg=7)))
        self.assertIn("return INT32_C(7);", render_c(UOp(Op.CONST, arg=7)))

    def test_negative_literals(self):
        self.assertIn("(-INT32_C(7))", render_c(UOp(Op.CONST, arg=-7)))
        self.assertIn("return INT32_MIN;", render_c(UOp(Op.CONST, arg=-(2**31))))

    def test_parameter_order_and_deduplication(self):
        b = UOp(Op.PARAM, arg="b")
        a = UOp(Op.PARAM, arg="a")
        inner = UOp(Op.ADD, src=(b, a))
        graph = UOp(Op.MUL, src=(inner, UOp(Op.PARAM, arg="b")))
        source = render_c(graph)
        self.assertIn("kernel(int32_t b, int32_t a)", source)

    def test_shared_arithmetic_emitted_once(self):
        x = UOp(Op.PARAM, arg="x")
        shared = UOp(Op.ADD, src=(x, UOp(Op.CONST, arg=1)))
        source = render_c(UOp(Op.MUL, src=(shared, shared)))
        self.assertEqual(source.count(" + "), 1)
        self.assertIn("(t0 * t0)", source)

    def test_temporary_names_do_not_shadow_parameters(self):
        graph = UOp(Op.ADD, src=(UOp(Op.PARAM, arg="t0"), UOp(Op.CONST, arg=1)))
        self.assertIn("int32_t t1 = (t0 + INT32_C(1));", render_c(graph))

    def test_custom_function_name(self):
        self.assertIn("add_one(void)", render_c(UOp(Op.CONST, arg=1), "add_one"))

    def test_function_name_does_not_collide_with_temporary(self):
        graph = UOp(Op.ADD, src=(UOp(Op.CONST, arg=1), UOp(Op.CONST, arg=2)))
        self.assertIn("int32_t t1 =", render_c(graph, "t0"))

    def test_invalid_c_names(self):
        names = [
            "",
            "1x",
            "x-y",
            "return",
            "_reserved",
            "x); bad();",
            "café",
            "int32_t",
            "INT32_C",
            "INT32_MIN",
            "uint64_t",
            "INT_FAST16_MAX",
            "SIZE_MAX",
            "main",
            None,
        ]
        for name in names:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "Invalid C"):
                    render_c(UOp(Op.CONST, arg=1), name)
                if isinstance(name, str) and name:
                    with self.assertRaisesRegex(ValueError, "Invalid C"):
                        render_c(UOp(Op.PARAM, arg=name))

    def test_parameter_cannot_shadow_function(self):
        with self.assertRaisesRegex(ValueError, "same name"):
            render_c(UOp(Op.PARAM, arg="kernel"))

    def test_out_of_range_constants(self):
        for value in (-(2**31) - 1, 2**31):
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(ValueError, "signed 32-bit range"),
            ):
                render_c(UOp(Op.CONST, arg=value))

    def test_malformed_graph_rejected_before_emission(self):
        with self.assertRaisesRegex(ValueError, "exactly two"):
            render_c(UOp(Op.ADD))


@unittest.skipUnless(CC, "Clang or GCC is needed for compiled-C tests")
class TestCompiledC(unittest.TestCase):
    def check_compiled(self, graph, parameter_names, inputs):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "kernel.c"
            library_path = Path(directory) / "kernel.so"
            source_path.write_text(render_c(graph), encoding="utf-8")
            subprocess.run(
                [
                    CC,
                    "-std=c11",
                    "-O0",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-Wshadow",
                    "-Wstrict-prototypes",
                    "-pedantic",
                    "-shared",
                    "-fPIC",
                    str(source_path),
                    "-o",
                    str(library_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Only load trusted generated code.
            library = ctypes.CDLL(str(library_path))
            function = library.kernel
            function.argtypes = [ctypes.c_int32] * len(parameter_names)
            function.restype = ctypes.c_int32
            for params in inputs:
                with self.subTest(params=params):
                    actual = function(*(params[name] for name in parameter_names))
                    self.assertEqual(actual, evaluate(graph, params))

    def test_example(self):
        self.check_compiled(build_graph(), ["x"], [{"x": x} for x in (4, 0, -2, 100)])

    def test_literal_boundaries(self):
        for value in (0, -7, -(2**31), 2**31 - 1):
            with self.subTest(value=value):
                self.check_compiled(UOp(Op.CONST, arg=value), [], [{}])

    def test_multiple_parameters(self):
        b, a = UOp(Op.PARAM, arg="b"), UOp(Op.PARAM, arg="a")
        graph = UOp(Op.ADD, src=(UOp(Op.MUL, src=(b, a)), a))
        rng = random.Random(0)
        inputs = [
            {"b": rng.randint(-100, 100), "a": rng.randint(-100, 100)}
            for _ in range(100)
        ]
        self.check_compiled(graph, ["b", "a"], inputs)

    def test_shared_expression(self):
        x = UOp(Op.PARAM, arg="x")
        shared = UOp(Op.ADD, src=(x, UOp(Op.CONST, arg=1)))
        self.check_compiled(
            UOp(Op.MUL, src=(shared, shared)), ["x"], [{"x": x} for x in (-3, 0, 4)]
        )

    def test_temporary_collision(self):
        graph = UOp(Op.ADD, src=(UOp(Op.PARAM, arg="t0"), UOp(Op.CONST, arg=-1)))
        self.check_compiled(graph, ["t0"], [{"t0": 5}])

    def test_duplicate_parameter_name(self):
        graph = UOp(Op.ADD, src=(UOp(Op.PARAM, arg="x"), UOp(Op.PARAM, arg="x")))
        self.check_compiled(graph, ["x"], [{"x": 7}])


if __name__ == "__main__":
    unittest.main()
