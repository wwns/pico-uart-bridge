"""
Raspberry Pi Pico - Simple UART bridge (no menu)
=================================================
Pico GP0 (TX, pin 1)  -> (RX) device
Pico GP1 (RX, pin 2)  <- (TX) device
Pico GND  (pin 3)     -> GND
Change BAUDRATE as needed.
"""
import sys, uselect, micropython
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
        sys.stdout.buffer.write(uart.read(n))
        led.toggle()
