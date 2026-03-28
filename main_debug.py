"""
Raspberry Pi Pico - Przezroczysty most USB <-> UART z RTS/CTS + Debug
======================================================================

 PINOUT PICO v1  (na podstawie oficjalnego schematu)
 ╔══════════════════════════════════════════════════════════════════════════════════════════════╗
 ║                         RASPBERRY Pi PICO v1 — KOMPLETNY PINOUT                            ║
 ╚══════════════════════════════════════════════════════════════════════════════════════════════╝
 
                                            ┌──[micro USB]──┐
                                            │  LED (GP25) ● │
                                            │               │
  UART0TX I2C0SDA SPI0RX  ★ GP0  [ 1] ────●┤               ├●──── [40] VBUS  (5V z USB)
  UART0RX I2C0SCL SPI0CSn ★ GP1  [ 2] ────●┤               ├●──── [39] VSYS  (zasilanie)
                     GND    GND  [ 3] ────■┤               ├■──── [38] GND
  I2C1SDA SPI0SCK        ★ GP2  [ 4] ────●┤               ├●──── [37] 3V3_EN
  I2C1SCL SPI0TX         ★ GP3  [ 5] ────●┤  [BOOTSEL]    ├●──── [36] 3V3 OUT (3.3V/300mA)
  UART1TX I2C0SDA SPI0RX ★ GP4  [ 6] ────●┤               ├●──── [35] ADC_VREF
  UART1RX I2C0SCL SPI0CSn  GP5  [ 7] ────●┤               ├●──── [34] GP28 / ADC2
                     GND    GND  [ 8] ────■┤               ├■──── [33] AGND
  I2C1SDA SPI0SCK           GP6  [ 9] ────●┤               ├●──── [32] GP27 / ADC1 / I2C1SCL
  I2C1SCL SPI0TX             GP7  [10] ────●┤               ├●──── [31] GP26 / ADC0 / I2C1SDA
  UART1TX I2C0SDA SPI1RX     GP8  [11] ────●┤               ├●──── [30] RUN  (reset)
  UART1RX I2C0SCL SPI1CSn    GP9  [12] ────●┤               ├●──── [29] GP22
                     GND    GND  [13] ────■┤               ├■──── [28] GND
  I2C1SDA SPI1SCK            GP10 [14] ────●┤               ├●──── [27] GP21 / I2C0SCL
  I2C1SCL SPI1TX             GP11 [15] ────●┤               ├●──── [26] GP20 / I2C0SDA
  UART0TX I2C0SDA SPI1RX     GP12 [16] ────●┤               ├●──── [25] GP19 / I2C1SCL / SPI0TX
  UART0RX I2C0SCL SPI1CSn    GP13 [17] ────●┤               ├●──── [24] GP18 / I2C1SDA / SPI0SCK
                     GND    GND  [18] ────■┤               ├■──── [23] GND
  I2C1SDA SPI1SCK            GP14 [19] ────●┤               ├●──── [22] GP17 / UART0RX / SPI0CSn
  I2C1SCL SPI1TX             GP15 [20] ────●┤               ├●──── [21] GP16 / UART0TX / SPI0RX
                                            │               │
                                            └──●───■───●────┘
                                             SWCLK GND SWDIO
                                             (SWD debug port)
 
  ★ = piny uzyte w projekcie bridge
 
 ╔═════╦════════╦══════════════╦══════════════════════════════════════════════════════════════╗
 ║ Pin ║  GPIO  ║  Peryferial  ║  Funkcja w projekcie                                        ║
 ╠═════╬════════╬══════════════╬══════════════════════════════════════════════════════════════╣
 ║  1  ║  GP0   ║  UART0 TX   ║  ──►  RX urzadzenia docelowego                              ║
 ║  2  ║  GP1   ║  UART0 RX   ║  ◄──  TX urzadzenia docelowego                              ║
 ║  3  ║  GND   ║  Masa       ║  ────  GND urzadzenia + GND adaptera debug                   ║
 ║  4  ║  GP2   ║  UART0 CTS  ║  ◄──  RTS urzadzenia  [flow ctrl, wl. przez [rts] w menu]   ║
 ║  5  ║  GP3   ║  UART0 RTS  ║  ──►  CTS urzadzenia  [flow ctrl, wl. przez [rts] w menu]   ║
 ║  6  ║  GP4   ║  UART1 TX   ║  ──►  RX adaptera debug (tylko TX!)  [wl. przez [dbg]]      ║
 ║  —  ║  GP25  ║  GPIO OUT   ║  LED wbudowany (6x blink=start, swieci=bridge aktywny)       ║
 ╚═════╩════════╩══════════════╩══════════════════════════════════════════════════════════════╝
 
 POLACZENIE MINIMALNE (bez flow control):
   Pico GP0 (pin 1) ──►  RX urzadzenia
   Pico GP1 (pin 2) ◄──  TX urzadzenia
   Pico GND (pin 3) ────  GND urzadzenia

 POLACZENIE Z RTS/CTS:
   Pico GP0 (pin 1) ──►  RX urzadzenia
   Pico GP1 (pin 2) ◄──  TX urzadzenia
   Pico GP2 (pin 4) ◄──  RTS urzadzenia
   Pico GP3 (pin 5) ──►  CTS urzadzenia
   Pico GND (pin 3) ────  GND urzadzenia

 DEBUG (opcjonalny, osobny adapter USB-serial 3.3V):
   Pico GP4 (pin 6) ──►  RX adaptera debug
   Pico GND (pin 3) ────  GND adaptera debug
   Adapter debug TX  NIE podlaczaj (wyjscie tylko)
   Otworz drugi terminal na 115200 baud aby widziec logi

 MENU (wpisz +++ w terminalu bridge):
   1-10  zmiana baudrate
   [rts] wl/wyl hardware RTS/CTS
   [dbg] wl/wyl debug na GP4/UART1
   [go]  powrot do trybu bridge
"""

