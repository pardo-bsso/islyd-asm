import re
import attr

ALL_INSTRUCTIONS = []


def register(instruction):
    ALL_INSTRUCTIONS.append(instruction)
    return instruction


def is_instruction(line, instruction):
    return instruction.can_be(line) not in (None, False)


@attr.s
class Symbol:
    address = attr.ib(default=None)
    identifier = attr.ib(default=None)
    value = attr.ib(default=None)


@attr.s
class BaseInstruction:
    size = attr.ib(default=2)
    address = attr.ib(default=None)
    provided_symbols = attr.ib(factory=list)    # list of Symbol() instances that this instruction provides (say, a label or EQU)
    required_symbols = attr.ib(factory=list)    # list of symbol names that this instruction requires

    @classmethod
    def from_data(cls, line=None, address=None):
        """ Tries to parse the given line as this instruction.
        If successful returns a new instance of this instruction properly
        initialized"""
        raise NotImplementedError

    @classmethod
    def can_be(cls, line):
        """ Returns True if line can be parsed as this instruction"""
        raise NotImplementedError

    def emit_opcode(self, symbol_table=None):
        """ Emits the opcode for this instruction, optionally using the provided symbol table """
        raise NotImplementedError


@attr.s
class SimpleInstruction(BaseInstruction):
    """ Instruction that does not require nor provide any Symbol """
    pattern = attr.ib(default=None)
    opcode = attr.ib(factory=list)    # list of bytes that represent this instruction

    @classmethod
    def from_data(cls, line, address=None):
        matches = cls.can_be(line)
        if not matches:
            raise ValueError('Provided line of data "{}" is not valid for {}'.format(line, cls.__qualname__))
        else:
            instance = cls()
            return instance.parse(matches, line, address)

    def parse(self, matches, line=None, address=None):
        return self

    @classmethod
    def can_be(cls, line):
        if cls.pattern is None:
            raise NotImplementedError('Instruction pattern is not defined')

        try:
            return cls.pattern.fullmatch(line)
        except AttributeError:
            return (line == cls.pattern)

    def emit_opcode(self, symbol_table=None):
        return self.opcode
