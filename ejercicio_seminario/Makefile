%.hex : %.asm
		islyd-asm $<

all: $(patsubst %.asm, %.hex, $(wildcard *.asm))
