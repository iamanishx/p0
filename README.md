# p0: A Tiny UOp-to-C Compiler

A compiler-learning project written in Python. The goal is to represent computations as a graph, simplify that graph, and generate equivalent C code.

Inspired by tinygrad's UOp-based IR, but this is a small independent teaching implementation—not a tinygrad clone or a general Python-to-C compiler.

## Current status

**Step 1: graph construction.** We can describe scalar integer expressions using immutable UOp nodes with four operations: `CONST`, `PARAM`, `ADD`, and `MUL`.

The example builds and prints the graph for `x * (2 + 3)`:

```text
PARAM(x) ────────────┐
                    MUL → result
CONST(2) ──┐        │
           ADD ─────┘
CONST(3) ──┘
```

Constructing this graph does **not** execute the expression. Evaluation, optimization, and C generation are not implemented yet.

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

Nodes can share inputs, so the representation is a graph, not necessarily a tree. Nodes are immutable, but validation of operation arity and argument types is not implemented yet.

## Roadmap

- [x] Define the IR and construct an example graph.
- [ ] Interpret the graph using supplied parameter values.
- [ ] Validate operations and types.
- [ ] Add constant folding: `2 + 3` → `5`.
- [ ] Render equivalent C functions.
- [ ] Compile the generated C with Clang/GCC and compare results with the interpreter.
- [ ] Add a small textual IR parser and printer.

The intended compilation path is:

```text
UOp graph → validation / rewrites → C source → Clang/GCC → machine code
```

The interpreter will provide a correctness reference. A parser or DSL frontend can be added later; for now, programs are built directly as UOp graphs in Python.
