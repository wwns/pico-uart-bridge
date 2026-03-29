"""
Raspberry Pi Pico - Transparent USB <-> UART Bridge (with menu)
===============================================================

Wiring:
  Windows (PuTTY/COM4, 115200) <--USB--> Pico <--UART--> Device

  Pico GP0 (TX, pin 1)  ---->  (RX)
  Pico GP1 (RX, pin 2)  <----  (TX)
  Pico GND  (pin 3/38)  ----   GND

Features:
  - LED on = bridge active; blink = data transfer
  - Type +++ to enter menu
"""

import machine
import sys
import utime
import uselect
import micropython

# 10s window for mpremote, then block Ctrl+C
utime.sleep_ms(10000)
micropython.kbd_intr(-1)

BAUDRATES = [
    ( 1,   1200, "Old devices, sensors"),
    ( 2,   2400, "Old devices"),
    ( 3,   4800, "GPS, old devices"),
    ( 4,   9600, "Arduino default, GPS, GSM"),
    ( 5,  19200, "Modems, PLC controllers"),
    ( 6,  38400, "Modems, Bluetooth HC-05/06"),
    ( 7,  57600, "Bluetooth, fast modules"),
    ( 8,  74880, "ESP8266 boot ROM"),
    ( 9, 115200, "ESP8266/ESP32 Arduino"),
    (10, 230400, "ESP32 fast transfer"),
]
baudrate = 115200

def make_uart(baud):
    return machine.UART(0, baudrate=baud,
                        tx=machine.Pin(0), rx=machine.Pin(1), timeout=0)

def usb_print(msg):
    sys.stdout.write(msg + "\r\n")

def show_menu():
    usb_print("")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|       PICO USB<->UART BRIDGE - SETTINGS             |")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  Current baudrate: {:<6}                           |".format(baudrate))
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  Nr | Baudrate |  Description                        |")
    usb_print("|" + "-" * 54 + "|")
    for nr, baud, desc in BAUDRATES:
        marker = " <--" if baud == baudrate else "    "
        usb_print("|  {:>2} | {:>8} | {:<35} |{}".format(nr, baud, desc, marker))
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  Type number (1-10) + Enter to change baudrate       |")
    usb_print("|  Type [go]  + Enter to return to bridge mode         |")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  To enter menu: type +++                             |")
    usb_print("+" + "-" * 54 + "+")

uart = make_uart(baudrate)
led  = machine.Pin(25, machine.Pin.OUT)

for _ in range(6):
    led.toggle()
    utime.sleep_ms(100)
led.on()

usb_print("=== BRIDGE READY | {} baud | GP0->TX GP1->RX | type +++ for menu ===".format(baudrate))

poll     = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

cmd_mode = False
seq_buf  = ""
cmd_buf  = ""

while True:
    try:
        if poll.poll(0):
            ch = sys.stdin.read(1)
            if ch:
                if cmd_mode:
                    if ch in ("\r", "\n"):
                        line = cmd_buf.strip()
                        cmd_buf = ""
                        if not line:
                            show_menu()
                        elif line.lower() == "go":
                            cmd_mode = False
                            usb_print("  Bridge active | {} baud".format(baudrate))
                        elif line.isdigit() and 1 <= int(line) <= len(BAUDRATES):
                            nr, new_baud, desc = BAUDRATES[int(line) - 1]
                            baudrate = new_baud
                            uart = make_uart(baudrate)
                            usb_print("  OK - baudrate set to {} ({})".format(baudrate, desc))
                            usb_print("  Type [go] to return to bridge or number to change.")
                        else:
                            usb_print("  Unknown option: '{}'  (type 1-{} or 'go')".format(line, len(BAUDRATES)))
                    elif ch == "\x08":
                        cmd_buf = cmd_buf[:-1]
                    else:
                        cmd_buf += ch
                        sys.stdout.write(ch)
                else:
                    seq_buf += ch
                    if seq_buf.endswith("+++"):
                        seq_buf = ""
                        cmd_mode = True
                        show_menu()
                    else:
                        if len(seq_buf) > 3:
                            uart.write(seq_buf[:-3].encode() if isinstance(seq_buf[:-3], str) else seq_buf[:-3])
                            seq_buf = seq_buf[-3:]
                        uart.write(ch if isinstance(ch, bytes) else ch.encode())

        if not cmd_mode:
            n = uart.any()
            if n:
                data = uart.read(n)
                sys.stdout.buffer.write(data)
                led.toggle()

    except KeyboardInterrupt:
        pass
