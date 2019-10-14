# islyd-asm

Simple assembler for the VHDL processor described in https://catedra.ing.unlp.edu.ar/electrotecnia/islyd/seminario_micro.html


# Installation

On most cases running

```
$ pip install --user .
```

from the top level source directory should do.


# Usage

```
$ islyd-asm --help
usage: islyd-asm [-h] [-o OUTPUT] asmfile

positional arguments:
  asmfile               Assembler source file

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Compiled IHEX file name (defaults to asmfile with hex suffix if not provided)
```


# Syntax

  - Labels and definitions *are* case sensitive
  - Instructions are case insensitive
  - Comments start with a semicolon, can be either alone or after a label/definition/instruction
  - Numeric literals and addresses are all in hexadecimal and prefixed with a dollar sign, like:

    ```
    $abcd
    ```

  - Labels are just a string of word characters (whatever \w matches in a regular expression) that ends in a colon.

    There should be no space between the label and the terminating colon. It is not necessary to define a label on the
    first column only but it improves readability

    ```
    some_label:     ; Good
    some_label :    ; Not good.
    ```

  - Definitions take the form of:

    ```
    identifier EQU value
    ```

    All the occurences of *identifier* are replaced by the literal *value*. No further expansion is performed.


# Instruction set


  - **CLR RX** Clears register *RX*
  - **INC RX** Increments contents of register *RX* by 1
  - **DEC RX** Decrements contents of register *RX* by 1
  - **DEC RX IF NOT ZERO**
  - **STR RX,**      *address, label or definition*
  - **LDD RX,**      *address, label or definition*
  - **LDI RX,**      *address, label or definition*
  - **LDI IX,**      *address, label or definition*
  - **LDI RXH PORTB**
  - **INC IX**
  - **LDD RX, IX**
  - **STR RX, IX**

## Flow control

  - **NOP** no-op
  - **RST** Resets processor
  - **JMP PC,**      *address, label or definition*
  - **JMP PC IF Z,** *address, label or definition*
  - **JMP PC IF C,** *address, label or definition*
  - **BTJC** *bit number or definition* **,** *address, label or definition* **, PORTB**
  - **BTJS** *bit number or definition* **,** *address, label or definition* **, PORTB**

## Arithmetic

  - **NOT**
  - **SWAP RX**
  - **SLA RX**
  - **SRA RX**
  - **SLL RX**
  - **SRL RX**
  - **AND**  *address, label or definition*
  - **OR**   *address, label or definition*
  - **XOR**  *address, label or definition*
  - **NAND** *address, label or definition*
  - **NOR**  *address, label or definition*
  - **XNOR** *address, label or definition*
  - **ADD**  *address, label or definition*
  - **SUB**  *address, label or definition*
  - **ADDC** *address, label or definition*
  - **SUBC** *address, label or definition*


## Port manipulation
  - **INC PORTA**
  - **DEC PORTA**
  - **STR RXL PORTA**
  - **BIT SET** *bit number or definition* **, PORTA**
  - **BIT CLR** *bit number or definition* **, PORTA**
