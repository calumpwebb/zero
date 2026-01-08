from dataclasses import dataclass
from zero.bytecode import Op, Chunk, CompiledProgram
from zero.builtins import BUILTIN_IMPLS


@dataclass
class CallFrame:
    chunk: Chunk
    ip: int
    stack_base: int


class VMError(Exception):
    pass


class VM:
    MAX_CALL_DEPTH = 1000

    def __init__(self, program):
        self.program = program
        self.stack = []
        self.frames = []

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        return self.stack.pop()

    def current_frame(self):
        return self.frames[-1]

    def run(self):
        main_idx = self.program.function_index["main"]
        main_chunk = self.program.chunks[main_idx]
        self.frames.append(CallFrame(main_chunk, 0, 0))

        while self.frames:
            frame = self.current_frame()
            chunk = frame.chunk

            if frame.ip >= len(chunk.code):
                break

            op = Op(chunk.code[frame.ip])
            frame.ip += 1

            match op:
                case Op.CONST:
                    idx = chunk.code[frame.ip]
                    frame.ip += 1
                    self.push(chunk.constants[idx])

                case Op.LOAD:
                    slot = chunk.code[frame.ip]
                    frame.ip += 1
                    value = self.stack[frame.stack_base + slot]
                    self.push(value)

                case Op.ADD_INT:
                    b = self.pop()
                    a = self.pop()
                    self.push(a + b)

                case Op.ADD_STR:
                    b = self.pop()
                    a = self.pop()
                    self.push(a + b)

                case Op.SUB_INT:
                    b = self.pop()
                    a = self.pop()
                    self.push(a - b)

                case Op.MUL_INT:
                    b = self.pop()
                    a = self.pop()
                    self.push(a * b)

                case Op.MOD_INT:
                    b = self.pop()
                    a = self.pop()
                    self.push(a % b)

                case Op.STORE:
                    slot = chunk.code[frame.ip]
                    frame.ip += 1
                    value = self.pop()
                    # Extend stack if needed for new local variables
                    target_idx = frame.stack_base + slot
                    while len(self.stack) <= target_idx:
                        self.stack.append(None)
                    self.stack[target_idx] = value

                # Integer comparisons
                case Op.CMP_EQ_INT:
                    b = self.pop()
                    a = self.pop()
                    self.push(a == b)

                case Op.CMP_NE_INT:
                    b = self.pop()
                    a = self.pop()
                    self.push(a != b)

                case Op.CMP_LT_INT:
                    b = self.pop()
                    a = self.pop()
                    self.push(a < b)

                case Op.CMP_GT_INT:
                    b = self.pop()
                    a = self.pop()
                    self.push(a > b)

                case Op.CMP_LE_INT:
                    b = self.pop()
                    a = self.pop()
                    self.push(a <= b)

                case Op.CMP_GE_INT:
                    b = self.pop()
                    a = self.pop()
                    self.push(a >= b)

                # Bool comparisons
                case Op.CMP_EQ_BOOL:
                    b = self.pop()
                    a = self.pop()
                    self.push(a == b)

                case Op.CMP_NE_BOOL:
                    b = self.pop()
                    a = self.pop()
                    self.push(a != b)

                # String comparisons
                case Op.CMP_EQ_STR:
                    b = self.pop()
                    a = self.pop()
                    self.push(a == b)

                case Op.CMP_NE_STR:
                    b = self.pop()
                    a = self.pop()
                    self.push(a != b)

                case Op.JUMP:
                    addr = chunk.code[frame.ip]
                    frame.ip = addr

                case Op.JUMP_IF_FALSE:
                    addr = chunk.code[frame.ip]
                    frame.ip += 1
                    condition = self.pop()
                    if not condition:
                        frame.ip = addr

                case Op.POP:
                    self.pop()

                case Op.CALL:
                    func_idx = chunk.code[frame.ip]
                    frame.ip += 1
                    argc = chunk.code[frame.ip]
                    frame.ip += 1

                    if len(self.frames) >= self.MAX_CALL_DEPTH:
                        raise VMError(f"maximum recursion depth exceeded ({self.MAX_CALL_DEPTH})")

                    func_chunk = self.program.chunks[func_idx]
                    new_base = len(self.stack) - argc
                    self.frames.append(CallFrame(func_chunk, 0, new_base))

                case Op.CALL_BUILTIN:
                    builtin_idx = chunk.code[frame.ip]
                    frame.ip += 1
                    argc = chunk.code[frame.ip]
                    frame.ip += 1

                    # Pop arguments and call the builtin implementation
                    args = [self.pop() for _ in range(argc)]
                    args.reverse()  # restore original order
                    result = BUILTIN_IMPLS[builtin_idx](*args)
                    self.push(result)

                case Op.RET:
                    return_value = self.pop()
                    old_frame = self.frames.pop()

                    while len(self.stack) > old_frame.stack_base:
                        self.stack.pop()

                    self.push(return_value)

                    if not self.frames:
                        return return_value

        return 0


def run(program):
    vm = VM(program)
    return vm.run()
