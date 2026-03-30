cmake_minimum_required(VERSION 3.13)

# Pico SDK path - ustaw PICO_SDK_PATH w systemie lub odkomentuj:
# set(PICO_SDK_PATH "C:/pico-sdk")

include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(jp1_bridge C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(jp1_bridge
    main.c
    usb_descriptors.c
)

target_include_directories(jp1_bridge PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(jp1_bridge
    pico_stdlib
    hardware_uart
    tinyusb_device
    tinyusb_board
)

# Generuj .uf2 i .bin
pico_add_extra_outputs(jp1_bridge)

# Brak stdio przez UART/USB (TinyUSB zarządza USB samodzielnie)
pico_enable_stdio_usb(jp1_bridge 0)
pico_enable_stdio_uart(jp1_bridge 0)
