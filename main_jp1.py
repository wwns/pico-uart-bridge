"""
Raspberry Pi Pico - Most USB <-> UART dla JP1 (URC-7120 i inne)
================================================================

ZASTOSOWANIE: programowanie pilotow JP1.x przez RMIR lub Remote Master
BAUDRATE: 9600 (staly — wymagany przez interfejs JP1)
BRAK MENU — czysty most, zaden bajt nie jest przechwytywany

Schemat polaczen:
  Pico GP0 (TX, pin 1) ──────────────────► [6] RXD pilota  (Bialy)
  Pico GP1 (RX, pin 2) ◄────────────────── [4] TXD pilota  (Zielony)
  Pico GND  (pin 3)    ──────────────────── [3] GND pilota  (Czarny)
  Pico GP3  (pin 5)    ──── HIGH ─────────► [2] RTS pilota  (Zolty)  [opcja]

  [1] VDD   pilota — NIE PODLACZAC (pilot ma wlasne baterie)
  [5] RESET pilota — NIE PODLACZAC

Polaczenie z RMIR:
  1. Flashuj ten plik jako main.py na Pico
  2. Podlacz pilot do Pico (4 przewody lub 3)
  3. Otworz RMIR → Interface: "JP1.X Serial" → Port: Pico COM
  4. Baudrate w RMIR: auto albo 9600

UWAGA: Numer COM portu Pico sprawdz w Menedzerze Urzadzen Windows.
"""

import machine
import sys
import utime
import uselect
import micropython

# -- Oczekiwanie na mpremote (2s wystarczy dla JP1 — skrocone vs 10s w main.py)
utime.sleep_ms(2000)
micropython.kbd_intr(-1)

# -- GP3 = RTS output HIGH (sygnalizuje gotowsc do pilota)
rts_out = machine.Pin(3, machine.Pin.OUT)
rts_out.on()

# -- LED
led = machine.Pin(25, machine.Pin.OUT)

# -- UART0 na GP0/GP1, 9600 baud (standard JP1)
BAUDRATE = 9600
uart = machine.UART(0, baudrate=BAUDRATE,
                    tx=machine.Pin(0), rx=machine.Pin(1), timeout=0)

# 3x blysk = gotowe
for _ in range(3):
    led.toggle()
    utime.sleep_ms(150)
led.on()

poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

LED_TIMEOUT = 100   # ms bez transferu = LED wraca do ON
last_xfer   = utime.ticks_ms()

while True:
    try:
        # --- USB (PC/RMIR) → UART (pilot) ---
        if poll.poll(0):
            ch = sys.stdin.buffer.read(1)
            if ch:
                uart.write(ch)
                led.off()
                last_xfer = utime.ticks_ms()

        # --- UART (pilot) → USB (PC/RMIR) ---
        n = uart.any()
        if n:
            data = uart.read(n)
            sys.stdout.buffer.write(data)
            led.off()
            last_xfer = utime.ticks_ms()

        # LED wraca do ON po przerwie w transferze
        if not led.value() and utime.ticks_diff(utime.ticks_ms(), last_xfer) > LED_TIMEOUT:
            led.on()

    except KeyboardInterrupt:
        pass
