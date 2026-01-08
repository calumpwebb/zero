class SemanticError(Exception):
    pass


def analyze(program):
    # Check for duplicate function names first
    seen = set()
    for func in program.functions:
        if func.name in seen:
            raise SemanticError(f"duplicate function: {func.name}")
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
