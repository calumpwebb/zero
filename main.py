from pathlib import Path

import typer

from zero.bytecode import load_program, save_program
from zero.cache import ensure_cache_dir
from zero.compiler import compile_program
from zero.lexer import tokenize
from zero.parser import parse
from zero.semantic import SemanticError, analyze
from zero.vm import run as vm_run

app = typer.Typer(help="The Zero programming language")


def compile_source(source_path: Path):
    """Compile source file to CompiledProgram."""
    source = source_path.read_text()
    tokens = tokenize(source)
    program = parse(tokens)
    analyze(program)
    return compile_program(program)


@app.command()
def build(
    file: Path = typer.Argument(..., help="Source file to compile (.zr)"),
    output: Path | None = typer.Option(None, "-o", "--output", help="Output path"),
):
    """Compile a .zr file to bytecode."""
    if file.suffix != ".zr":
        typer.echo(f"Error: expected .zr file, got {file.suffix}", err=True)
        raise typer.Exit(1)

    if not file.exists():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(1)

    try:
        compiled = compile_source(file)
    except SemanticError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    out_path = output if output else ensure_cache_dir(file)
    save_program(compiled, out_path)
    typer.echo(f"Compiled to {out_path}")


@app.command(name="run")
def run_cmd(
    file: Path = typer.Argument(..., help="File to run (.zr or .zrc)"),
):
    """Run a .zr or .zrc file."""
    if not file.exists():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(1)

    try:
        if file.suffix == ".zr":
            compiled = compile_source(file)
        elif file.suffix == ".zrc":
            compiled = load_program(file)
        else:
            typer.echo(f"Error: expected .zr or .zrc file, got {file.suffix}", err=True)
            raise typer.Exit(1)
    except SemanticError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    vm_run(compiled)


@app.command()
def disasm(
    file: Path = typer.Argument(..., help="File to disassemble (.zr or .zrc)"),
):
    """Disassemble a .zr or .zrc file."""
    if not file.exists():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(1)

    try:
        if file.suffix == ".zr":
            compiled = compile_source(file)
        elif file.suffix == ".zrc":
            compiled = load_program(file)
        else:
            typer.echo(f"Error: expected .zr or .zrc file, got {file.suffix}", err=True)
            raise typer.Exit(1)
    except SemanticError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    disassemble(compiled)


def disassemble(compiled):
    """Print disassembly of compiled program."""
    from zero.builtins import BUILTIN_INDICES
    from zero.bytecode import Op

    idx_to_name = {v: k for k, v in compiled.function_index.items()}

    for name, idx in compiled.function_index.items():
        chunk = compiled.chunks[idx]
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
                case Op.STORE:
                    slot = chunk.code[i + 1]
                    print(f"  {i:04d} STORE {slot}")
                    i += 2
                case Op.ADD_INT:
                    print(f"  {i:04d} ADD_INT")
                    i += 1
                case Op.SUB_INT:
                    print(f"  {i:04d} SUB_INT")
                    i += 1
                case Op.MUL_INT:
                    print(f"  {i:04d} MUL_INT")
                    i += 1
                case Op.MOD_INT:
                    print(f"  {i:04d} MOD_INT")
                    i += 1
                case Op.ADD_STR:
                    print(f"  {i:04d} ADD_STR")
                    i += 1
                case Op.CMP_EQ_INT:
                    print(f"  {i:04d} CMP_EQ_INT")
                    i += 1
                case Op.CMP_NE_INT:
                    print(f"  {i:04d} CMP_NE_INT")
                    i += 1
                case Op.CMP_LT_INT:
                    print(f"  {i:04d} CMP_LT_INT")
                    i += 1
                case Op.CMP_GT_INT:
                    print(f"  {i:04d} CMP_GT_INT")
                    i += 1
                case Op.CMP_LE_INT:
                    print(f"  {i:04d} CMP_LE_INT")
                    i += 1
                case Op.CMP_GE_INT:
                    print(f"  {i:04d} CMP_GE_INT")
                    i += 1
                case Op.CMP_EQ_BOOL:
                    print(f"  {i:04d} CMP_EQ_BOOL")
                    i += 1
                case Op.CMP_NE_BOOL:
                    print(f"  {i:04d} CMP_NE_BOOL")
                    i += 1
                case Op.CMP_EQ_STR:
                    print(f"  {i:04d} CMP_EQ_STR")
                    i += 1
                case Op.CMP_NE_STR:
                    print(f"  {i:04d} CMP_NE_STR")
                    i += 1
                case Op.JUMP:
                    addr = chunk.code[i + 1]
                    print(f"  {i:04d} JUMP {addr}")
                    i += 2
                case Op.JUMP_IF_FALSE:
                    addr = chunk.code[i + 1]
                    print(f"  {i:04d} JUMP_IF_FALSE {addr}")
                    i += 2
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
                        (k for k, v in BUILTIN_INDICES.items() if v == builtin_idx),
                        f"<builtin {builtin_idx}>"
                    )
                    print(f"  {i:04d} CALL_BUILTIN {builtin_idx} ({builtin_name}), {argc} args")
                    i += 3
        print()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """The Zero programming language."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
