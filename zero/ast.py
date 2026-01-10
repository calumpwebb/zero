from dataclasses import dataclass, field


@dataclass(frozen=True)
class Span:
    """Source location span for LSP features."""
    start_line: int
    start_column: int
    end_line: int
    end_column: int


@dataclass(frozen=True)
class Node:
    """Base class for all AST nodes with optional span tracking."""
    span: Span | None = field(default=None, kw_only=True, compare=False)


@dataclass(frozen=True)
class IntLiteral(Node):
    value: int


@dataclass(frozen=True)
class BoolLiteral(Node):
    value: bool


@dataclass(frozen=True)
class StringLiteral(Node):
    value: str


@dataclass(frozen=True)
class Identifier(Node):
    name: str


@dataclass(frozen=True)
class BinaryExpr(Node):
    op: str
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class UnaryExpr(Node):
    op: str
    operand: "Expr"


@dataclass(frozen=True)
class Call(Node):
    name: str
    args: list

    def __eq__(self, other):
        if not isinstance(other, Call):
            return NotImplemented
        return self.name == other.name and list(self.args) == list(other.args)


Expr = IntLiteral | BoolLiteral | StringLiteral | Identifier | BinaryExpr | UnaryExpr | Call


@dataclass(frozen=True)
class ReturnStmt(Node):
    expr: Expr


@dataclass(frozen=True)
class ExprStmt(Node):
    expr: Expr


@dataclass(frozen=True)
class VarDecl(Node):
    name: str
    type: str
    value: "Expr"


@dataclass(frozen=True)
class Assignment(Node):
    name: str
    value: "Expr"


@dataclass(frozen=True)
class IfStmt(Node):
    condition: "Expr"
    then_body: list
    else_body: list | None

    def __eq__(self, other):
        if not isinstance(other, IfStmt):
            return NotImplemented
        return (
            self.condition == other.condition
            and list(self.then_body) == list(other.then_body)
            and (
                (self.else_body is None and other.else_body is None)
                or (
                    self.else_body is not None
                    and other.else_body is not None
                    and list(self.else_body) == list(other.else_body)
                )
            )
        )


@dataclass(frozen=True)
class ForStmt(Node):
    condition: "Expr"
    body: list

    def __eq__(self, other):
        if not isinstance(other, ForStmt):
            return NotImplemented
        return self.condition == other.condition and list(self.body) == list(other.body)


@dataclass(frozen=True)
class BreakStmt(Node):
    pass


@dataclass(frozen=True)
class ContinueStmt(Node):
    pass


Stmt = ReturnStmt | ExprStmt | VarDecl | Assignment | IfStmt | ForStmt | BreakStmt | ContinueStmt


@dataclass(frozen=True)
class Param(Node):
    name: str
    type: str


@dataclass(frozen=True)
class Function(Node):
    name: str
    params: list
    return_type: str
    body: list
    name_span: Span | None = field(default=None, kw_only=True)  # span of just the identifier

    def __eq__(self, other):
        if not isinstance(other, Function):
            return NotImplemented
        return (
            self.name == other.name
            and list(self.params) == list(other.params)
            and self.return_type == other.return_type
            and list(self.body) == list(other.body)
        )


@dataclass(frozen=True)
class Program(Node):
    functions: list

    def __eq__(self, other):
        if not isinstance(other, Program):
            return NotImplemented
        return list(self.functions) == list(other.functions)
