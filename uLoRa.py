
# Ported By Cyril Anthony (ArduDev - dailyduino.com).
# Source : sandeepmistry - arduino-LoRa


import machine
import utime
import time
import _thread
import ustruct
import sys

_implicitHeaderMode = False
_onTxDone = False
_frequency = 0

cs = None
dio0 = None
rst = None
spi = None
pindex = 0
iemode = False

REG_FIFO         =       0x00
REG_OP_MODE      =       0x01
REG_FRF_MSB      =       0x06
REG_FRF_MID      =       0x07
REG_FRF_LSB      =       0x08
REG_PA_CONFIG    =       0x09
REG_OCP          =       0x0b
REG_LNA          =       0x0c
REG_FIFO_ADDR_PTR =      0x0d
REG_FIFO_TX_BASE_ADDR =  0x0e
REG_FIFO_RX_BASE_ADDR =  0x0f
REG_FIFO_RX_CURRENT_ADDR=0x10
REG_IRQ_FLAGS           =0x12
REG_RX_NB_BYTES         =0x13
REG_PKT_SNR_VALUE       =0x19
REG_PKT_RSSI_VALUE      =0x1a
REG_RSSI_VALUE          =0x1b
REG_MODEM_CONFIG_1      =0x1d
REG_MODEM_CONFIG_2      =0x1e
REG_PREAMBLE_MSB        =0x20
REG_PREAMBLE_LSB        =0x21
REG_PAYLOAD_LENGTH      =0x22
REG_MODEM_CONFIG_3      =0x26
REG_FREQ_ERROR_MSB      =0x28
REG_FREQ_ERROR_MID      =0x29
REG_FREQ_ERROR_LSB      =0x2a
REG_RSSI_WIDEBAND       =0x2c
REG_DETECTION_OPTIMIZE  =0x31
REG_INVERTIQ            =0x33
REG_DETECTION_THRESHOLD =0x37
REG_SYNC_WORD           =0x39
REG_INVERTIQ2           =0x3b
REG_DIO_MAPPING_1       =0x40
REG_VERSION             =0x42
REG_PA_DAC              =0x4d

# modes
MODE_LONG_RANGE_MODE    =0x80
MODE_SLEEP              =0x00
MODE_STDBY              =0x01
MODE_TX                 =0x03
MODE_RX_CONTINUOUS      =0x05
MODE_RX_SINGLE          =0x06

# PA config
PA_BOOST                =0x80

# IRQ masks
IRQ_TX_DONE_MASK          =0x08
IRQ_PAYLOAD_CRC_ERROR_MASK=0x20
IRQ_RX_DONE_MASK          =0x40

RF_MID_BAND_THRESHOLD   =525E6
RSSI_OFFSET_HF_PORT     =157
RSSI_OFFSET_LF_PORT     =164

MAX_PKT_LENGTH          =255



                  
def spiWrite(reg,data):
    msg = bytearray()
    msg.append(0x00|reg)
    msg.append(data)
    cs.value(0)
    spi.write(msg)
    cs.value(1)
    
def spiRead(reg,nbytes=1):
    if nbytes <1:
        return bytearray()
    elif nbytes == 1:
        mb=0
    else:
        mb=1
    msg = bytearray()
    af = reg & 0x7F
    msg.append(af)
    #msg.append(af >> 8)
    #msg.append(0x80 | (mb << 6) | reg)
    cs.value(0)
    spi.write(msg)
    data = spi.read(nbytes)
    cs.value(1)
    return data
            
def writeRegister(reg,val):
    msg = bytearray()
    msg.append(reg | 0x80)
    msg.append(val)
    cs.value(0)
    spi.write(msg)
    ndata = spi.read(1)
    cs.value(1)
    return ndata
    
def readRegister(reg):
    msg = bytearray()
    msg.append(reg & 0x7F)
    cs.value(0)
    spi.write(msg)
    ndata = spi.read(1)
    cs.value(1)
    return ndata[0]

def sleep():
    writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_SLEEP)
    
    
def idle():
    writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_STDBY)

def enableCRC(en):
    mreg = readRegister(REG_MODEM_CONFIG_1)
    if en:
        writeRegister(REG_MODEM_CONFIG_1,mreg|0x04)
    else:
        writeRegister(REG_MODEM_CONFIG_1,mreg&0xFB)




    
def setFrequency(freq):
    global _frequency
    if freq < 410 or freq >525:
        return False
    else:
        #print("freq OK")
        lfrq = freq * 1000000
        _frequency = lfrq
        frf = int((lfrq << 19) / 32000000)
        writeRegister(REG_FRF_MSB,frf>>16)
        writeRegister(REG_FRF_MID,(frf>>8)&0xFF)
        writeRegister(REG_FRF_LSB,frf & 0xFF)
        return True
    
def LoRaOCP(ma):
    ocptrim = 27
    if ma <=120:
        ocptrim = int((ma-45)/5)
    elif ma <=240:
        ocptrim = int((ma+30)/10)
    writeRegister(REG_OCP,0x20 | (0x1F & ocptrim))
    
def setTxPower(power):
    writeRegister(0x4D,0x87)
    LoRaOCP(140)
    writeRegister(0x09,0x80| 0x0C)
    
def isTransmitting():
    egx = readRegister(REG_OP_MODE) & MODE_TX
    if egx == MODE_TX:
        return True
    pmx = readRegister(REG_IRQ_FLAGS) & IRQ_TX_DONE_MASK
    
    if pmx:
        writeRegister(REG_IRQ_FLAGS,IRQ_TX_DONE_MASK)
    return False

