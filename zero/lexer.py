from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Keywords
    FN = auto()
    RETURN = auto()

    # Literals
    INT = auto()

    # Identifiers
    IDENT = auto()

    # Symbols
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COLON = auto()
    COMMA = auto()
    PLUS = auto()

    # End
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str | int | None = None


KEYWORDS = {
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
}

SYMBOLS = {
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    ":": TokenType.COLON,
    ",": TokenType.COMMA,
    "+": TokenType.PLUS,
}


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0

    def tokenize(self) -> list[Token]:
        tokens = []
        while not self.at_end():
            token = self.next_token()
            if token:
                tokens.append(token)
        return tokens

    def at_end(self) -> bool:
        return self.pos >= len(self.source)

    def current(self) -> str:
        return self.source[self.pos]

    def advance(self) -> str:
        char = self.source[self.pos]
        self.pos += 1
        return char

    def next_token(self) -> Token | None:
        if self.at_end():
            return None

        char = self.current()

        if char.isspace():
            self.advance()
            return None

        if char == "#":
            self.skip_comment()
            return None

        if char.isdigit():
            return self.read_number()

        if char.isalpha() or char == "_":
            return self.read_identifier()

        if char in SYMBOLS:
            self.advance()
            return Token(SYMBOLS[char])

        raise SyntaxError(f"Unexpected character: {char}")

    def skip_comment(self):
        while not self.at_end() and self.current() != "\n":
            self.advance()

    def read_number(self) -> Token:
        digits = ""
        while not self.at_end() and self.current().isdigit():
            digits += self.advance()
        return Token(TokenType.INT, int(digits))

    def read_identifier(self) -> Token:
        ident = ""
        while not self.at_end() and (self.current().isalnum() or self.current() == "_"):
            ident += self.advance()
        if ident in KEYWORDS:
            return Token(KEYWORDS[ident])
        return Token(TokenType.IDENT, ident)


def tokenize(source: str) -> list[Token]:
    return Lexer(source).tokenize()
