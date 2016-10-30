import opcodes
import dasm_objects
from util import dw_to_uint, tc_to_int


def disassemble_instruction(mem, address):
    try:
        opcode = mem[address]
    except IndexError:
        import pdb; pdb.set_trace()
    instruction = opcodes.opcode_table[opcode](mem, address)
    return instruction

def disassemble_program(program):
    find_and_label_entry_points(program)
    program.print_entry_points()

    for ep in program.entry_points:
        disassemble_chunk(program, ep)

def disassemble_chunk(program, start_address):
    chunk = dasm_objects.Chunk(start_address)

    address = start_address
    while True:
        instruction = disassemble_instruction(program.mem, address)
        if instruction.category == opcodes.category.Illegal:
            chunk.print_instructions()
            import pdb; pdb.set_trace()
            raise Exception("Tried to disassemble illegal instruction {}".format(instruction))
        chunk.add_instruction(instruction)
        address += instruction.size

        if instruction.is_conditional_jump or instruction.is_function_call:
            chunk.add_exit_point(instruction.address, get_jump_target(instruction))
        if instruction.is_unconditional_jump or instruction.is_function_return:
            chunk.add_exit_point(instruction.address, get_jump_target(instruction))
            break

def find_and_label_entry_points(program):
    vectors = (
        ("NMI", 0xFFFA),
        ("RESET", 0xFFFC),
        ("IRQ", 0xFFFE))
    for label, v in vectors:
        address = read_dword(program.mem, v)
        program.entry_points.add(address)
        program.labels[address] = label

def read_dword(mem, address):
    """ Read a 2-byte dword, little-endian, at the given address. """
    lsb = mem[address]
    msb = mem[address+1]
    return dw_to_uint((lsb, msb))

def get_jump_target(instruction):
    if instruction.is_conditional_jump:
        # All conditional jumps are relative.
        assert len(instruction.operands) == 1
        operand = instruction.operands[0]
        return instruction.address + tc_to_int(operand)

    if instruction.is_unconditional_jump or instruction.is_function_call:
        if instruction.category == opcodes.category.JmpAbsolute:
            return dw_to_uint(instruction.operands)
        if instruction.category == opcodes.category.JmpAbsoluteIndirect:
            return dasm_objects.UNKNOWN_JUMP_TARGET

    if instruction.is_function_return:
        return dasm_objects.UNKNOWN_JUMP_TARGET

    raise Exception("Instruction {} is not a jump".format(instruction))