def explicitHeaderMode():
    global _implicitHeaderMode
    _implicitHeaderMode = False
    px1 =  readRegister(REG_MODEM_CONFIG_1) & 0xfe
    writeRegister(REG_MODEM_CONFIG_1,px1)


def implicitHeaderMode():
    global _implicitHeaderMode
    _implicitHeaderMode = True
    px1 =  readRegister(REG_MODEM_CONFIG_1) & 0x01
    writeRegister(REG_MODEM_CONFIG_1,px1)



def beginPacket(header=0):
    psm = isTransmitting()
    if psm:
        #print("Lora is in TX Mode")
        return False
    idle()
    if header>0:
        implicitHeaderMode()
    else:
        explicitHeaderMode()

    writeRegister(REG_FIFO_ADDR_PTR, 0)
    writeRegister(REG_PAYLOAD_LENGTH, 0)

    return True
    
def dataPacket(buff):
    size = len(buff)
    paylen = readRegister(REG_PAYLOAD_LENGTH)
    if paylen + size > 255:
        size = 255 - paylen
        
    for x in buff:
        writeRegister(0x00,x)
    writeRegister(REG_PAYLOAD_LENGTH,paylen+size)
    return size

def endPacket(async1 = False):
    if async1 == True and _onTxDone == True:
        writeRegister(REG_DIO_MAPPING_1, 0x40)
    writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_TX)
    if not async1:
        while readRegister(REG_IRQ_FLAGS) & IRQ_TX_DONE_MASK == 0:
            pass
        writeRegister(REG_IRQ_FLAGS, IRQ_TX_DONE_MASK)
    return True


def parsePacket(psize=0):
    global pindex
    packetLength = 0
    irqFlags = readRegister(REG_IRQ_FLAGS)
    if psize > 0:
        implicitHeaderMode()
        writeRegister(REG_PAYLOAD_LENGTH, size & 0xff)
    else:
        explicitHeaderMode()

    writeRegister(REG_IRQ_FLAGS, irqFlags);

    if irqFlags & 0x40 == 0 and irqFlags & 0x20 ==0:
        #print("here1")
        pindex = 0
        if _implicitHeaderMode:
            packetLength = readRegister(REG_PAYLOAD_LENGTH)
        else:
            packetLength = readRegister(REG_RX_NB_BYTES);
        writeRegister(REG_FIFO_ADDR_PTR, readRegister(REG_FIFO_RX_CURRENT_ADDR))
        idle()
    elif readRegister(REG_OP_MODE) != (MODE_LONG_RANGE_MODE | MODE_RX_SINGLE):
        #print("here2")
        writeRegister(REG_FIFO_ADDR_PTR, 0)
        writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_RX_SINGLE)
    return packetLength
    

def available():
    return readRegister(REG_RX_NB_BYTES) - pindex
    
            
def read():
    global pindex
    if available() == 0:
        return -1
    pindex = pindex + 1
    return readRegister(REG_FIFO)
        
def readBuffer():
    pkt_size = parsePacket()
    rmp = available()
    buff1 = []
    if rmp > 0:
        for x in range (0,pkt_size):
            buff1.append(readRegister(REG_FIFO))
        return buff1
    else:
        return []


def receive(psize):
    writeRegister(REG_DIO_MAPPING_1, 0x00)
    if size>0:
        implicitHeaderMode()
    else:
        explicitHeaderMode()
    writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_RX_CONTINUOUS)


def packetRssi():
    pgx = readRegister(REG_PKT_RSSI_VALUE)
    if _frequency < RF_MID_BAND_THRESHOLD:
        return pgx - RSSI_OFFSET_LF_PORT
    else:
        return pgx - RSSI_OFFSET_HF_PORT

def getSignalBandwidth():
    mox1 = readRegister(REG_MODEM_CONFIG_1) >> 4
    if mox1 == 0:
        return 7.8E3
    elif mox1 == 1:
        return 10.4E3
    elif mox1 == 2:
        return 15.6E3
    elif mox1 == 3:
        return 20.8E3
    elif mox1 == 4:
        return 31.25E3
    elif mox1 == 5:
        return 41.7E3
    elif mox1 == 6:
        return 62.5E3
    elif mox1 == 7:
        return 125E3
    elif mox1 == 8:
        return 250E3
    elif mox1 == 9:
        return 500E3


def setSignalBandwidth(bw):
    if bw >=0 and bw <=9:
        mox1 = readRegister(REG_MODEM_CONFIG_1) & 0x0F | (bw << 4)
        writeRegister(REG_MODEM_CONFIG_1,mox1)
        return True
    else:
        return False


def begin(spip,csp,rstp,dio0p,freq):
    global rst,spi,cs,dio0
    spi = spip
    cs = csp
    rst = rstp
    dio0 = dio0p
    if rstp != None:
        rst.value(0)
        time.sleep(1)
        rst.value(1)
        #print("rset OK")
    ndata = readRegister(REG_VERSION)
    if ndata != 0x12:
        return False
    sleep()
    setFrequency(freq)
    writeRegister(REG_FIFO_TX_BASE_ADDR, 0);
    writeRegister(REG_FIFO_RX_BASE_ADDR, 0);
    erpm = readRegister(REG_LNA)
    writeRegister(REG_LNA, erpm | 0x03);
    writeRegister(REG_MODEM_CONFIG_3, 0x04);
    setTxPower(17)
    idle()
    return True
    