"""
Selftest Raspberry Pi Pico
Uruchom: mpremote connect COM4 run selftest.py
"""
import machine
import utime
import gc
import sys

PASS = "[ OK ]"
FAIL = "[FAIL]"
INFO = "[INFO]"

def test(name, fn):
    try:
        result = fn()
        if result is False:
            print(f"{FAIL} {name}")
            return False
        else:
            msg = f" ({result})" if result is not True else ""
            print(f"{PASS} {name}{msg}")
            return True
    except Exception as e:
        print(f"{FAIL} {name} — {e}")
        return False

print()
print("=" * 40)
print("  PICO SELFTEST")
print("=" * 40)

ok = 0
fail = 0

# 1. LED
def t_led():
    led = machine.Pin(25, machine.Pin.OUT)
    for _ in range(6):
        led.toggle()
        utime.sleep_ms(80)
    led.on()
    return True

r = test("LED GP25 (miga 6x)", t_led)
ok += r; fail += not r

# 2. CPU freq
def t_cpu():
    f = machine.freq()
    if f < 100_000_000:
        return False
    return f"{f//1_000_000} MHz"

r = test("CPU freq >= 100 MHz", t_cpu)
ok += r; fail += not r

# 3. RAM
def t_ram():
    gc.collect()
    free = gc.mem_free()
    alloc = gc.mem_alloc()
    total = free + alloc
    if free < 50_000:
        return False
    return f"free={free//1024}kB total={total//1024}kB"

r = test("RAM (min 50kB wolne)", t_ram)
ok += r; fail += not r

# 4. Flash filesystem
def t_flash():
    import uos
    s = uos.statvfs("/")
    block_size = s[0]
    total_blocks = s[2]
    free_blocks = s[3]
    total_kb = (block_size * total_blocks) // 1024
    free_kb = (block_size * free_blocks) // 1024
    if total_kb < 500:
        return False
    return f"total={total_kb}kB free={free_kb}kB"

r = test("Flash filesystem", t_flash)
ok += r; fail += not r

# 5. UART0 (GP0/GP1) — loopback jezeli masz zwarte TX-RX
def t_uart():
    uart = machine.UART(0, baudrate=9600,
                        tx=machine.Pin(0), rx=machine.Pin(1), timeout=50)
    uart.write(b"\xAA\x55")
    utime.sleep_ms(20)
    data = uart.read(2)
    uart.deinit()
    if data == b"\xAA\x55":
        return "loopback OK (TX-RX zwarte)"
    return "brak loopback (normalne jesli TX-RX nie zwarte)"

r = test("UART0 GP0/GP1", t_uart)
ok += r; fail += not r

# 6. GP2, GP3 jako GPIO
def t_gpio():
    errors = []
    for pin_num in [2, 3]:
        # OUT: ustaw HIGH i odczytaj z tego samego obiektu (RP2040 obsluguje readback)
        p = machine.Pin(pin_num, machine.Pin.OUT)
        p.on()
        utime.sleep_ms(2)
        if p.value() != 1:
            errors.append(f"GP{pin_num} HIGH fail")
        p.off()
        utime.sleep_ms(2)
        if p.value() != 0:
            errors.append(f"GP{pin_num} LOW fail")
        p.init(machine.Pin.IN)  # zostaw jako IN po tescie
    if errors:
        return False
    return "GP2 GP3 OK"

r = test("GPIO GP2/GP3", t_gpio)
ok += r; fail += not r

# 7. Unikalne ID
def t_uid():
    import machine
    uid = machine.unique_id()
    s = "".join("{:02X}".format(b) for b in uid)
    return s

r = test("Unique ID", t_uid)
ok += r; fail += not r

# 8. ADC (temperature sensor)
def t_adc():
    adc = machine.ADC(4)  # wbudowany czujnik temperatury
    raw = adc.read_u16()
    voltage = raw * 3.3 / 65535
    temp = 27 - (voltage - 0.706) / 0.001721
    if temp < 0 or temp > 80:
        return False
    return f"{temp:.1f} C"

r = test("ADC temp sensor", t_adc)
ok += r; fail += not r

# Podsumowanie
print("=" * 40)
print(f"  Wynik: {ok} OK  /  {fail} FAIL")
print("=" * 40)
if fail == 0:
    print("  Pico sprawne!")
else:
    print("  Wykryto problemy!")
print()
