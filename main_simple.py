"""
Raspberry Pi Pico - Prosty UART bridge bez menu
================================================
Pico GP0 (TX, pin 1)  -> (RX) urzadzenia
Pico GP1 (RX, pin 2)  <- (TX) urzadzenia
Pico GND  (pin 3)     -> GND
Zmien BAUDRATE na potrzebny.
"""
import sys, utime, uselect, micropython
from machine import UART, Pin

BAUDRATE = 115200

micropython.kbd_intr(-1)
uart = UART(0, baudrate=BAUDRATE, tx=Pin(0), rx=Pin(1), timeout=0)
led  = Pin(25, Pin.OUT)
poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

led.on()

while True:
    if poll.poll(0):
        data = sys.stdin.buffer.read(64)
        if data:
            uart.write(data)
            led.toggle()
    n = uart.any()
    if n:
        r = uart.read(n)
        if r:
            sys.stdout.buffer.write(r)
            led.toggle()