import machine
import sys
import utime
import uselect
import micropython

# ── 10s okno dla mpremote, potem blokuj Ctrl+C ──────────────────────────────
utime.sleep_ms(10000)
micropython.kbd_intr(-1)

# ── Konfiguracja baudrate ────────────────────────────────────────────────────
BAUDRATES = [
    ( 1,   1200, "Stare urzadzenia, czujniki"),
    ( 2,   2400, "Stare urzadzenia"),
    ( 3,   4800, "GPS, stare urzadzenia"),
    ( 4,   9600, "Arduino domyslny, GPS, GSM"),
    ( 5,  19200, "Modemy, sterowniki PLC"),
    ( 6,  38400, "Modemy, Bluetooth HC-05/06"),
    ( 7,  57600, "Bluetooth, szybkie moduly"),
    ( 8,  74880, "ESP8266 boot ROM (krzaki przy starcie)"),
    ( 9, 115200, "ESP8266/ESP32 Arduino  [DOMYSLNY]"),
    (10, 230400, "ESP32 szybki transfer"),
]

baudrate  = 115200
flow_ctrl = False    # True = hardware RTS/CTS wlaczone (GP2/GP3)
debug_on  = False    # True = logi na UART1 (GP4, pin 6)

# Liczniki bajtow (widoczne w logach debug)
cnt_usb_to_uart = 0
cnt_uart_to_usb = 0


# ── UART helper ──────────────────────────────────────────────────────────────
def make_uart(baud, flow):
    """Tworzy UART0 z podanym baudrate i opcjonalnym RTS/CTS."""
    if flow:
        return machine.UART(0, baudrate=baud,
                            tx=machine.Pin(0),
                            rx=machine.Pin(1),
                            cts=machine.Pin(2),   # GP2 pin 4  ◄── RTS urzadzenia
                            rts=machine.Pin(3),   # GP3 pin 5  ──► CTS urzadzenia
                            timeout=0)
    else:
        return machine.UART(0, baudrate=baud,
                            tx=machine.Pin(0),
                            rx=machine.Pin(1),
                            timeout=0)


# ── Debug UART (UART1, GP4, pin 6) ──────────────────────────────────────────
dbg_uart = machine.UART(1, baudrate=115200, tx=machine.Pin(4), timeout=0)

def dbg(msg):
    """Wyslij linie debug na UART1 (GP4). Aktywny tylko gdy debug_on=True."""
    if debug_on:
        dbg_uart.write((msg + "\r\n").encode())

def dbg_bytes(direction, data):
    """Wyslij hex dump przesylanych bajtow na debug uart."""
    if debug_on and data:
        hex_str = " ".join(f"{b:02X}" for b in data)
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in data)
        dbg_uart.write(f"{direction} [{len(data):3d}B] {hex_str}  |{ascii_str}|\r\n".encode())


# ── USB print ────────────────────────────────────────────────────────────────
def usb_print(msg):
    sys.stdout.write(msg + "\r\n")


# ── Menu ─────────────────────────────────────────────────────────────────────
def show_menu():
    flow_str = "WLACZONY  (GP2=CTS  GP3=RTS)" if flow_ctrl else "WYLACZONY"
    dbg_str  = f"WLACZONY  (GP4 TX, 115200 baud)" if debug_on else "WYLACZONY"
    usb_print("")
    usb_print("+" + "-" * 58 + "+")
    usb_print("|     PICO USB<->UART BRIDGE - USTAWIENIA               |")
    usb_print("+" + "-" * 58 + "+")
    usb_print(f"|  Baudrate : {baudrate:<8}                                   |")
    usb_print(f"|  RTS/CTS  : {flow_str:<45} |")
    usb_print(f"|  Debug    : {dbg_str:<45} |")
    usb_print(f"|  Liczniki : USB->UART={cnt_usb_to_uart}B  UART->USB={cnt_uart_to_usb}B        |")
    usb_print("+" + "-" * 58 + "+")
    usb_print("|  Nr | Baudrate |  Opis                                  |")
    usb_print("|" + "-" * 58 + "|")
    for nr, baud, opis in BAUDRATES:
        marker = " <--" if baud == baudrate else "    "
        usb_print(f"|  {nr:>2} | {baud:>8} | {opis:<38} |{marker}")
    usb_print("+" + "-" * 58 + "+")
    usb_print("|  Wpisz numer (1-10)  zmiana baudrate                   |")
    usb_print("|  Wpisz [rts]         wl/wyl hardware RTS/CTS           |")
    usb_print("|  Wpisz [dbg]         wl/wyl debug na GP4/UART1        |")
    usb_print("|  Wpisz [go]          powrot do trybu bridge            |")
    usb_print("+" + "-" * 58 + "+")
    usb_print("|  Aby wejsc do menu: wpisz +++                          |")
    usb_print("+" + "-" * 58 + "+")


