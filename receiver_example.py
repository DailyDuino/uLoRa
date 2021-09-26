import machine
import utime
import time
import _thread
import ustruct
import sys

import uLoRa as lora

cspin = machine.Pin(5,machine.Pin.OUT)
dio0 = machine.Pin(6,machine.Pin.IN)
rst = machine.Pin(7,machine.Pin.OUT)
#rst = None # uncomment if you are not using reset pin
spi = machine.SPI(0,
                  baudrate=1000000,
                  polarity=1,
                  phase=1,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(2),
                  mosi=machine.Pin(3),
                  miso=machine.Pin(4))



cspin.value(1)

lora_init = lora.begin(spi,cspin,rst,dio0,433)


if lora_init:
    print("LoRa OK")
else:
    print("LoRa Failed!!")
        
    
while True:
    if lora_init:
        packet_size = lora.parsePacket()
        if packet_size > 0:
            print("Received Packet")
            while lora.available() > 0:
                print(chr(lora.read()))
            print(" with RSSI ")
            print(lora.packetRssi())
        #time.sleep(1)