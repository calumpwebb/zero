import dataclasses
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

import msgpack

BYTECODE_VERSION = 1
MAX_BYTECODE_SIZE = 10 * 1024 * 1024  # 10MB


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


def save_program(program: CompiledProgram, path: Path) -> None:
    """Serialize compiled program to bytecode file."""
    data = {
        "version": BYTECODE_VERSION,
        "program": dataclasses.asdict(program),
    }
    with open(path, "wb") as f:
        msgpack.pack(data, f, use_bin_type=True)


def load_program(path: Path) -> CompiledProgram:
    """Load compiled program from bytecode file."""
    file_size = path.stat().st_size
    if file_size > MAX_BYTECODE_SIZE:
        raise ValueError(f"Bytecode file too large: {file_size} bytes (max {MAX_BYTECODE_SIZE})")

    with open(path, "rb") as f:
        data = msgpack.unpack(f, raw=False, strict_map_key=False)

    if data["version"] != BYTECODE_VERSION:
        raise ValueError(
            f"Bytecode version mismatch: file has v{data['version']}, "
            f"VM expects v{BYTECODE_VERSION}. Recompile your source."
        )

    p = data["program"]
    return CompiledProgram(
        chunks=[Chunk(**c) for c in p["chunks"]],
        function_index=p["function_index"],
    )
