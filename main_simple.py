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

# LED blink natychmiast po starcie
led = Pin(25, Pin.OUT)
for _ in range(3):
    led.on();  utime.sleep_ms(80)
    led.off(); utime.sleep_ms(80)
led.on()

micropython.kbd_intr(-1)
uart = UART(0, baudrate=BAUDRATE, tx=Pin(0), rx=Pin(1), timeout=0)
poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

_last_beat = utime.ticks_ms()

while True:
    active = False
    if poll.poll(0):
        data = sys.stdin.buffer.read(64)
        if data:
            uart.write(data)
            active = True
    n = uart.any()
    if n:
        r = uart.read(n)
        if r:
            sys.stdout.buffer.write(r)
            active = True
    if active:
        led.toggle()
        _last_beat = utime.ticks_ms()
    elif utime.ticks_diff(utime.ticks_ms(), _last_beat) >= 500:
        led.toggle()
        _last_beat = utime.ticks_ms()
