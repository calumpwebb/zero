from dataclasses import dataclass
from enum import IntEnum


class Op(IntEnum):
    # === Stack/Memory ===
    CONST = 0            # Push constant from pool
    LOAD = 1             # Load local variable
    STORE = 2            # Store to local variable
    POP = 3              # Discard top of stack

    # === Integer Arithmetic ===
    ADD_INT = 10         # Pop two ints, push sum
    SUB_INT = 11         # Pop two ints, push difference
    MUL_INT = 12         # Pop two ints, push product
    MOD_INT = 13         # Pop two ints, push remainder
    # DIV_INT = 14       # Future: integer division

    # === String Operations ===
    ADD_STR = 20         # Pop two strings, push concatenation

    # === Integer Comparisons ===
    CMP_EQ_INT = 30      # Pop two ints, push true if equal
    CMP_NE_INT = 31      # Pop two ints, push true if not equal
    CMP_LT_INT = 32      # Pop two ints, push true if a < b
    CMP_GT_INT = 33      # Pop two ints, push true if a > b
    CMP_LE_INT = 34      # Pop two ints, push true if a <= b
    CMP_GE_INT = 35      # Pop two ints, push true if a >= b

    # === Bool Comparisons ===
    CMP_EQ_BOOL = 40     # Pop two bools, push true if equal
    CMP_NE_BOOL = 41     # Pop two bools, push true if not equal

    # === String Comparisons ===
    CMP_EQ_STR = 50      # Pop two strings, push true if equal
    CMP_NE_STR = 51      # Pop two strings, push true if not equal

    # === Control Flow ===
    JUMP = 60            # Unconditional jump to address
    JUMP_IF_FALSE = 61   # Pop value, jump if false

    # === Functions ===
    CALL = 70            # Call function
    CALL_BUILTIN = 71    # Call builtin function
    RET = 72             # Return from function


@dataclass
class Chunk:
    code: list[int]       # Opcodes and operands interleaved
    constants: list[int]  # Constant pool
    arity: int            # Number of parameters


@dataclass
class CompiledProgram:
    chunks: list[Chunk]
    function_index: dict[str, int]  # Function name -> chunk index
