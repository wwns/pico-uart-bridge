#ifndef _TUSB_CONFIG_H_
#define _TUSB_CONFIG_H_

// Urządzenie USB na port 0
#define CFG_TUSB_RHPORT0_MODE   OPT_MODE_DEVICE

// Jeden interfejs CDC
#define CFG_TUD_CDC             1
#define CFG_TUD_CDC_RX_BUFSIZE  512
#define CFG_TUD_CDC_TX_BUFSIZE  512

// Brak HID, MSC, MIDi
#define CFG_TUD_HID             0
#define CFG_TUD_MSC             0
#define CFG_TUD_MIDI            0
#define CFG_TUD_VENDOR          0

#endif // _TUSB_CONFIG_H_
