"""
Raspberry Pi Pico - Przezroczysty most USB <-> UART
=====================================================

Schemat polaczen:
  Windows (PuTTY/COM4, 115200) <--USB--> Pico <--UART--> Decices

  Pico GP0 (TX, pin 1)  ---->  (RX)
  Pico GP1 (RX, pin 2)  <----  (TX)
  Pico GND  (pin 3/38)  ----   GND  

Pico dziala jako przezroczysty konwerter USB<->UART:
  - LED swieci = uart aktywny; miga = transfer danych
"""

import machine
import sys
import utime
import uselect
import micropython

# 10s okno dla mpremote, potem blokuj Ctrl+C
utime.sleep_ms(10000)
micropython.kbd_intr(-1)

# (numer, baudrate, opis urzadzenia)
BAUDRATES = [
    ( 1,   1200, "Stare urzadzenia, czujniki"),
    ( 2,   2400, "Stare urzadzenia"),
    ( 3,   4800, "GPS, stare urzadzenia"),
    ( 4,   9600, "Arduino domyslny, GPS, GSM"),
    ( 5,  19200, "Modemy, sterowniki PLC"),
    ( 6,  38400, "Modemy, Bluetooth HC-05/06"),
    ( 7,  57600, "Bluetooth, szybkie moduly"),
    ( 8,  74880, "ESP8266 boot ROM jak widzisz krzaki"),
    ( 9, 115200, "ESP8266/ESP32 Arduino"),
    (10, 230400, "ESP32 szybki transfer"),
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
    usb_print("|       PICO USB<->UART BRIDGE - USTAWIENIA           |")
    usb_print("+" + "-" * 54 + "+")
    usb_print(f"|  Aktualny baudrate: {baudrate:<6}                          |")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  Nr | Baudrate |  Opis                               |")
    usb_print("|" + "-" * 54 + "|")
    for nr, baud, opis in BAUDRATES:
        marker = " <--" if baud == baudrate else "    "
        usb_print(f"|  {nr:>2} | {baud:>8} | {opis:<35} |{marker}")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  Wpisz numer (1-10) i Enter aby zmienic baudrate     |")
    usb_print("|  Wpisz [go] i Enter aby wrocic do trybu bridge       |")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  Aby wejsc do menu: wpisz +++                        |")
    usb_print("+" + "-" * 54 + "+")

uart = make_uart(baudrate)
led  = machine.Pin(25, machine.Pin.OUT)

# 6x blysk = Pico gotowe
for _ in range(6):
    led.toggle()
    utime.sleep_ms(100)
led.on()

usb_print(f"=== UART GOTOWY | {baudrate} baud | GP0->TX GP1->RX | wpisz +++ = menu ===")

poll     = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

cmd_mode = False
seq_buf  = ""    # bufor do wykrywania +++
cmd_buf  = ""    # bufor komendy w trybie cmd

while True:
    try:
        # --- USB → UART lub obsługa komendy ---
        if poll.poll(0):
            ch = sys.stdin.read(1)
            if ch:
                if cmd_mode:
                    # Tryb komendy: zbieraj linie
                    if ch in ("\r", "\n"):
                        line = cmd_buf.strip()
                        cmd_buf = ""
                        if not line:
                            show_menu()
                        elif line.lower() == "go":
                            cmd_mode = False
                            usb_print(f"  Bridge aktywny | {baudrate} baud")
                        elif line.isdigit() and 1 <= int(line) <= len(BAUDRATES):
                            nr, new_baud, opis = BAUDRATES[int(line) - 1]
                            baudrate = new_baud
                            uart = make_uart(baudrate)
                            usb_print(f"  OK - baudrate zmieniony na {baudrate} ({opis})")
                            usb_print(f"  Wpisz [go] aby wrocic do bridge lub numer aby zmienic.")
                        else:
                            usb_print(f"  Nieznana opcja: '{line}'  (wpisz numer 1-{len(BAUDRATES)} lub 'go')")
                    elif ch == "\x08":  # backspace
                        cmd_buf = cmd_buf[:-1]
                    else:
                        cmd_buf += ch
                        sys.stdout.write(ch)  # echo
                else:
                    # Tryb bridge: wykryj +++
                    seq_buf += ch
                    if seq_buf.endswith("+++"):
                        seq_buf = ""
                        cmd_mode = True
                        show_menu()
                    else:
                        if len(seq_buf) > 3:
                            # Wyslij zalegly bufor do UART
                            uart.write(seq_buf[:-3].encode() if isinstance(seq_buf[:-3], str) else seq_buf[:-3])
                            seq_buf = seq_buf[-3:]
                        uart.write(ch if isinstance(ch, bytes) else ch.encode())

        # --- UART → USB ---
        if not cmd_mode:
            n = uart.any()
            if n:
                sys.stdout.buffer.write(uart.read(n))

    except KeyboardInterrupt:
        pass  # ignoruj Ctrl+C







