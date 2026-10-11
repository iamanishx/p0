# p0: A Tiny UOp-to-C Compiler

A compiler-learning project written in Python. The goal is to represent computations as a graph, simplify that graph, and generate equivalent C code.

Inspired by tinygrad's UOp-based IR, but this is a small independent teaching implementation—not a tinygrad clone or a general Python-to-C compiler.

## Current status

**Step 3: C code generation.** We can describe, validate, interpret, and compile scalar integer expression graphs to C11 source. The IR supports four operations: `CONST`, `PARAM`, `ADD`, and `MUL`.

The example builds the graph for `x * (2 + 3)`, evaluates it with `x = 4` to produce `20`, and independently generates C:

```text
PARAM(x) ────────────┐
                    MUL → result
CONST(2) ──┐        │
           ADD ─────┘
CONST(3) ──┘
```

Constructing this graph does **not** execute the expression. Calling `evaluate(graph, {"x": 4})` executes it in Python. Calling `render_c(graph)` generates source without evaluating the graph or requiring runtime parameter values. Neither changes the graph. Our compiler does not optimize yet; Clang/GCC may optimize the generated C later.

Generated source:

```c
#include <stdint.h>

int32_t kernel(int32_t x) {
    int32_t t0 = (INT32_C(2) + INT32_C(3));
    int32_t t1 = (x * t0);
    return t1;
}
```

Each arithmetic node becomes a temporary variable. Shared graph nodes are emitted once, and parameter arguments are ordered by their first encounter in input-first traversal.

## What is a UOp?

A UOp is one operation in our intermediate representation (IR):

```python
UOp(op, src=(), arg=None)
```

- `op`: which operation the node describes.
- `src`: the input nodes, in order.
- `arg`: extra information, such as an integer constant or parameter name.

For example, this describes `2 + 3` without computing it:

```python
from compiler.ir import Op, UOp

two = UOp(Op.CONST, arg=2)
three = UOp(Op.CONST, arg=3)
addition = UOp(Op.ADD, src=(two, three))
```

Nodes can share inputs, so the representation is a graph, not necessarily a tree. Nodes are immutable. A separate validation pass checks node structure, arity, argument types, and cycles before C generation. The renderer additionally checks C identifiers, name collisions, and constant range.

## Run

Requires Python 3.10+; no third-party Python dependencies or GPU are needed. GCC or Clang is needed to compile and run generated C. Native execution tests use Linux-style shared libraries; they skip when neither compiler is installed.

From the repository root:

```bash
# Show the graph, interpreter result, and generated C.
python3 -m example.simple

# Generate source, compile it with a small C caller, and run the executable.
# Substitute clang for gcc if desired.
python3 -m example.simple --emit-c > /tmp/p0-kernel.c
gcc -std=c11 -Wall -Wextra -Werror -pedantic \
    /tmp/p0-kernel.c example/run_kernel.c -o /tmp/p0-demo
/tmp/p0-demo
# kernel(4) = 20

# Run Python and compiled-C correctness tests.
python3 -m unittest discover -s test -v
```

## Integer semantics and current limits

The interpreter uses arbitrary-precision Python integers. Generated C uses `int32_t`: parameters and **every intermediate result** must fit in the signed 32-bit range. Out-of-range constants are rejected, but runtime overflow is not checked and C signed overflow is undefined. Tests use values within this supported range; fixed-width semantics are future work.

This version supports pure scalar expressions only. There are no loops, arrays, memory effects, parser, or optimization passes. C names are restricted to non-reserved ASCII identifiers, and generated names cannot shadow parameters.

## Project layout

```text
compiler/ir.py          Operation definitions and immutable graph nodes
compiler/interpret.py   Python evaluation (correctness reference)
compiler/validate.py    Graph validation and input-first traversal
compiler/render_c.py    C11 source generation
example/simple.py       Build, evaluate, and render x * (2 + 3)
example/run_kernel.c    C caller for the generated function
test/test_ir.py         Graph construction tests
test/test_interpret.py  Evaluation and error-handling tests
test/test_validate.py   Validation and traversal tests
test/test_render_c.py   Source checks and native execution comparisons
```

## Roadmap

- [x] Define the IR and construct an example graph.
- [x] Interpret the graph using supplied parameter values.
- [x] Validate operations and scalar integer arguments.
- [ ] Add constant folding: `2 + 3` → `5`.
- [x] Render equivalent C functions.
- [x] Compile the generated C with Clang/GCC and compare results with the interpreter.
- [ ] Add a small textual IR parser and printer.

The intended compilation path is:

```text
UOp graph → validation / rewrites → C source → Clang/GCC → machine code
```

The interpreter provides a correctness reference for future rewrites and code generation. A parser or DSL frontend can be added later; for now, programs are built directly as UOp graphs in Python.
