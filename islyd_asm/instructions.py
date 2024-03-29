import re
import attr

from .utils import int_to_split_hex

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
    size = attr.ib(default=1)
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


def parse_hex_literal(literal):
    """ Given an hex literal like $1234 returns [0x12, 0x34] """
    parsed = int(literal.strip().replace('$', ''), 16)
    hi, lo = int_to_split_hex(parsed)
    return [hi, lo]


@attr.s
class MultipleArgumentsInstruction(SimpleInstruction):
    """ Instruction that has more than one pattern and argument (for example, accepts both literals and identifiers) """
    size = attr.ib(default=2)
    pattern = attr.ib(factory=list)
    arguments = attr.ib(factory=dict)
    value = None

    @classmethod
    def can_be(cls, line):
        if not cls.pattern:
            raise NotImplementedError('Instruction pattern list is not defined')

        for pattern in cls.pattern:
            matches = pattern.fullmatch(line)
            if matches:
                return matches
        return None

    def parse(self, matches, line=None, address=None):
        arguments = self.arguments = matches.groupdict()
        value = arguments.get('value', None)
        identifier = arguments.get('identifier', None)
        self.value = value
        if identifier is not None:
            self.required_symbols = [identifier]

        return self

    def resolve_symbols(self, symbol_table):
        for identifier in self.required_symbols:
            self.arguments[identifier] = symbol_table.get(identifier)

    def emit_opcode(self, symbol_table=None):
        self.resolve_symbols(symbol_table)
        operand = [0, 0]
        resolved_symbol_name = self.arguments.get('identifier', None)
        resolved_symbol = self.arguments.get(resolved_symbol_name, None)

        if self.value is not None:
            operand = parse_hex_literal(self.value)
        elif resolved_symbol is not None:
            operand = parse_hex_literal(str(resolved_symbol.value))

        full_opcode = list(self.opcode)
        full_opcode.extend(operand)
        return full_opcode


@attr.s
class BitManipulationInstruction(MultipleArgumentsInstruction):
    size = attr.ib(default=1)
    def emit_opcode(self, symbol_table=None):
        self.resolve_symbols(symbol_table)
        operand = 0
        resolved_symbol_name = self.arguments.get('identifier', None)
        resolved_symbol = self.arguments.get(resolved_symbol_name, None)

        if self.value is not None:
            operand = int(self.value)
        elif resolved_symbol is not None:
            operand = int(resolved_symbol.value)

        if operand not in range(8):
            raise ValueError('Provided bit number "{}" is not valid for {}'.format(operand, self.__class__.__qualname__))

        operand = (operand * 32) & 0xE0

        full_opcode = list(self.opcode)
        full_opcode.extend([operand])
        return full_opcode


@attr.s
class BitTestInstruction(BitManipulationInstruction):
    size = attr.ib(default=2)
    def parse(self, matches, line=None, address=None):
        super().parse(matches, line, address)
        target_identifier = self.arguments.get('jump_target_identifier', None)
        if target_identifier is not None:
            self.required_symbols.append(target_identifier)

        return self

    def emit_opcode(self, symbol_table=None):
        opcode = super().emit_opcode(symbol_table)
        jump_target = [0, 0]

        target = self.arguments.get('jump_target', None)
        target_symbol_name = self.arguments.get('jump_target_identifier', None)
        target_symbol = self.arguments.get(target_symbol_name, None)

        if target is not None:
            jump_target = parse_hex_literal(str(target))
        elif target_symbol is not None:
            jump_target = parse_hex_literal(str(target_symbol.value))

        opcode.extend(jump_target)
        return opcode


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
        label = Symbol(identifier=identifier, value=hex(self.address), address=self.address)
        self.provided_symbols = [label]
        return self


@register
@attr.s
class EQU(SimpleInstruction):
    size = attr.ib(default=0)
    pattern = re.compile(r'(?P<label>\w{3,})\s+EQU\s+(?P<value>[\w$]+)$', re.I)

    def parse(self, matches, line=None, address=None):
        identifier = matches.group('label')
        value = matches.group('value')
        sym = Symbol(identifier=identifier, value=value, address=self.address)
        self.provided_symbols = [sym]
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


@register
@attr.s
class INC_IX(SimpleInstruction):
    pattern = re.compile(r'\s*INC IX\s*', re.I)
    opcode = attr.ib(default=[0x15, 0x00])


@register
@attr.s
class LDD_RX_IX(SimpleInstruction):
    pattern = re.compile(r'\s*LDD RX,\s*IX\s*', re.I)
    opcode = attr.ib(default=[0x16, 0x00])


@register
@attr.s
class STR_RX_IX(SimpleInstruction):
    pattern = re.compile(r'\s*STR RX,\s*IX\s*', re.I)
    opcode = attr.ib(default=[0x17, 0x00])


