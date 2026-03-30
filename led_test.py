from machine import Pin
import utime
led = Pin(25, Pin.OUT)
for _ in range(10):
    led.on();  utime.sleep_ms(200)
    led.off(); utime.sleep_ms(200)
print("done")
