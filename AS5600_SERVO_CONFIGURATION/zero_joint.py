#!/usr/bin/env python3
from smbus2 import SMBus
import time, json, os

I2C_BUS = 1
MUX_ADDR = 0x70
AS5600_ADDR = 0x36
CONFIG_FILE = "joints_config.json"

bus = SMBus(I2C_BUS)

def select_channel(ch):
    bus.write_byte(MUX_ADDR, 1 << ch)
    time.sleep(0.001)

def read_raw_angle(channel):
    select_channel(channel)
    data = bus.read_i2c_block_data(AS5600_ADDR, 0x0E, 2)
    raw = ((data[0] << 8) | data[1]) & 0x0FFF
    return raw * 360.0 / 4096.0

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"joints": []}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

if __name__ == "__main__":
    cfg = load_config()
    joints = cfg["joints"]

    print("Available joints:")
    for i, j in enumerate(joints):
        print(f"{i}: {j['name']} (channel {j['channel']})")

    idx = int(input("Select joint index to calibrate: "))
    joint = joints[idx]

    print(f"Move {joint['name']} to mechanical zero.")
    input("Press Enter to set zero...")

    raw = read_raw_angle(joint["channel"])
    joint["zero_offset"] = raw
    save_config(cfg)

    print(f"✅ {joint['name']} zero set at raw={raw:.2f}°")
    bus.close()
