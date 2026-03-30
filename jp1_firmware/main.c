/*
 * Pico JP1 USB Adapter — TinyUSB CDC Bridge
 * ==========================================
 * Mapuje stany RTS/DTR z USB CDC na piny GPIO.
 * RMIR używa RTS do bit-bangowania magistrali JP1.
 *
 * Piny:
 *   GP0  (pin 1)  — UART TX → RXD urządzenia
 *   GP1  (pin 2)  — UART RX ← TXD urządzenia
 *   GP2  (pin 4)  — RTS output  ← HOST RTS
 *   GP3  (pin 5)  — DTR output  ← HOST DTR
 *   GP25          — LED (aktywność)
 *
 * JP1 connector (pilot):
 *   JP1[1] = VCC   (nie podłączaj — pilot zasilany bateryjnie)
 *   JP1[2] = RST   → GP2 (RTS z hosta, bit-bang RMIR)
 *   JP1[3] = GND   → Pico GND
 *   JP1[4] = TX    → GP1 (RX Pico)
 *   JP1[5] = (brak)
 *   JP1[6] = RX    → GP0 (TX Pico)
 */

#include <string.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "tusb.h"

// ---- Piny ----
#define UART_ID       uart0
#define PIN_TX        0
#define PIN_RX        1
#define PIN_RTS       2    // RTS z hosta → GP2
#define PIN_DTR       3    // DTR z hosta → GP3
#define PIN_LED       25

// ---- Bufor ----
#define BUF_SIZE      256

// ============================================================
// Callback: host zmienił stan RTS / DTR
// Wywoływane natychmiast przez TinyUSB (IRQ-level safe).
// ============================================================
void tud_cdc_line_state_cb(uint8_t itf, bool dtr, bool rts) {
    (void)itf;
    gpio_put(PIN_RTS, rts ? 1 : 0);
    gpio_put(PIN_DTR, dtr ? 1 : 0);
}

// Callback: host zmienił parametry linii (baudrate itp.)
void tud_cdc_line_coding_cb(uint8_t itf, cdc_line_coding_t const *coding) {
    (void)itf;
    // Synchronizuj baudrate UART z hostem
    uart_set_baudrate(UART_ID, coding->bit_rate);
}

// ============================================================
int main(void) {
    // ---- GPIO ----
    gpio_init(PIN_LED);
    gpio_set_dir(PIN_LED, GPIO_OUT);
    gpio_put(PIN_LED, 0);

    gpio_init(PIN_RTS);
    gpio_set_dir(PIN_RTS, GPIO_OUT);
    gpio_put(PIN_RTS, 1);   // idle HIGH

    gpio_init(PIN_DTR);
    gpio_set_dir(PIN_DTR, GPIO_OUT);
    gpio_put(PIN_DTR, 1);   // idle HIGH

    // ---- UART ----
    uart_init(UART_ID, 115200);
    gpio_set_function(PIN_TX, GPIO_FUNC_UART);
    gpio_set_function(PIN_RX, GPIO_FUNC_UART);
    gpio_pull_up(PIN_RX);   // RX idle = 3.3V

    // ---- TinyUSB ----
    tusb_init();

    // Krótki blink: gotowość
    for (int i = 0; i < 6; i++) {
        gpio_put(PIN_LED, i & 1);
        sleep_ms(80);
    }
    gpio_put(PIN_LED, 1);

    // ---- Pętla główna ----
    uint8_t buf[BUF_SIZE];

    while (true) {
        tud_task();   // obsługa zdarzeń USB

        // USB → UART
        uint32_t avail = tud_cdc_available();
        if (avail > 0) {
            uint32_t count = tud_cdc_read(buf,
                avail < BUF_SIZE ? avail : BUF_SIZE);
            uart_write_blocking(UART_ID, buf, count);
            gpio_put(PIN_LED, !gpio_get(PIN_LED));
        }

        // UART → USB
        if (tud_cdc_connected()) {
            uint32_t sent = 0;
            while (uart_is_readable(UART_ID) && sent < BUF_SIZE) {
                buf[sent++] = uart_getc(UART_ID);
            }
            if (sent > 0) {
                tud_cdc_write(buf, sent);
                tud_cdc_write_flush();
                gpio_put(PIN_LED, !gpio_get(PIN_LED));
            }
        }
    }

    return 0;
}
