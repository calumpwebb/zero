from dataclasses import dataclass


@dataclass(frozen=True)
class IntLiteral:
    value: int


@dataclass(frozen=True)
class BoolLiteral:
    value: bool


@dataclass(frozen=True)
class StringLiteral:
    value: str


@dataclass(frozen=True)
class Identifier:
    name: str


@dataclass(frozen=True)
class BinaryExpr:
    op: str
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class Call:
    name: str
    args: list

    def __eq__(self, other):
        if not isinstance(other, Call):
            return NotImplemented
        return self.name == other.name and list(self.args) == list(other.args)


Expr = IntLiteral | BoolLiteral | StringLiteral | Identifier | BinaryExpr | Call


@dataclass(frozen=True)
class ReturnStmt:
    expr: Expr


@dataclass(frozen=True)
class ExprStmt:
    expr: Expr


@dataclass(frozen=True)
class VarDecl:
    name: str
    type: str
    value: "Expr"


@dataclass(frozen=True)
class Assignment:
    name: str
    value: "Expr"


@dataclass(frozen=True)
class IfStmt:
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
class ForStmt:
    condition: "Expr"
    body: list

    def __eq__(self, other):
        if not isinstance(other, ForStmt):
            return NotImplemented
        return self.condition == other.condition and list(self.body) == list(other.body)


@dataclass(frozen=True)
class BreakStmt:
    pass


@dataclass(frozen=True)
class ContinueStmt:
    pass


Stmt = ReturnStmt | ExprStmt | VarDecl | Assignment | IfStmt | ForStmt | BreakStmt | ContinueStmt


@dataclass(frozen=True)
class Param:
    name: str
    type: str


@dataclass(frozen=True)
class Function:
    name: str
    params: list
    return_type: str
    body: list

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
class Program:
    functions: list

    def __eq__(self, other):
        if not isinstance(other, Program):
            return NotImplemented
        return list(self.functions) == list(other.functions)