@register
@attr.s
class LDI_IX(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*LDI IX,\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*LDI IX,\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x14, 0x00])


@register
@attr.s
class LDI_RX(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*LDI RX,\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*LDI RX,\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x02, 0x00])


@register
@attr.s
class LDD_RX(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*LDD RX,\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*LDD RX,\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x05, 0x00])


@register
@attr.s
class STR_RX(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*STR RX,\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*STR RX,\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x06, 0x00])


@register
@attr.s
class JMP_PC(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*JMP PC,\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*JMP PC,\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x10, 0x00])


@register
@attr.s
class JMP_PC_IF_Z(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*JMP PC IF Z,\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*JMP PC IF Z,\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x11, 0x00])


@register
@attr.s
class JMP_PC_IF_C(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*JMP PC IF C,\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*JMP PC IF C,\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x12, 0x00])


@register
@attr.s
class AND(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*AND\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*AND\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x07, 0x18])


@register
@attr.s
class NAND(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*NAND\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*NAND\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x07, 0x19])


@register
@attr.s
class OR(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*OR\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*OR\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x07, 0x1A])


@register
@attr.s
class NOR(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*NOR\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*NOR\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x07, 0x1B])


@register
@attr.s
class XOR(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*XOR\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*XOR\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x07, 0x1C])


@register
@attr.s
class XNOR(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*XNOR\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*XNOR\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x07, 0x1D])


@register
@attr.s
class ADD(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*ADD\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*ADD\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x07, 0x08])


@register
@attr.s
class ADDC(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*ADDC\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*ADDC\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x07, 0x09])


@register
@attr.s
class SUB(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*SUB\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*SUB\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x07, 0x0A])


@register
@attr.s
class SUBC(MultipleArgumentsInstruction):
    pattern = [
        re.compile(r'\s*SUBC\s+(?P<value>\$[\dA-F]{1,4})\s*', re.I),
        re.compile(r'\s*SUBC\s+(?P<identifier>\w{3,})\s*', re.I)
    ]
    opcode = attr.ib(default=[0x07, 0x0B])


@register
@attr.s
class BIT_SET_A(BitManipulationInstruction):
    pattern = [
        re.compile(r'\s*BIT SET\s+(?P<value>[0-7])\s*,\s*PORTA', re.I),
        re.compile(r'\s*BIT SET\s+(?P<identifier>\w{3,})\s*,\s*PORTA', re.I)
    ]
    opcode = attr.ib(default=[0x09])


@register
@attr.s
class BIT_CLR_A(BitManipulationInstruction):
    pattern = [
        re.compile(r'\s*BIT CLR\s+(?P<value>[0-7])\s*,\s*PORTA', re.I),
        re.compile(r'\s*BIT CLR\s+(?P<identifier>\w{3,})\s*,\s*PORTA', re.I)
    ]
    opcode = attr.ib(default=[0x0A])


@register
@attr.s
class BIT_TEST_CLR_B(BitTestInstruction):
    pattern = [
        re.compile(r'\s*BTJC\s+(?P<value>[0-7])\s*,\s*(?P<jump_target>\$[\dA-F]{1,4})\s*,\s*PORTB', re.I),
        re.compile(r'\s*BTJC\s+(?P<value>[0-7])\s*,\s*(?P<jump_target_identifier>\w{3,})\s*,\s*PORTB', re.I),
        re.compile(r'\s*BTJC\s+(?P<identifier>\w{3,})\s*,\s*(?P<jump_target>\$[\dA-F]{1,4})\s*,\s*PORTB', re.I),
        re.compile(r'\s*BTJC\s+(?P<identifier>\w{3,})\s*,\s*(?P<jump_target_identifier>\w{3,})\s*,\s*PORTB', re.I)
    ]
    opcode = attr.ib(default=[0x0E])


@register
@attr.s
class BIT_TEST_SET_B(BitTestInstruction):
    pattern = [
        re.compile(r'\s*BTJS\s+(?P<value>[0-7])\s*,\s*(?P<jump_target>\$[\dA-F]{1,4})\s*,\s*PORTB', re.I),
        re.compile(r'\s*BTJS\s+(?P<value>[0-7])\s*,\s*(?P<jump_target_identifier>\w{3,})\s*,\s*PORTB', re.I),
        re.compile(r'\s*BTJS\s+(?P<identifier>\w{3,})\s*,\s*(?P<jump_target>\$[\dA-F]{1,4})\s*,\s*PORTB', re.I),
        re.compile(r'\s*BTJS\s+(?P<identifier>\w{3,})\s*,\s*(?P<jump_target_identifier>\w{3,})\s*,\s*PORTB', re.I)
    ]
    opcode = attr.ib(default=[0x0F])
