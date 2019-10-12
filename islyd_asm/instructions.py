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
            instance = cls(address=address)
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


@attr.s
class UnknownInstruction(BaseInstruction):
    size = attr.ib(default=0)
    line = attr.ib(default='')

    @classmethod
    def from_data(cls, line=None, address=None):
        instance = cls(line=line, address=address)
        return instance

    # XXX FIXME: later test that this is really unknown?
    @classmethod
    def can_be(cls, line=None):
        return True


@register
@attr.s
class LABEL(SimpleInstruction):
    size = attr.ib(default=0)
    pattern = re.compile(r'(?P<label>\w+):$', re.I)

    def parse(self, matches, line=None, address=None):
        identifier = matches.group('label')
        label = Symbol(identifier=identifier, value=self.address, address=self.address)
        self.provided_symbols = [label]
        return self


@register
@attr.s
class RST(SimpleInstruction):
    pattern = re.compile(r'\s*RST\s*', re.I)
    opcode = attr.ib(default=[0x80, 0x00])


@register
@attr.s
class CLR_RX(SimpleInstruction):
    pattern = re.compile(r'\s*CLR RX\s*', re.I)
    opcode = attr.ib(default=[0x00, 0x00])


@register
@attr.s
class INC_RX(SimpleInstruction):
    pattern = re.compile(r'\s*INC RX\s*', re.I)
    opcode = attr.ib(default=[0x01, 0x00])


@register
@attr.s
class DEC_RX(SimpleInstruction):
    pattern = re.compile(r'\s*DEC RX\s*', re.I)
    opcode = attr.ib(default=[0x03, 0x00])


@register
@attr.s
class NOP(SimpleInstruction):
    pattern = re.compile(r'\s*NOP\s*', re.I)
    opcode = attr.ib(default=[0x04, 0x00])


@register
@attr.s
class NOT(SimpleInstruction):
    pattern = re.compile(r'\s*NOT\s*', re.I)
    opcode = attr.ib(default=[0x07, 0x11])


@register
@attr.s
class SWAP(SimpleInstruction):
    pattern = re.compile(r'\s*SWAP RX\s*', re.I)
    opcode = attr.ib(default=[0x07, 0x12])


@register
@attr.s
class SLA(SimpleInstruction):
    pattern = re.compile(r'\s*SLA RX\s*', re.I)
    opcode = attr.ib(default=[0x07, 0x13])


@register
@attr.s
class SRA(SimpleInstruction):
    pattern = re.compile(r'\s*SRA RX\s*', re.I)
    opcode = attr.ib(default=[0x07, 0x14])


@register
@attr.s
class SLL(SimpleInstruction):
    pattern = re.compile(r'\s*SLL RX\s*', re.I)
    opcode = attr.ib(default=[0x07, 0x15])


@register
@attr.s
class SLR(SimpleInstruction):
    pattern = re.compile(r'\s*SLR RX\s*', re.I)
    opcode = attr.ib(default=[0x07, 0x16])


@register
@attr.s
class DEC_RX_IF_NOT_ZERO(SimpleInstruction):
    pattern = re.compile(r'\s*DEC RX IF NOT ZERO\s*', re.I)
    opcode = attr.ib(default=[0x13, 0x00])


@register
@attr.s
class STR_RXL_PORTA(SimpleInstruction):
    pattern = re.compile(r'\s*STR RXL PORTA\s*', re.I)
    opcode = attr.ib(default=[0x08, 0x00])


@register
@attr.s
class INC_PORTA(SimpleInstruction):
    pattern = re.compile(r'\s*INC PORTA\s*', re.I)
    opcode = attr.ib(default=[0x0B, 0x00])


@register
@attr.s
class DEC_PORTA(SimpleInstruction):
    pattern = re.compile(r'\s*DEC PORTA\s*', re.I)
    opcode = attr.ib(default=[0x0C, 0x00])


@register
@attr.s
class LDI_RXH_PORTB(SimpleInstruction):
    pattern = re.compile(r'\s*LDI RXH PORTB\s*', re.I)
    opcode = attr.ib(default=[0x0D, 0x00])
