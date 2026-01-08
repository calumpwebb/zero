from dataclasses import dataclass, field
from enum import Enum, auto


class TokenType(Enum):
    FN = auto()
    RETURN = auto()
    TRUE = auto()
    FALSE = auto()
    INT = auto()
    STRING = auto()
    IDENT = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COLON = auto()
    COMMA = auto()
    PLUS = auto()
    MINUS = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: object = None


KEYWORDS = {
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
}

SYMBOLS = {
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    ":": TokenType.COLON,
    ",": TokenType.COMMA,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
}


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0

    def tokenize(self):
        tokens = []
        while not self.at_end():
            token = self.next_token()
            if token:
                tokens.append(token)
        tokens.append(Token(TokenType.EOF))
        return tokens

    def at_end(self):
        return self.pos >= len(self.source)

    def current(self):
        return self.source[self.pos]

    def advance(self):
        char = self.source[self.pos]
        self.pos += 1
        return char

    def next_token(self):
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

        if char == '"':
            return self.read_string()

        if char.isalpha() or char == "_":
            return self.read_identifier()

        if char in SYMBOLS:
            self.advance()
            return Token(SYMBOLS[char])

        raise SyntaxError(f"Unexpected character: {char}")

    def skip_comment(self):
        while not self.at_end() and self.current() != "\n":
            self.advance()

    def read_number(self):
        digits = ""
        while not self.at_end() and self.current().isdigit():
            digits += self.advance()
        return Token(TokenType.INT, int(digits))

    def read_string(self):
        self.advance()  # consume opening "
        chars = ""
        while not self.at_end() and self.current() != '"':
            chars += self.advance()
        if self.at_end():
            raise SyntaxError("Unterminated string literal")
        self.advance()  # consume closing "
        return Token(TokenType.STRING, chars)

    def read_identifier(self):
        ident = ""
        while not self.at_end() and (self.current().isalnum() or self.current() == "_"):
            ident += self.advance()
        if ident in KEYWORDS:
            return Token(KEYWORDS[ident])
        return Token(TokenType.IDENT, ident)


def tokenize(source):
    return Lexer(source).tokenize()
