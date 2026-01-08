from zero.lexer import Token, TokenType
from zero.ast import (
    Program,
    Function,
    Param,
    ReturnStmt,
    ExprStmt,
    BinaryExpr,
    Call,
    IntLiteral,
    BoolLiteral,
    StringLiteral,
    Identifier,
)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos >= len(self.tokens):
            return Token(TokenType.EOF)
        return self.tokens[self.pos]

    def peek(self, offset=0):
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return Token(TokenType.EOF)
        return self.tokens[pos]

    def advance(self):
        token = self.current()
        self.pos += 1
        return token

    def check(self, type):
        return self.current().type == type

    def match(self, type):
        if self.check(type):
            self.advance()
            return True
        return False

    def expect(self, type, message):
        if not self.check(type):
            raise SyntaxError(message)
        return self.advance()

    def at_end(self):
        return self.check(TokenType.EOF)

    def parse_expression(self):
        return self.parse_additive()

    def parse_additive(self):
        left = self.parse_call()

        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            if self.match(TokenType.PLUS):
                right = self.parse_call()
                left = BinaryExpr("+", left, right)
            elif self.match(TokenType.MINUS):
                right = self.parse_call()
                left = BinaryExpr("-", left, right)

        return left

    def parse_call(self):
        expr = self.parse_primary()

        if isinstance(expr, Identifier) and self.match(TokenType.LPAREN):
            args = self.parse_arguments()
            self.expect(TokenType.RPAREN, "Expected ')' after arguments")
            return Call(expr.name, args)

        return expr

    def parse_arguments(self):
        args = []

        if not self.check(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                args.append(self.parse_expression())

        return args

    def parse_primary(self):
        token = self.current()

        if token.type == TokenType.INT:
            self.advance()
            return IntLiteral(token.value)

        if token.type == TokenType.TRUE:
            self.advance()
            return BoolLiteral(True)

        if token.type == TokenType.FALSE:
            self.advance()
            return BoolLiteral(False)

        if token.type == TokenType.STRING:
            self.advance()
            return StringLiteral(token.value)

        if token.type == TokenType.IDENT:
            self.advance()
            return Identifier(token.value)

        if self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        raise SyntaxError(f"Unexpected token: {token.type}")

    def parse_statement(self):
        if self.match(TokenType.RETURN):
            expr = self.parse_expression()
            return ReturnStmt(expr)

        expr = self.parse_expression()
        return ExprStmt(expr)

    def parse_params(self):
        params = []

        if self.check(TokenType.EOF) or self.check(TokenType.RPAREN):
            return params

        params.append(self.parse_param())

        while self.match(TokenType.COMMA):
            params.append(self.parse_param())

        return params

    def parse_param(self):
        name_token = self.expect(TokenType.IDENT, "Expected parameter name")
        self.expect(TokenType.COLON, "Expected ':' after parameter name")
        type_token = self.expect(TokenType.IDENT, "Expected parameter type")
        return Param(name_token.value, type_token.value)

    def parse_function(self):
        self.expect(TokenType.FN, "Expected 'fn'")
        name_token = self.expect(TokenType.IDENT, "Expected function name")
        name = name_token.value

        self.expect(TokenType.LPAREN, "Expected '(' after function name")
        params = self.parse_params()
        self.expect(TokenType.RPAREN, "Expected ')' after parameters")

        return_type = None
        if self.match(TokenType.COLON):
            type_token = self.expect(TokenType.IDENT, "Expected return type")
            return_type = type_token.value

        self.expect(TokenType.LBRACE, "Expected '{' before function body")
        body = self.parse_block()
        self.expect(TokenType.RBRACE, "Expected '}' after function body")

        return Function(name, params, return_type, body)

    def parse_block(self):
        statements = []

        while not self.check(TokenType.RBRACE) and not self.at_end():
            statements.append(self.parse_statement())

        return statements

    def parse_program(self):
        functions = []

        while not self.at_end():
            functions.append(self.parse_function())

        return Program(functions)


def parse(tokens):
    return Parser(tokens).parse_program()
