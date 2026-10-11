from dataclasses import dataclass
from enum import Enum, auto


class Op(Enum):
    CONST = auto()
    PARAM = auto()
    ADD = auto()
    MUL = auto()


@dataclass(frozen=True)
class UOp:
    op: Op
    src: tuple["UOp", ...] = ()
    arg: int | str | None = None
