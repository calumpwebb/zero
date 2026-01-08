import sys
from zero.lexer import tokenize


def main():
    if len(sys.argv) < 2:
        print("Usage: zero <file.zero>")
        sys.exit(1)

    source = open(sys.argv[1]).read()
    tokens = tokenize(source)

    for token in tokens:
        print(token)

    print("hello  world")

if __name__ == "__main__":
    main()
