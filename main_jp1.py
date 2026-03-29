"""
Raspberry Pi Pico - JP1 EEPROM Adapter dla RMIR
================================================

URC-7120 i inne oryginalne JP1 remoty maja chip EEPROM (24C32, I2C).
RMIR wysyla komendy E/I/V/R/S po USB serial 38400 baud.
Pico tluma to na I2C do chipa EEPROM w pilocie.

Schemat polaczen (6-pin zlacze JP1 w pilocie):
  Pico 3V3(OUT) (pin 36) ──────────────── [1]+[2] Vdd pilota  (zasilanie EEPROM!)
  Pico GND               ──────────────── [3] GND pilota
  Pico GP4/SDA (pin 6)   ──────────────── [4] SDA pilota  (I2C data)
  Pico GND               ──────────────── [5] RESET pilota (do masy)
  Pico GP5/SCL (pin 7)   ──────────────── [6] SCL pilota  (I2C clock)

  WAZNE: Pin [1]+[2] (Vdd) to zasilanie chipa EEPROM — nie baterie pilota!
  FTDI/CP2102 dawalo tu RTS=3.45V jako VCC. Pico daje 3V3(OUT) = stale 3.3V.
  Pin [5] (RESET) musi byc do GND (wymagane przez protokol I2C EEPROM).

Polaczenie z RMIR:
  1. Flashuj ten plik jako main.py na Pico
  2. Podlacz pilot (5 przewodow jak above)
  3. Wyjmij baterie z pilota (opcja — ale bezpieczniej)
  4. Otworz RMIR → Interface: "JP1.X Serial" → Port: COM4
  5. Baudrate: 38400 (NIE 9600!)
  6. Kliknij "Read Remote"

Protokol: Kevin Timmerman JP1 EEPROM Programmer
  http://www.compendiumarcana.com/jp1epa/
  Komendy: E(ping) I(ident) V(vars) R(read) S(write) C(erase) 1/2(addr) 4/8/6/3(size)
  Checksum: XOR wszystkich bajtow pakietu = 0
  EEPROM I2C addr: 0x50, domyslny rozmiar: 24C32 (4KB)
"""

import machine
import sys
import utime
import uselect
from machine import I2C, Pin

# ── Hardware ──────────────────────────────────────────────────────────────────
led = Pin(25, Pin.OUT)
led.on()

# I2C: GP4=SDA, GP5=SCL, 100kHz (standardowy I2C)
# Wbudowane pull-up rezystory Pico (~50kOhm) — wystarczaja gdy pilot ma baterie 2xAA
Pin(4, Pin.IN, Pin.PULL_UP)
Pin(5, Pin.IN, Pin.PULL_UP)
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)

# ── Protokol JP1 EPA ──────────────────────────────────────────────────────────
DEVADDR      = 0x50   # adres I2C chipa EEPROM (24Cxx)
ACK          = 0x06
NAK          = 0x15
EEPROM_ID    = b'24C32\x00'   # identyfikator zwracany przez komende I

ee_size      = 4096   # domyslnie 24C32 = 4KB
two_byte_adr = True   # 24C32 wymaga 2-bajtowego adresu

# ── USB serial (RMIR) ─────────────────────────────────────────────────────────
usb_in  = sys.stdin.buffer
usb_out = sys.stdout.buffer
poll    = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)


def ser_rx():
    """Czekaj na 1 bajt z USB (blokujace)."""
    while not poll.poll(100):
        led.toggle()
    led.on()
    return usb_in.read(1)[0]


def ser_tx(data):
    """Wyslij bajty do USB."""
    usb_out.write(data)


def chk(data):
    """Checksum XOR wszystkich bajtow. Poprawny pakiet: XOR = 0."""
    c = 0
    for b in data:
        c ^= b
    return c


def eeprom_read(addr, length):
    """Czytaj length bajtow z EEPROM pod adresem addr."""
    if two_byte_adr:
        i2c.writeto(DEVADDR, bytes([addr >> 8, addr & 0xFF]))
    else:
        i2c.writeto(DEVADDR, bytes([addr & 0xFF]))
    return i2c.readfrom(DEVADDR, length)


