; L1_OUT = SW0
; L2_OUT = SW0 & SW2
; L3_OUT = SW0 | (SW2 & SW3)

SW0     equ 0   ; PB0
SW1     equ 1   ; PB1
SW2     equ 2   ; PB2

L1_OUT  equ 1   ; PA1
L2_OUT  equ 2   ; PA2
L3_OUT  equ 3   ; PA3


mainloop_begin:

; L1
L1_begin:

    ldi rxh portb
    btjs SW0, turn_l1_on, portb

turn_l1_off:
    bit clr L1_OUT, porta
    jmp pc, L1_end

turn_l1_on:
    bit set L1_OUT, porta

L1_end:


; L2
L2_begin:

    ldi rxh portb
    btjc SW0, turn_l2_off, portb
    btjc SW2, turn_l2_off, portb
    jmp pc, turn_l2_on

turn_l2_off:
    bit clr L2_OUT, porta
    jmp pc, L2_end

turn_l2_on:
    bit set L2_OUT, porta

L2_end:


; L3
L3_begin:

    ldi rxh portb
    btjs SW0, turn_l3_on, portb

    btjc SW1, turn_l3_off, portb
    btjc SW2, turn_l3_off, portb
    jmp pc, turn_l3_on

turn_l3_off:
    bit clr L3_OUT, porta
    jmp pc, L3_end

turn_l3_on:
    bit set L3_OUT, porta

L3_end:


mainloop_end:
    jmp pc, mainloop_begin
