#!/usr/bin/env python3
# servo_deg.py — send absolute servo degrees (0..180) to ESP32 over I2C
import json, sys, argparse
from smbus2 import SMBus, i2c_msg

CFG = "joints_config.json"
I2C_BUS = 1

def load():
    with open(CFG, "r") as f: return json.load(f)

def get_joint(cfg, name):
    for j in cfg["joints"]:
        if j.get("name") == name:
            return j
    sys.exit(f"[ERR] Joint '{name}' not found. Available: {[x['name'] for x in cfg['joints']]}")

def send_deg(bus, addr, ch, deg):
    d = max(0, min(180, int(round(deg))))
    payload = bytes([ch & 0xFF, (d >> 8) & 0xFF, d & 0xFF])
    bus.i2c_rdwr(i2c_msg.write(addr, payload))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Send servo degrees (0..180) to ESP32 degree bridge")
    ap.add_argument("--joint", required=True)
    ap.add_argument("--deg", type=float, required=True)
    args = ap.parse_args()

    cfg = load()
    j = get_joint(cfg, args.joint)
    sv = j.get("servo", {})
    addr = int(sv.get("esp32_addr", 8))   # 0x08
    ch   = int(sv.get("channel", 0))

    print(f"[info] joint={args.joint} servo_deg={args.deg:.1f} → 0x{addr:02X}/ch{ch}")
    with SMBus(I2C_BUS) as bus:
        send_deg(bus, addr, ch, args.deg)
    print("[ok] sent")
