from dataclasses import dataclass, field
from enum import Enum, auto


class TokenType(Enum):
    FN = auto()
    RETURN = auto()
    TRUE = auto()
    FALSE = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    BREAK = auto()
    CONTINUE = auto()
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
    STAR = auto()
    PERCENT = auto()
    PLUS_EQUAL = auto()
    MINUS_EQUAL = auto()
    ASSIGN = auto()
    EQ = auto()
    NE = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: object = None
    line: int = field(default=1, compare=False)
    column: int = field(default=1, compare=False)


KEYWORDS = {
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "for": TokenType.FOR,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
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
    "*": TokenType.STAR,
    "%": TokenType.PERCENT,
}


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1

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

    def peek(self, offset=1):
        pos = self.pos + offset
        if pos >= len(self.source):
            return "\0"
        return self.source[pos]

    def advance(self):
        char = self.source[self.pos]
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def make_token(self, token_type, value=None):
        """Create a token with the saved start position."""
        return Token(token_type, value, self.start_line, self.start_column)

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

        # Save position at start of token
        self.start_line = self.line
        self.start_column = self.column

        if char.isdigit():
            return self.read_number()

        if char == '"':
            return self.read_string()

        if char.isalpha() or char == "_":
            return self.read_identifier()

        # Multi-character operators
        if char == "=" and self.peek() == "=":
            self.advance()
            self.advance()
            return self.make_token(TokenType.EQ)
        if char == "!" and self.peek() == "=":
            self.advance()
            self.advance()
            return self.make_token(TokenType.NE)
        if char == "<" and self.peek() == "=":
            self.advance()
            self.advance()
            return self.make_token(TokenType.LE)
        if char == ">" and self.peek() == "=":
            self.advance()
            self.advance()
            return self.make_token(TokenType.GE)
        if char == "+" and self.peek() == "=":
            self.advance()
            self.advance()
            return self.make_token(TokenType.PLUS_EQUAL)
        if char == "-" and self.peek() == "=":
            self.advance()
            self.advance()
            return self.make_token(TokenType.MINUS_EQUAL)

        # Single-character operators
        if char == "=":
            self.advance()
            return self.make_token(TokenType.ASSIGN)
        if char == "<":
            self.advance()
            return self.make_token(TokenType.LT)
        if char == ">":
            self.advance()
            return self.make_token(TokenType.GT)

        if char in SYMBOLS:
            self.advance()
            return self.make_token(SYMBOLS[char])

        raise SyntaxError(f"Unexpected character: {char}")

    def skip_comment(self):
        while not self.at_end() and self.current() != "\n":
            self.advance()

    def read_number(self):
        digits = ""
        while not self.at_end() and self.current().isdigit():
            digits += self.advance()
        value = int(digits)
        if value > 9223372036854775807:  # i64 max
            raise SyntaxError(f"Integer too large: {digits}")
        return self.make_token(TokenType.INT, value)

    def read_string(self):
        self.advance()  # consume opening "
        chars = ""
        while not self.at_end() and self.current() != '"':
            chars += self.advance()
        if self.at_end():
            raise SyntaxError("Unterminated string literal")
        self.advance()  # consume closing "
        return self.make_token(TokenType.STRING, chars)

    def read_identifier(self):
        ident = ""
        while not self.at_end() and (self.current().isalnum() or self.current() == "_"):
            ident += self.advance()
        if ident in KEYWORDS:
            return self.make_token(KEYWORDS[ident])
        return self.make_token(TokenType.IDENT, ident)


def tokenize(source):
    return Lexer(source).tokenize()
