"""Run all example Zero programs."""

from pathlib import Path

from zero.compiler import compile_program
from zero.lexer import tokenize
from zero.parser import parse
from zero.semantic import analyze
from zero.vm import run


def main() -> None:
    examples_dir = Path(__file__).parent / "examples"
    for path in sorted(examples_dir.glob("*.zero")):
        print(f"--- {path.name} ---")
        source = path.read_text()
        tokens = tokenize(source)
        program = parse(tokens)
        analyze(program)
        compiled = compile_program(program)
        run(compiled)
        print()


if __name__ == "__main__":
    main()