# ── Inicjalizacja ─────────────────────────────────────────────────────────────
uart = make_uart(baudrate, flow_ctrl)
led  = machine.Pin(25, machine.Pin.OUT)   # Pico v1: LED = pin 25

# 6x blysk = Pico gotowe
for _ in range(6):
    led.toggle()
    utime.sleep_ms(100)
led.on()

flow_info = "RTS/CTS:WYL" if not flow_ctrl else "RTS/CTS:WL(GP2/GP3)"
usb_print(f"=== BRIDGE GOTOWY | {baudrate} baud | {flow_info} | debug:WYL(GP4) | +++ = menu ===")

dbg(f"=== PICO BRIDGE BOOT | {baudrate} baud | flow={flow_ctrl} ===")

poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

cmd_mode = False
seq_buf  = ""    # bufor wykrywania +++
cmd_buf  = ""    # bufor wpisywanej komendy


# ── Glowna petla ──────────────────────────────────────────────────────────────
while True:
    try:
        # ── USB → UART lub obsluga menu ──────────────────────────────────────
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
                            flow_info = "RTS/CTS:WL" if flow_ctrl else "RTS/CTS:WYL"
                            dbg_info  = "debug:WL" if debug_on else "debug:WYL"
                            usb_print(f"  Bridge aktywny | {baudrate} baud | {flow_info} | {dbg_info}")
                            dbg(f"--- Bridge aktywny | {baudrate} baud | flow={flow_ctrl} | debug={debug_on} ---")
                        elif line.lower() == "rts":
                            flow_ctrl = not flow_ctrl
                            uart = make_uart(baudrate, flow_ctrl)
                            stan = "WLACZONY  (GP2=CTS, GP3=RTS)" if flow_ctrl else "WYLACZONY"
                            usb_print(f"  RTS/CTS {stan}")
                            dbg(f"RTS/CTS zmieniony na: {flow_ctrl}")
                            show_menu()
                        elif line.lower() == "dbg":
                            debug_on = not debug_on
                            stan = "WLACZONY  (GP4 TX, 115200 baud)" if debug_on else "WYLACZONY"
                            usb_print(f"  Debug {stan}")
                            dbg(f"=== DEBUG WLACZONY | {baudrate} baud | flow={flow_ctrl} ===")
                            show_menu()
                        elif line.isdigit() and 1 <= int(line) <= len(BAUDRATES):
                            nr, new_baud, opis = BAUDRATES[int(line) - 1]
                            baudrate = new_baud
                            uart = make_uart(baudrate, flow_ctrl)
                            usb_print(f"  OK - baudrate zmieniony na {baudrate} ({opis})")
                            usb_print(f"  Wpisz [go] aby wrocic lub numer aby zmienic ponownie.")
                            dbg(f"Baudrate zmieniony na {baudrate}")
                        else:
                            usb_print(f"  Nieznana opcja: '{line}'")
                            usb_print(f"  Dostepne: 1-{len(BAUDRATES)} | rts | dbg | go")
                    elif ch == "\x08":   # backspace
                        cmd_buf = cmd_buf[:-1]
                    else:
                        cmd_buf += ch
                        sys.stdout.write(ch)   # lokalny echo
                else:
                    # Tryb bridge: wykryj +++
                    seq_buf += ch
                    if seq_buf.endswith("+++"):
                        seq_buf = ""
                        cmd_mode = True
                        dbg(f"--- MENU otwarte | cnt USB->UART={cnt_usb_to_uart}B UART->USB={cnt_uart_to_usb}B ---")
                        show_menu()
                    else:
                        if len(seq_buf) > 3:
                            pending = seq_buf[:-3]
                            data = pending.encode() if isinstance(pending, str) else pending
                            uart.write(data)
                            cnt_usb_to_uart += len(data)
                            dbg_bytes("USB->UART", data)
                            seq_buf = seq_buf[-3:]
                        data = ch if isinstance(ch, bytes) else ch.encode()
                        uart.write(data)
                        cnt_usb_to_uart += len(data)
                        dbg_bytes("USB->UART", data)

        # ── UART → USB: dane z urzadzenia do PC ──────────────────────────────
        if not cmd_mode:
            n = uart.any()
            if n:
                data = uart.read(n)
                sys.stdout.buffer.write(data)
                cnt_uart_to_usb += len(data)
                dbg_bytes("UART->USB", data)

    except KeyboardInterrupt:
        pass   # Ctrl+C ignorowany, bridge dziala dalej
