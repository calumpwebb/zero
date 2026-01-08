from dataclasses import dataclass
from enum import IntEnum


class Op(IntEnum):
    CONST = 0         # Push constant from pool
    LOAD = 1          # Load local variable
    ADD_INT = 2       # Pop two ints, push sum
    SUB_INT = 3       # Pop two ints, push difference
    CALL = 4          # Call function
    RET = 5           # Return from function
    POP = 6           # Discard top of stack
    CALL_BUILTIN = 7  # Call builtin function
    ADD_STR = 8       # Pop two strings, push concatenation


# Builtin function indices
BUILTINS = {
    "print": 0,
}


@dataclass
class Chunk:
    code: list[int]       # Opcodes and operands interleaved
    constants: list[int]  # Constant pool
    arity: int            # Number of parameters


@dataclass
class CompiledProgram:
    chunks: list[Chunk]
    function_index: dict[str, int]  # Function name -> chunk index
