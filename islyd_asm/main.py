import sys
import argparse
from pathlib import PurePath

from .assembler import Assembler


def run():
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output',
                        required=False,
                        type=str,
                        default='',
                        help='Compiled IHEX file name (defaults to asmfile with hex suffix if not provided)')

    parser.add_argument('asmfile',
                        type=str,
                        help='Assembler source file')

    args = parser.parse_args()

    assembler = Assembler()

    with open(args.asmfile) as f:
        assembler.parse(f).compile()

    output = args.output
    if not output:
        output = str(PurePath(args.asmfile).with_suffix('.hex'))

    with open(output, 'w') as f:
        f.write(assembler.to_ihex())
