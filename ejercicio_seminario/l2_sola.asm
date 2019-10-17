; L2_OUT = SW0 & SW2

SW0     equ 0   ; PB0
SW2     equ 2   ; PB2

L2_OUT  equ 2   ; PA2


begin:

    btjc SW0, turn_l2_off, portb
    btjc SW2, turn_l2_off, portb
    jmp pc, turn_l2_on

turn_l2_off:
    bit clr L2_OUT, porta
    jmp pc, loop_end

turn_l2_on:
    bit set L2_OUT, porta

loop_end:
    jmp pc, begin