def eeprom_write(addr, data):
    """Zapisuj dane do EEPROM strona po stronie (page write = 32B dla 24C32)."""
    PAGE = 32
    offset = 0
    while offset < len(data):
        chunk = data[offset:offset + PAGE]
        if two_byte_adr:
            buf = bytes([((addr + offset) >> 8), ((addr + offset) & 0xFF)]) + chunk
        else:
            buf = bytes([(addr + offset) & 0xFF]) + chunk
        i2c.writeto(DEVADDR, buf)
        utime.sleep_ms(10)  # EEPROM write cycle
        offset += PAGE


def C16():
    global ee_size, two_byte_adr
    ee_size = 4096
    two_byte_adr = True


# ── Glowna petla komend ───────────────────────────────────────────────────────
C16()

# Skan I2C — sprawdz czy EEPROM podlaczony
_devs = i2c.scan()
_found = DEVADDR in _devs
# Blyski: szybkie3 = OK, wolne3 = brak EEPROM (ale dziala dalej)
for _ in range(3):
    led.toggle(); utime.sleep_ms(80 if _found else 500)
led.on()

while True:
    cmd = ser_rx()

    if cmd == ord('E'):                          # Ping — 1 bajt, brak chk
        ser_tx(bytes([ACK]))

    elif cmd == ord('I'):                        # Identify — 1 bajt, brak chk
        payload = EEPROM_ID
        ser_tx(payload + bytes([chk(payload)]))

    elif cmd == ord('V'):                        # Get Variables — 1 bajt, brak chk
        sz_h = (ee_size >> 8) & 0xFF
        sz_l = ee_size & 0xFF
        payload = bytes([sz_h, sz_l, 0, 0])
        ser_tx(payload + bytes([chk(payload)]))

    elif cmd == ord('R'):                        # Read — ma checksum
        addrh = ser_rx()
        addrl = ser_rx()
        length = ser_rx()
        c = ser_rx()
        if chk(bytes([cmd, addrh, addrl, length, c])) == 0:
            addr = (addrh << 8) | addrl
            try:
                data = eeprom_read(addr, length)
                ser_tx(bytes([ord('r')]) + data + bytes([chk(bytes([ord('r')]) + data)]))
            except Exception:
                ser_tx(bytes([NAK]))

    elif cmd == ord('S'):                        # Write — ma checksum
        addrh = ser_rx()
        addrl = ser_rx()
        length = ser_rx()
        buf = bytearray()
        for _ in range(length):
            buf.append(ser_rx())
        c = ser_rx()
        if chk(bytes([cmd, addrh, addrl, length]) + buf + bytes([c])) == 0:
            addr = (addrh << 8) | addrl
            try:
                eeprom_write(addr, bytes(buf))
                ser_tx(bytes([ACK]))
            except Exception:
                ser_tx(bytes([NAK]))

    elif cmd == ord('C'):                        # Erase — ma checksum (ignoruj, ACK)
        addrh = ser_rx(); addrl = ser_rx()
        cnth  = ser_rx(); cntl  = ser_rx()
        c = ser_rx()
        if chk(bytes([cmd, addrh, addrl, cnth, cntl, c])) == 0:
            ser_tx(bytes([ACK]))

    elif cmd in (ord('1'), ord('2'), ord('3'),   # addr/size — 1 bajt, brak chk
                 ord('4'), ord('6'), ord('8')):
        global two_byte_adr, ee_size
        if   cmd == ord('1'): two_byte_adr = False
        elif cmd == ord('2'): two_byte_adr = True
        elif cmd == ord('3'): ee_size = 4096; two_byte_adr = True
        elif cmd == ord('4'): ee_size = 512;  two_byte_adr = False
        elif cmd == ord('6'): ee_size = 2048; two_byte_adr = False
        elif cmd == ord('8'): ee_size = 1024; two_byte_adr = False
        ser_tx(bytes([ACK]))

