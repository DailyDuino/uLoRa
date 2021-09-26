# uLoRa
Pi Pico Micropython Module for sending and receiving data using Ra-02 LoRa

## Compatible Hardware

* Ra-02 Ai-Thinker -> Tested

### Wiring

| Ra-02 Module | Pi Pico |
| :---------------------: | :------:|
| VCC | 3.3V |
| GND | GND |
| SCK | GPIO2 |
| MISO | GPIO4 |
| MOSI | GPIO3 |
| NSS | GPIO5 |
| NRESET | GPIO7 |
| DIO0 | GPIO6 |

### Notes
* The SPI pins can be re-mapped to comaptible alternate pins in pi pico.
* Ra-02 module might require external 3.3V Regulator due to power requirement

## Installation
1. Open Thonny
2. In the Menubar go to `View` -> `Files`
3. A Sidebar will appear. In `This computer` section navigate to the folder where you have cloned this Repo.
4. Right Click on `uLoRa.py` and select `Upload to /`

## Source
Ported from [sandeepmistery's](https://github.com/sandeepmistry) [arduino-LoRa](https://github.com/sandeepmistry/arduino-LoRa) Library




