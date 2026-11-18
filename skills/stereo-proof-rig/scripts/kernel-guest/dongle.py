#!/usr/bin/python3 -I
# a stand-in for the dongle's hidraw node: a uhid device with a vendor page and no meaning; it exists while this runs
import os, struct, sys, time
RD = bytes([0x06,0x00,0xFF,0x09,0x01,0xA1,0x01,0x15,0x00,0x26,0xFF,0x00,0x75,0x08,0x95,0x01,0x09,0x02,0x81,0x02,0xC0])
fd = os.open('/dev/uhid', os.O_RDWR)
os.write(fd, struct.pack('<I128s64s64sHHIIII4096s', 11, b'HyperX dongle stand-in', b'', b'gr108-test-dongle', len(RD), 0x03, 0x03f0, 0x018b, 0, 0, RD.ljust(4096, b'\0')))
time.sleep(float(sys.argv[1]) if len(sys.argv) > 1 else 3600)
