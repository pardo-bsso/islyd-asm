#!/usr/bin/env python3

from collections import OrderedDict

import attr

from .instructions import UnknownInstruction
from .parser import Parser
from .symbol_table import SymbolTable, UndefinedSymbol, SymbolRedefinedError
from .ihex import IHEX_EOF, line_info_to_ihex


class SyntaxError(Exception):
    pass


@attr.s
class LineInfo:
    line_number = attr.ib(default=0)
    line = attr.ib(default='')
    instruction = attr.ib(default=None)
    opcode = attr.ib(factory=list)


class Assembler:
    def __init__(self):
        self.parser = Parser()
        self.symbol_table = SymbolTable()
        # [LineInfo]
        self.parsed_lines = []
        self.line_count = 1

    def parse(self, source):
        """
Tries to parse source as a valid assembler source.
source is an iterable of lines.
        """

        for line in source:
            instruction = self.parser.parse_line(line)
            if instruction is not None:     # Comment or blank line
                line_info = LineInfo(line=line, line_number=self.line_count, instruction=instruction)
                self.parsed_lines.append(line_info)

                for symbol in instruction.provided_symbols:
                    self.symbol_table.add(symbol)

                for identifier in instruction.required_symbols:
                    self.symbol_table.add_dependency(identifier)

                if isinstance(instruction, UnknownInstruction):
                    msg = """Unknown instruction in line {line_number}:\n{line}""".format(**attr.asdict(line_info))
                    raise SyntaxError(msg)

            self.line_count += 1

        if self.symbol_table.dependencies:
            msg = """Undefined symbols:\n{}""".format('\n'.join(self.symbol_table.dependencies))
            raise UndefinedSymbol(msg)

        return self

    def compile(self):
        """ Updates each parsed line with the corresponding opcode after resolving symbol dependencies """
        for line_info in self.parsed_lines:
            try:
                line_info.opcode = line_info.instruction.emit_opcode(self.symbol_table)
            except Exception as e:
                msg = """{exception}\nIn line {line_number}:\n{line}""".format(exception=e, **attr.asdict(line_info))
                raise SyntaxError(msg) from None

        return self

    def to_ihex(self):
        records = []
        for line in self.parsed_lines:
            hexrecord = line_info_to_ihex(line)
            if hexrecord is not None:
                records.append(hexrecord)
        records.append(IHEX_EOF)

        return '\n'.join(records)


if __name__ == '__main__':
    import fileinput

    assembler = Assembler()
    assembler.parse(fileinput.input()).compile()

    for line in assembler.parsed_lines:
        print(line)

    print(assembler.to_ihex())
