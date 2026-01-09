from zero.ast import (
    Program,
    Function,
    Stmt,
    ReturnStmt,
    ExprStmt,
    VarDecl,
    Assignment,
    IfStmt,
    ForStmt,
    BreakStmt,
    ContinueStmt,
    Expr,
    IntLiteral,
    BoolLiteral,
    StringLiteral,
    Identifier,
    BinaryExpr,
    UnaryExpr,
    Call,
)
from zero.bytecode import Op, Chunk, CompiledProgram
from zero.builtins import BUILTIN_INDICES


class Compiler:
    def __init__(self, function_index, function_return_types=None):
        self.function_index = function_index
        self.function_return_types = function_return_types or {}
        self.code = []
        self.constants = []
        self.locals = {}  # name -> (slot, type)
        self.next_slot = 0  # next available slot for locals
        # Loop context stack: each entry is (loop_start_addr, break_patches)
        # break_patches is a list of addresses that need to be patched to jump to loop end
        self.loop_stack = []

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
                elif op == "*":
                    if left_type == "int" and right_type == "int":
                        self.emit(Op.MUL_INT)
                        return "int"
                    else:
                        raise TypeError(f"Cannot multiply {left_type} and {right_type}")
                elif op == "%":
                    if left_type == "int" and right_type == "int":
                        self.emit(Op.MOD_INT)
                        return "int"
                    else:
                        raise TypeError(f"Cannot modulo {left_type} and {right_type}")
                elif op == "==":
                    if left_type == "int" and right_type == "int":
                        self.emit(Op.CMP_EQ_INT)
                    elif left_type == "bool" and right_type == "bool":
                        self.emit(Op.CMP_EQ_BOOL)
                    elif left_type == "str" and right_type == "str":
                        self.emit(Op.CMP_EQ_STR)
                    else:
                        raise TypeError(f"Cannot compare {left_type} and {right_type} for equality")
                    return "bool"
                elif op == "!=":
                    if left_type == "int" and right_type == "int":
                        self.emit(Op.CMP_NE_INT)
                    elif left_type == "bool" and right_type == "bool":
                        self.emit(Op.CMP_NE_BOOL)
                    elif left_type == "str" and right_type == "str":
                        self.emit(Op.CMP_NE_STR)
                    else:
                        raise TypeError(f"Cannot compare {left_type} and {right_type} for inequality")
                    return "bool"
                elif op == "<":
                    if left_type == "int" and right_type == "int":
                        self.emit(Op.CMP_LT_INT)
                    else:
                        raise TypeError(f"Cannot compare {left_type} < {right_type}")
                    return "bool"
                elif op == ">":
                    if left_type == "int" and right_type == "int":
                        self.emit(Op.CMP_GT_INT)
                    else:
                        raise TypeError(f"Cannot compare {left_type} > {right_type}")
                    return "bool"
                elif op == "<=":
                    if left_type == "int" and right_type == "int":
                        self.emit(Op.CMP_LE_INT)
                    else:
                        raise TypeError(f"Cannot compare {left_type} <= {right_type}")
                    return "bool"
                elif op == ">=":
                    if left_type == "int" and right_type == "int":
                        self.emit(Op.CMP_GE_INT)
                    else:
                        raise TypeError(f"Cannot compare {left_type} >= {right_type}")
                    return "bool"

            case UnaryExpr(op, operand):
                if op == "-":
                    # Compile -x as 0 - x
                    zero_idx = self.add_constant(0)
                    self.emit(Op.CONST, zero_idx)
                    operand_type = self.compile_expr(operand)
                    if operand_type != "int":
                        raise TypeError(f"Cannot negate {operand_type}")
                    self.emit(Op.SUB_INT)
                    return "int"

            case Call(name, args):
                for arg in args:
                    self.compile_expr(arg)
                if name in BUILTIN_INDICES:
                    self.emit(Op.CALL_BUILTIN, BUILTIN_INDICES[name], len(args))
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

            case VarDecl(name, type_, value):
                # Compile the value expression
                self.compile_expr(value)
                # Allocate a new slot for the variable
                slot = self.next_slot
                self.next_slot += 1
                self.locals[name] = (slot, type_)
                # Store the value
                self.emit(Op.STORE, slot)

            case Assignment(name, value):
                # Compile the value expression
                self.compile_expr(value)
                # Store to the existing variable's slot
                slot, _ = self.locals[name]
                self.emit(Op.STORE, slot)

            case IfStmt(condition, then_body, else_body):
                # Compile condition
                self.compile_expr(condition)

                # Emit JUMP_IF_FALSE with placeholder
                self.emit(Op.JUMP_IF_FALSE, 0)
                jump_if_false_addr = len(self.code) - 1

                # Compile then block
                for stmt in then_body:
                    self.compile_stmt(stmt)

                if else_body is not None:
                    # Emit JUMP to skip else block (with placeholder)
                    self.emit(Op.JUMP, 0)
                    jump_addr = len(self.code) - 1

                    # Patch JUMP_IF_FALSE to jump to else block
                    self.code[jump_if_false_addr] = len(self.code)

                    # Compile else block
                    for stmt in else_body:
                        self.compile_stmt(stmt)

                    # Patch JUMP to skip past else block
                    self.code[jump_addr] = len(self.code)
                else:
                    # No else - patch JUMP_IF_FALSE to after then block
                    self.code[jump_if_false_addr] = len(self.code)

            case ForStmt(condition, body):
                # Record loop start address
                loop_start = len(self.code)

                # Compile condition
                self.compile_expr(condition)

                # Emit JUMP_IF_FALSE with placeholder (will jump past loop)
                self.emit(Op.JUMP_IF_FALSE, 0)
                jump_if_false_addr = len(self.code) - 1

                # Push loop context for break/continue
                break_patches = []
                self.loop_stack.append((loop_start, break_patches))

                # Compile loop body
                for stmt in body:
                    self.compile_stmt(stmt)

                # Pop loop context
                self.loop_stack.pop()

                # Emit jump back to loop start
                self.emit(Op.JUMP, loop_start)

                # Patch JUMP_IF_FALSE to after loop
                loop_end = len(self.code)
                self.code[jump_if_false_addr] = loop_end

                # Patch all break jumps to loop end
                for addr in break_patches:
                    self.code[addr] = loop_end

            case BreakStmt():
                # Emit JUMP with placeholder (will be patched when loop ends)
                self.emit(Op.JUMP, 0)
                # Record this address for patching
                _, break_patches = self.loop_stack[-1]
                break_patches.append(len(self.code) - 1)

            case ContinueStmt():
                # Jump back to loop start (condition check)
                loop_start, _ = self.loop_stack[-1]
                self.emit(Op.JUMP, loop_start)

    def compile_function(self, func):
        # Parameters occupy the first slots
        for i, param in enumerate(func.params):
            self.locals[param.name] = (i, param.type)
        self.next_slot = len(func.params)

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
