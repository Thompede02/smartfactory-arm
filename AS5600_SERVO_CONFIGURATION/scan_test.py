#!/usr/bin/env python3
# scan_mux_all.py — list I2C devices per TCA9548A channel
from smbus2 import SMBus
import time

BUS = 1
MUX_ADDR = 0x70
# channels to scan (edit to 0..5 if you only wired 6)
CHANNELS = list(range(8))
# address range to probe (skip 0x00..0x02, scan 0x03..0x77 like i2cdetect)
ADDRS = list(range(0x03, 0x78))

def mux_select(bus, ch):
    bus.write_byte(MUX_ADDR, 1 << ch)
    time.sleep(0.001)  # 1 ms settle

def present(bus, addr):
    try:
        # SMBus "read byte" without a register; many devices NACK if absent
        bus.read_byte(addr)
        return True
    except OSError:
        return False

if __name__ == "__main__":
    with SMBus(BUS) as bus:
        # make sure no channel is stuck on from previous session
        try: bus.write_byte(MUX_ADDR, 0x00)
        except Exception: pass

        print("Scanning TCA9548A channels...")
        for ch in CHANNELS:
            try:
                mux_select(bus, ch)
            except OSError as e:
                print(f"CH{ch}: [mux select error: {e}]")
                continue

            found = []
            for a in ADDRS:
                if a == MUX_ADDR:   # upstream mux is always visible; skip
                    continue
                if present(bus, a):
                    found.append(a)

            if found:
                hexlist = " ".join(f"0x{a:02X}" for a in found)
                print(f"CH{ch}: {hexlist}")
            else:
                print(f"CH{ch}: (no devices)")

        # hygiene: disable all channels
        try: bus.write_byte(MUX_ADDR, 0x00)
        except Exception: pass
