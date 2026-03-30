# Budowanie jp1_bridge (Pico SDK + TinyUSB)

## Wymagania

- [pico-sdk](https://github.com/raspberrypi/pico-sdk) — sklonuj i ustaw `PICO_SDK_PATH`
- CMake >= 3.13
- Arm GNU Toolchain (`arm-none-eabi-gcc`)
- Ninja lub make

## Instalacja pico-sdk (Windows)

```powershell
git clone https://github.com/raspberrypi/pico-sdk C:\pico-sdk
cd C:\pico-sdk
git submodule update --init          # pobiera TinyUSB
[System.Environment]::SetEnvironmentVariable("PICO_SDK_PATH","C:\pico-sdk","User")
```

## Budowanie

```powershell
cd C:\Users\wiesl\Pipico\jp1_firmware
mkdir build ; cd build
cmake -G "Ninja" -DCMAKE_BUILD_TYPE=Release ..
ninja
```

Wynik: `build/jp1_bridge.uf2`

## Wgrywanie

1. Przytrzymaj **BOOTSEL** na Pico i podłącz USB
2. Skopiuj `jp1_bridge.uf2` na dysk `RPI-RP2`

## Schemat podłączenia JP1

```
Pico         JP1 pilot
------       ---------
GP0 (TX) --> JP1[2] RXD
GP1 (RX) <-- JP1[3] TXD
GP2      --> JP1[5] (RTS — bit-bang JP1)
GP3      --> opcjonalnie DTR
GND      --- JP1[1] GND
             JP1[4] VCC — NIE podłączaj
```

## Jak to działa

`tud_cdc_line_state_cb()` jest wywoływany przez TinyUSB natychmiast gdy
RMIR zmieni stan RTS/DTR przez USB. Callback ustawia fizyczny GPIO —
Pico staje się transparentnym adapterem JP1 identycznym z CP2102/CH340.

Baudrate UART jest automatycznie synchronizowany z ustawieniami hosta
przez `tud_cdc_line_coding_cb()`.
