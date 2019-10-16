; L1_OUT = SW0

SW0     equ 0   ; PB0

L1_OUT  equ 1   ; PA1


begin:

    ldi rxh portb
    btjs SW0, turn_l1_on, portb

turn_l1_off:
    bit clr L1_OUT, porta
    jmp pc, loop_end

turn_l1_on:
    bit set L1_OUT, porta

loop_end:
    jmp pc, begin
