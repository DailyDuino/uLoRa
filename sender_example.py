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
spi = machine.SPI(0,
                  baudrate=2000000,
                  polarity=1,
                  phase=1,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(2),
                  mosi=machine.Pin(3),
                  miso=machine.Pin(4))




lora_init = lora.begin(spi,cspin,rst,dio0,434)

if lora_init:
    print("LoRa OK")
    
else:
    print("LoRa Failed!!")
        
    
while True:
    if lora_init:
        lora.beginPacket()
        data = "Hello!!"
        enc_data = data.encode()
        packet = bytearray(enc_data)
        es = lora.dataPacket(packet)
        lora.endPacket()
        print("Packet Sent")
    time.sleep(2)
    