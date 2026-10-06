from dataclasses import dataclass
from enum import Enum, auto


class Op(Enum):
    CONST = auto()  # A literal integer, such as 2.
    PARAM = auto()  # An input supplied when the program runs, such as x.
    ADD = auto()    # Add two input values.
    MUL = auto()    # Multiply two input values.


@dataclass(frozen=True)
class UOp:
    op: Op
    src: tuple["UOp", ...] = ()
    arg: int | str | None = None
