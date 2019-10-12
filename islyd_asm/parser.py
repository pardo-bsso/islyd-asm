#!/usr/bin/env python3

import re

import attr
from .instructions import ALL_INSTRUCTIONS, is_instruction, UnknownInstruction


@attr.s
class Parser:
    """ Simple instruction parser that keeps track of current memory address """
    base_address = attr.ib(default=0)
    current_address = attr.ib()

    @current_address.default
    def _get_initial_current_address(self):
        return self.base_address

    def parse_line(self, line):
        line = line.strip()

        if not line:
            return None

        if line.startswith(';'):   # Comments
            return None

        # remove comments and extra whitespace
        line = re.split(r';[\w\s]*$', line)[0]
        line = line.strip()

        for instruction in ALL_INSTRUCTIONS:
            if is_instruction(line, instruction):
                parsed_instruction = instruction.from_data(line, self.current_address)
                self.current_address += parsed_instruction.size
                return parsed_instruction
        return UnknownInstruction.from_data(line, address=self.current_address)


if __name__ == '__main__':
    import fileinput

    parser = Parser()
    for line in fileinput.input():
        print(parser.parse_line(line))
