from dataclasses import fields

from zero.lexer import Token, TokenType
from zero.ast import (
    Program,
    Function,
    Param,
    ReturnStmt,
    ExprStmt,
    BinaryExpr,
    UnaryExpr,
    Call,
    IntLiteral,
    BoolLiteral,
    StringLiteral,
    Identifier,
    VarDecl,
    Assignment,
    IfStmt,
    ForStmt,
    BreakStmt,
    ContinueStmt,
    Span,
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

    def _make_span_from_expr(self, start_token, expr):
        """Create a span from a start token to the end of an expression."""
        if expr.span:
            return Span(start_token.line, start_token.column, expr.span.end_line, expr.span.end_column)
        # Fallback if expression has no span
        return Span(start_token.line, start_token.column, start_token.line, start_token.column)

    def _span_from_nodes(self, left, right):
        """Create a span that covers both left and right nodes."""
        if left.span and right.span:
            return Span(left.span.start_line, left.span.start_column, right.span.end_line, right.span.end_column)
        if left.span:
            return left.span
        if right.span:
            return right.span
        return None

    def parse_expression(self):
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_additive()

        # Non-associative: only parse one comparison operator
        if self.check(TokenType.EQ):
            self.advance()
            right = self.parse_additive()
            span = self._span_from_nodes(left, right)
            return BinaryExpr("==", left, right, span=span)
        if self.check(TokenType.NE):
            self.advance()
            right = self.parse_additive()
            span = self._span_from_nodes(left, right)
            return BinaryExpr("!=", left, right, span=span)
        if self.check(TokenType.LT):
            self.advance()
            right = self.parse_additive()
            span = self._span_from_nodes(left, right)
            return BinaryExpr("<", left, right, span=span)
        if self.check(TokenType.GT):
            self.advance()
            right = self.parse_additive()
            span = self._span_from_nodes(left, right)
            return BinaryExpr(">", left, right, span=span)
        if self.check(TokenType.LE):
            self.advance()
            right = self.parse_additive()
            span = self._span_from_nodes(left, right)
            return BinaryExpr("<=", left, right, span=span)
        if self.check(TokenType.GE):
            self.advance()
            right = self.parse_additive()
            span = self._span_from_nodes(left, right)
            return BinaryExpr(">=", left, right, span=span)

        return left

    def parse_additive(self):
        left = self.parse_multiplicative()

        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            if self.match(TokenType.PLUS):
                right = self.parse_multiplicative()
                span = self._span_from_nodes(left, right)
                left = BinaryExpr("+", left, right, span=span)
            elif self.match(TokenType.MINUS):
                right = self.parse_multiplicative()
                span = self._span_from_nodes(left, right)
                left = BinaryExpr("-", left, right, span=span)

        return left

    def parse_multiplicative(self):
        left = self.parse_unary()

        while self.check(TokenType.STAR) or self.check(TokenType.PERCENT):
            if self.match(TokenType.STAR):
                right = self.parse_unary()
                span = self._span_from_nodes(left, right)
                left = BinaryExpr("*", left, right, span=span)
            elif self.match(TokenType.PERCENT):
                right = self.parse_unary()
                span = self._span_from_nodes(left, right)
                left = BinaryExpr("%", left, right, span=span)

        return left

    def parse_unary(self):
        if self.check(TokenType.MINUS):
            minus_token = self.advance()
            operand = self.parse_unary()  # right-associative
            if operand.span:
                span = Span(minus_token.line, minus_token.column, operand.span.end_line, operand.span.end_column)
            else:
                span = Span(minus_token.line, minus_token.column, minus_token.line, minus_token.column)
            return UnaryExpr("-", operand, span=span)
        return self.parse_call()

    def parse_call(self):
        # Store start position before parsing primary (in case it's a call)
        start_token = self.current()
        expr = self.parse_primary()

        if isinstance(expr, Identifier) and self.match(TokenType.LPAREN):
            args = self.parse_arguments()
            rparen_token = self.expect(TokenType.RPAREN, "Expected ')' after arguments")
            # Span from identifier start to closing paren end
            call_span = Span(
                start_token.line,
                start_token.column,
                rparen_token.line,
                rparen_token.column,  # end column is after the ')'
            )
            return Call(expr.name, args, span=call_span)

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
            value_str = str(token.value)
            span = Span(token.line, token.column, token.line, token.column + len(value_str) - 1)
            return IntLiteral(token.value, span=span)

        if token.type == TokenType.TRUE:
            self.advance()
            span = Span(token.line, token.column, token.line, token.column + 3)  # "true" is 4 chars
            return BoolLiteral(True, span=span)

        if token.type == TokenType.FALSE:
            self.advance()
            span = Span(token.line, token.column, token.line, token.column + 4)  # "false" is 5 chars
            return BoolLiteral(False, span=span)

        if token.type == TokenType.STRING:
            self.advance()
            # String includes quotes in source, so add 2 for the quotes
            span = Span(token.line, token.column, token.line, token.column + len(token.value) + 1)
            return StringLiteral(token.value, span=span)

        if token.type == TokenType.IDENT:
            self.advance()
            span = Span(token.line, token.column, token.line, token.column + len(token.value) - 1)
            return Identifier(token.value, span=span)

        if self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        raise SyntaxError(f"Unexpected token: {token.type}")

    def parse_statement(self):
        start_token = self.current()

        if self.check(TokenType.RETURN):
            return_token = self.advance()
            expr = self.parse_expression()
            stmt_span = self._make_span_from_expr(return_token, expr)
            return ReturnStmt(expr, span=stmt_span)

        # Check for if statement: "if" "(" expr ")" block [ "else" block ]
        if self.check(TokenType.IF):
            if_token = self.advance()
            self.expect(TokenType.LPAREN, "Expected '(' after 'if'")
            condition = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')' after condition")
            self.expect(TokenType.LBRACE, "Expected '{' before then block")
            then_body = self.parse_block()
            end_token = self.expect(TokenType.RBRACE, "Expected '}' after then block")

            else_body = None
            if self.match(TokenType.ELSE):
                self.expect(TokenType.LBRACE, "Expected '{' before else block")
                else_body = self.parse_block()
                end_token = self.expect(TokenType.RBRACE, "Expected '}' after else block")

            stmt_span = Span(if_token.line, if_token.column, end_token.line, end_token.column)
            return IfStmt(condition, then_body, else_body, span=stmt_span)

        # Check for for loop: "for" "(" expr ")" block
        if self.check(TokenType.FOR):
            for_token = self.advance()
            self.expect(TokenType.LPAREN, "Expected '(' after 'for'")
            condition = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')' after condition")
            self.expect(TokenType.LBRACE, "Expected '{' before loop body")
            body = self.parse_block()
            end_token = self.expect(TokenType.RBRACE, "Expected '}' after loop body")
            stmt_span = Span(for_token.line, for_token.column, end_token.line, end_token.column)
            return ForStmt(condition, body, span=stmt_span)

        # Check for break statement
        if self.check(TokenType.BREAK):
            break_token = self.advance()
            stmt_span = Span(break_token.line, break_token.column, break_token.line, break_token.column + 4)
            return BreakStmt(span=stmt_span)

        # Check for continue statement
        if self.check(TokenType.CONTINUE):
            continue_token = self.advance()
            stmt_span = Span(continue_token.line, continue_token.column, continue_token.line, continue_token.column + 7)
            return ContinueStmt(span=stmt_span)

        # Check for variable declaration: IDENT ":" type "=" expr
        if self.check(TokenType.IDENT) and self.peek(1).type == TokenType.COLON:
            name_token = self.advance()
            self.expect(TokenType.COLON, "Expected ':' after variable name")
            type_token = self.expect(TokenType.IDENT, "Expected type")
            self.expect(TokenType.ASSIGN, "Expected '=' in variable declaration")
            value = self.parse_expression()
            stmt_span = self._make_span_from_expr(name_token, value)
            return VarDecl(name_token.value, type_token.value, value, span=stmt_span)

        # Check for assignment: IDENT "=" expr
        if self.check(TokenType.IDENT) and self.peek(1).type == TokenType.ASSIGN:
            name_token = self.advance()
            self.expect(TokenType.ASSIGN, "Expected '='")
            value = self.parse_expression()
            stmt_span = self._make_span_from_expr(name_token, value)
            return Assignment(name_token.value, value, span=stmt_span)

        # Check for compound assignment: IDENT "+=" expr or IDENT "-=" expr
        # Desugar: x += e  →  x = x + e
        if self.check(TokenType.IDENT) and self.peek(1).type == TokenType.PLUS_EQUAL:
            name_token = self.advance()
            self.advance()  # consume +=
            value = self.parse_expression()
            ident_span = Span(name_token.line, name_token.column, name_token.line, name_token.column + len(name_token.value) - 1)
            binary_span = self._make_span_from_expr(name_token, value)
            stmt_span = self._make_span_from_expr(name_token, value)
            return Assignment(name_token.value, BinaryExpr("+", Identifier(name_token.value, span=ident_span), value, span=binary_span), span=stmt_span)

        if self.check(TokenType.IDENT) and self.peek(1).type == TokenType.MINUS_EQUAL:
            name_token = self.advance()
            self.advance()  # consume -=
            value = self.parse_expression()
            ident_span = Span(name_token.line, name_token.column, name_token.line, name_token.column + len(name_token.value) - 1)
            binary_span = self._make_span_from_expr(name_token, value)
            stmt_span = self._make_span_from_expr(name_token, value)
            return Assignment(name_token.value, BinaryExpr("-", Identifier(name_token.value, span=ident_span), value, span=binary_span), span=stmt_span)

        expr = self.parse_expression()
        stmt_span = expr.span if expr.span else Span(start_token.line, start_token.column, start_token.line, start_token.column)
        return ExprStmt(expr, span=stmt_span)

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
        param_span = Span(
            name_token.line,
            name_token.column,
            type_token.line,
            type_token.column + len(type_token.value) - 1,
        )
        return Param(name_token.value, type_token.value, span=param_span)

    def parse_function(self):
        fn_token = self.expect(TokenType.FN, "Expected 'fn'")
        name_token = self.expect(TokenType.IDENT, "Expected function name")
        name = name_token.value

        # Create span for just the function name identifier
        name_span = Span(
            name_token.line,
            name_token.column,
            name_token.line,
            name_token.column + len(name) - 1,
        )

        self.expect(TokenType.LPAREN, "Expected '(' after function name")
        params = self.parse_params()
        self.expect(TokenType.RPAREN, "Expected ')' after parameters")

        return_type = None
        if self.match(TokenType.COLON):
            type_token = self.expect(TokenType.IDENT, "Expected return type")
            return_type = type_token.value

        self.expect(TokenType.LBRACE, "Expected '{' before function body")
        body = self.parse_block()
        rbrace_token = self.expect(TokenType.RBRACE, "Expected '}' after function body")

        # Create span for entire function definition
        func_span = Span(
            fn_token.line,
            fn_token.column,
            rbrace_token.line,
            rbrace_token.column,
        )

        return Function(name, params, return_type, body, span=func_span, name_span=name_span)

    def parse_block(self):
        statements = []

        while not self.check(TokenType.RBRACE) and not self.at_end():
            statements.append(self.parse_statement())

        return statements

    def parse_program(self):
        start_token = self.current()
        functions = []

        while not self.at_end():
            functions.append(self.parse_function())

        # Program span: from start to last function's end (or start if empty)
        if functions:
            last_func = functions[-1]
            program_span = Span(
                start_token.line if start_token.line else 1,
                start_token.column if start_token.column else 1,
                last_func.span.end_line,
                last_func.span.end_column,
            )
        else:
            # Empty program
            program_span = Span(1, 1, 1, 1)

        return Program(functions, span=program_span)


def _validate_spans(node):
    """Walk AST, assert any field ending in 'span' is not None."""
    if not hasattr(node, '__dataclass_fields__'):
        return

    for field in fields(node):
        value = getattr(node, field.name)

        if field.name.endswith('span') and value is None:
            raise AssertionError(f"{type(node).__name__} missing {field.name}")

        if isinstance(value, list):
            for item in value:
                _validate_spans(item)
        elif hasattr(value, '__dataclass_fields__'):
            _validate_spans(value)


def parse(tokens):
    program = Parser(tokens).parse_program()
    _validate_spans(program)
    return program
