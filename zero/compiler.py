from zero.ast import (
    Program,
    Function,
    Stmt,
    ReturnStmt,
    ExprStmt,
    Expr,
    IntLiteral,
    BoolLiteral,
    StringLiteral,
    Identifier,
    BinaryExpr,
    Call,
)
from zero.bytecode import Op, Chunk, CompiledProgram, BUILTINS


class Compiler:
    def __init__(self, function_index, function_return_types=None):
        self.function_index = function_index
        self.function_return_types = function_return_types or {}
        self.code = []
        self.constants = []
        self.locals = {}  # name -> (slot, type)

    def emit(self, op, *operands):
        self.code.append(op)
        for operand in operands:
            self.code.append(operand)

    def add_constant(self, value):
        self.constants.append(value)
        return len(self.constants) - 1

    def compile_expr(self, expr) -> str:
        """Compile expression and return its type."""
        match expr:
            case IntLiteral(value):
                idx = self.add_constant(value)
                self.emit(Op.CONST, idx)
                return "int"

            case BoolLiteral(value):
                idx = self.add_constant(value)
                self.emit(Op.CONST, idx)
                return "bool"

            case StringLiteral(value):
                idx = self.add_constant(value)
                self.emit(Op.CONST, idx)
                return "str"

            case Identifier(name):
                slot, var_type = self.locals[name]
                self.emit(Op.LOAD, slot)
                return var_type

            case BinaryExpr(op, left, right):
                left_type = self.compile_expr(left)
                right_type = self.compile_expr(right)
                if op == "+":
                    if left_type == "int" and right_type == "int":
                        self.emit(Op.ADD_INT)
                        return "int"
                    elif left_type == "str" and right_type == "str":
                        self.emit(Op.ADD_STR)
                        return "str"
                    else:
                        raise TypeError(f"Cannot add {left_type} and {right_type}")
                elif op == "-":
                    if left_type == "int" and right_type == "int":
                        self.emit(Op.SUB_INT)
                        return "int"
                    else:
                        raise TypeError(f"Cannot subtract {left_type} and {right_type}")

            case Call(name, args):
                for arg in args:
                    self.compile_expr(arg)
                if name in BUILTINS:
                    self.emit(Op.CALL_BUILTIN, BUILTINS[name], len(args))
                    return "int"  # print returns int (0)
                else:
                    func_idx = self.function_index[name]
                    self.emit(Op.CALL, func_idx, len(args))
                    return self.function_return_types.get(name, "int")

    def compile_stmt(self, stmt):
        match stmt:
            case ReturnStmt(expr):
                self.compile_expr(expr)
                self.emit(Op.RET)

            case ExprStmt(expr):
                self.compile_expr(expr)
                self.emit(Op.POP)

    def compile_function(self, func):
        for i, param in enumerate(func.params):
            self.locals[param.name] = (i, param.type)

        for stmt in func.body:
            self.compile_stmt(stmt)

        return Chunk(
            code=self.code,
            constants=self.constants,
            arity=len(func.params),
        )


def compile_program(program):
    function_index = {}
    function_return_types = {}
    for i, func in enumerate(program.functions):
        function_index[func.name] = i
        function_return_types[func.name] = func.return_type or "int"

    chunks = []
    for func in program.functions:
        compiler = Compiler(function_index, function_return_types)
        chunk = compiler.compile_function(func)
        chunks.append(chunk)

    return CompiledProgram(chunks=chunks, function_index=function_index)
