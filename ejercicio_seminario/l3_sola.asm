; L3_OUT = SW0 | (SW1 & SW2)

SW0     equ 0   ; PB0
SW1     equ 1   ; PB1
SW2     equ 2   ; PB2

L3_OUT  equ 3   ; PA3


begin:

    ldi rxh portb
    btjs SW0, turn_l3_on, portb

    btjc SW1, turn_l3_off, portb
    btjc SW2, turn_l3_off, portb
    jmp pc, turn_l3_on

turn_l3_off:
    bit clr L3_OUT, porta
    jmp pc, loop_end

turn_l3_on:
    bit set L3_OUT, porta

loop_end:
    jmp pc, begin
