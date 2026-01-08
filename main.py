import sys
from zero.lexer import tokenize
from zero.parser import parse
from zero.semantic import analyze, SemanticError
from zero.compiler import compile_program
from zero.vm import run
from zero.bytecode import Op, BUILTINS


def disassemble_chunk(name, idx, chunk, function_index):
    idx_to_name = {v: k for k, v in function_index.items()}

    print(f"== {name} (index={idx}, arity={chunk.arity}) ==")
    if chunk.constants:
        print(f"constants: {chunk.constants}")

    i = 0
    while i < len(chunk.code):
        op = Op(chunk.code[i])
        match op:
            case Op.CONST:
                const_idx = chunk.code[i + 1]
                print(f"  {i:04d} CONST {const_idx} ({chunk.constants[const_idx]})")
                i += 2
            case Op.LOAD:
                slot = chunk.code[i + 1]
                print(f"  {i:04d} LOAD {slot}")
                i += 2
            case Op.ADD:
                print(f"  {i:04d} ADD")
                i += 1
            case Op.CALL:
                func_idx = chunk.code[i + 1]
                argc = chunk.code[i + 2]
                func_name = idx_to_name.get(func_idx, f"<{func_idx}>")
                print(f"  {i:04d} CALL {func_idx} ({func_name}), {argc} args")
                i += 3
            case Op.RET:
                print(f"  {i:04d} RET")
                i += 1
            case Op.POP:
                print(f"  {i:04d} POP")
                i += 1
            case Op.CALL_BUILTIN:
                builtin_idx = chunk.code[i + 1]
                argc = chunk.code[i + 2]
                builtin_name = next(
                    (k for k, v in BUILTINS.items() if v == builtin_idx),
                    f"<builtin {builtin_idx}>"
                )
                print(f"  {i:04d} CALL_BUILTIN {builtin_idx} ({builtin_name}), {argc} args")
                i += 3
    print()


def disassemble(compiled):
    for name, idx in compiled.function_index.items():
        disassemble_chunk(name, idx, compiled.chunks[idx], compiled.function_index)


def main():
    if len(sys.argv) < 2:
        print("Usage: zero [-d] <file.zero>")
        print("  -d  Disassemble only (don't run)")
        sys.exit(1)

    disassemble_mode = False
    file_arg = 1

    if sys.argv[1] == "-d":
        disassemble_mode = True
        file_arg = 2
        if len(sys.argv) < 3:
            print("Usage: zero [-d] <file.zero>")
            sys.exit(1)

    source = open(sys.argv[file_arg]).read()

    tokens = tokenize(source)
    program = parse(tokens)

    try:
        analyze(program)
    except SemanticError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    compiled = compile_program(program)

    if disassemble_mode:
        disassemble(compiled)
    else:
        run(compiled)


if __name__ == "__main__":
    main()
