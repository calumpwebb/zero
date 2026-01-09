from zero.ast import (
    VarDecl,
    Assignment,
    ReturnStmt,
    ExprStmt,
    IfStmt,
    ForStmt,
    BreakStmt,
    ContinueStmt,
    IntLiteral,
    BoolLiteral,
    StringLiteral,
    Identifier,
    BinaryExpr,
    UnaryExpr,
    Call,
)
from zero.builtins import BUILTIN_NAMES, BUILTIN_TYPES


class SemanticError(Exception):
    pass


def analyze(program):
    # Check for duplicate function names and builtin shadowing
    seen = set()
    for func in program.functions:
        if func.name in seen:
            raise SemanticError(f"duplicate function: {func.name}")
        if func.name in BUILTIN_NAMES:
            raise SemanticError(f"shadows builtin: {func.name}")
        seen.add(func.name)

    # Check main exists
    main_func = None
    for func in program.functions:
        if func.name == "main":
            main_func = func
            break

    if main_func is None:
        raise SemanticError("missing main function")

    # Check main signature
    if main_func.params:
        raise SemanticError("main must not accept parameters")

    if main_func.return_type is not None:
        raise SemanticError("main must not have a return type")

    # Build function return type table
    func_types = dict(BUILTIN_TYPES)
    for func in program.functions:
        func_types[func.name] = func.return_type or "int"

    # Analyze each function body
    for func in program.functions:
        analyze_function(func, func_types)


def analyze_function(func, func_types):
    """Analyze a function body for variable usage."""
    # Track variable types: name -> type
    variables = {}

    # Parameters are variables
    for param in func.params:
        variables[param.name] = param.type

    # Analyze each statement (loop_depth=0 means not inside a loop)
    for stmt in func.body:
        analyze_statement(stmt, variables, func_types, loop_depth=0)


def analyze_statement(stmt, variables, func_types, loop_depth=0):
    """Analyze a statement for variable usage."""
    match stmt:
        case VarDecl(name, type_, value):
            # Check the value expression first
            check_expr(value, variables)
            # Check the value type matches the declared type
            value_type = type_of(value, variables, func_types)
            if value_type != type_:
                raise SemanticError(f"type mismatch: expected {type_}, got {value_type}")
            # Record the variable type
            variables[name] = type_

        case Assignment(name, value):
            # Check variable is defined
            if name not in variables:
                raise SemanticError(f"undefined variable: {name}")
            # Check the value expression
            value_type = type_of(value, variables, func_types)
            expected_type = variables[name]
            if value_type != expected_type:
                raise SemanticError(
                    f"type mismatch: cannot assign {value_type} to {expected_type}"
                )

        case ReturnStmt(expr):
            check_expr(expr, variables)

        case ExprStmt(expr):
            check_expr(expr, variables)

        case IfStmt(condition, then_body, else_body):
            check_expr(condition, variables)
            # Condition must be bool
            cond_type = type_of(condition, variables, func_types)
            if cond_type != "bool":
                raise SemanticError(f"if condition must be bool, got {cond_type}")
            for s in then_body:
                analyze_statement(s, variables, func_types, loop_depth)
            if else_body:
                for s in else_body:
                    analyze_statement(s, variables, func_types, loop_depth)

        case ForStmt(condition, body):
            check_expr(condition, variables)
            # Condition must be bool
            cond_type = type_of(condition, variables, func_types)
            if cond_type != "bool":
                raise SemanticError(f"for condition must be bool, got {cond_type}")
            # Create new scope for loop body (copy variables dict)
            loop_vars = dict(variables)
            for s in body:
                analyze_statement(s, loop_vars, func_types, loop_depth + 1)

        case BreakStmt():
            if loop_depth == 0:
                raise SemanticError("break outside of loop")

        case ContinueStmt():
            if loop_depth == 0:
                raise SemanticError("continue outside of loop")


def check_expr(expr, variables):
    """Check an expression for undefined variables."""
    match expr:
        case IntLiteral(_) | BoolLiteral(_) | StringLiteral(_):
            pass
        case Identifier(name):
            if name not in variables:
                raise SemanticError(f"undefined variable: {name}")
        case BinaryExpr(_, left, right):
            check_expr(left, variables)
            check_expr(right, variables)
        case UnaryExpr(op, operand):
            check_expr(operand, variables)
            # Type check: can only negate int
            if op == "-":
                operand_type = type_of(operand, variables, BUILTIN_TYPES)
                if operand_type != "int":
                    raise SemanticError(f"cannot negate {operand_type}")
        case Call(_, args):
            for arg in args:
                check_expr(arg, variables)


def type_of(expr, variables, func_types):
    """Get the type of an expression."""
    match expr:
        case IntLiteral(_):
            return "int"
        case BoolLiteral(_):
            return "bool"
        case StringLiteral(_):
            return "str"
        case Identifier(name):
            if name not in variables:
                raise SemanticError(f"undefined variable: {name}")
            return variables[name]
        case BinaryExpr(op, left, _):
            # For comparisons, return bool
            if op in ("==", "!=", "<", ">", "<=", ">="):
                return "bool"
            # For arithmetic, return the type of operands (simplified)
            return type_of(left, variables, func_types)
        case UnaryExpr(op, operand):
            operand_type = type_of(operand, variables, func_types)
            if op == "-":
                if operand_type != "int":
                    raise SemanticError(f"cannot negate {operand_type}")
                return "int"
            return operand_type
        case Call(name, _):
            # Look up the function's return type
            return func_types.get(name, "int")
    return "int"  # default
