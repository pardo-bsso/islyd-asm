#!/usr/bin/env python3

from collections import OrderedDict

import attr

from .instructions import UnknownInstruction
from .parser import Parser
from .symbol_table import SymbolTable, UndefinedSymbol, SymbolRedefinedError


class SyntaxError(Exception):
    pass


@attr.s
class LineInfo:
    line_number = attr.ib(default=0)
    line = attr.ib(default='')
    instruction = attr.ib(default=None)


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


if __name__ == '__main__':
    import fileinput

    assembler = Assembler()
    assembler.parse(fileinput.input())
