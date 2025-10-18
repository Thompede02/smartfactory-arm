#!/usr/bin/env python3
"""
Auto-center the servo so that a 0° command reads ~0° on the AS5600.

Usage:
  python3 servo_zero.py --joint joint0
Options:
  --tol <deg>        tolerance in degrees (default 0.5)
  --max-steps <N>    max iterations (default 20)
  --alpha <0..1>     fraction of correction each step (default 0.7)
"""

import json, sys, time, argparse
from smbus2 import SMBus, i2c_msg

CONFIG_FILE = "joints_config.json"

# I2C addresses (fixed by your hardware)
I2C_BUS = 1
MUX_ADDR = 0x70
AS5600_ADDR = 0x36

def load_cfg():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_cfg(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")

def get_joint(cfg, name):
    for j in cfg["joints"]:
        if j.get("name") == name:
            return j
    sys.exit(f"[ERR] Joint '{name}' not found in {CONFIG_FILE}. Available: {[x['name'] for x in cfg['joints']]}")

def select_mux(bus, ch, settle=0.002):
    bus.write_byte(MUX_ADDR, 1 << int(ch))
    time.sleep(settle)

def read_raw_deg(bus, angle_reg="ANGLE"):
    # ANGLE: 0x0E/0x0F; RAW: 0x0C/0x0D
    reg = 0x0E if angle_reg == "ANGLE" else 0x0C
    d = bus.read_i2c_block_data(AS5600_ADDR, reg, 2)
    raw = ((d[0] << 8) | d[1]) & 0x0FFF
    return raw * 360.0 / 4096.0

def norm_pm180(x):
    x = (x + 180.0) % 360.0
    return x - 360.0 if x > 180.0 else x

def calibrated(raw_deg, zero_offset, invert):
    v = raw_deg - zero_offset
    if invert:
        v = -v
    return norm_pm180(v)

def send_us(bus, esp_addr, ch, us):
    # Write 3 bytes to ESP32 slave: [channel, us_hi, us_lo]
    us = max(0, min(65535, int(us)))
    payload = bytes([ch & 0xFF, (us >> 8) & 0xFF, us & 0xFF])
    bus.i2c_rdwr(i2c_msg.write(esp_addr, payload))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--joint", required=True)
    ap.add_argument("--tol", type=float, default=0.5, help="tolerance in degrees")
    ap.add_argument("--max-steps", type=int, default=20)
    ap.add_argument("--alpha", type=float, default=0.7)
    args = ap.parse_args()

    cfg = load_cfg()
    angle_reg = cfg.get("angle_register", "ANGLE")

    j = get_joint(cfg, args.joint)
    mux_ch = int(j["channel"])
    zero = float(j.get("zero_offset", 0.0))
    invert = bool(j.get("invert", False))

    sv = j.setdefault("servo", {})
    # IMPORTANT: for your setup this should be 8 (0x08). Change if you use a different address.
    esp_addr = int(sv.get("esp32_addr", 8))
    sv_ch = int(sv.get("channel", 0))
    center = int(sv.get("center_us", 1500))
    slope = float(sv.get("us_per_deg", 7.5))  # make NEGATIVE here if direction is reversed
    min_us = int(sv.get("min_us", 700))
    max_us = int(sv.get("max_us", 2300))

    print(f"[info] Auto-centering '{args.joint}' on ESP32 0x{esp_addr:02X}/ch{sv_ch}")
    print("[hint] Make sure you've run zero_joint.py at mechanical zero so AS5600 reads ~0° there.")

    with SMBus(I2C_BUS) as bus:
        # Start at current center; command "0°" (i.e., just center µs since target=0)
        us = max(min_us, min(max_us, center))
        send_us(bus, esp_addr, sv_ch, us)
        time.sleep(0.3)

        for step in range(1, args.max_steps + 1):
            select_mux(bus, mux_ch)
            raw = read_raw_deg(bus, angle_reg)
            ang = calibrated(raw, zero, invert)  # measured angle (deg)

            err = ang  # we want 0.0°
            print(f"step {step:02d}: center_us={us:4d}  angle={ang:+6.2f}°  err={err:+6.2f}°")

            if abs(err) <= args.tol:
                print("✅ within tolerance.")
                break

            # Adjust center by slope * error (µs/deg) * alpha
            delta_us = - err * slope * args.alpha
            # keep the adjustment sane
            delta_us = int(round(max(-150, min(150, delta_us))))
            us = max(min_us, min(max_us, us + delta_us))
            send_us(bus, esp_addr, sv_ch, us)
            time.sleep(0.25)

    # Save final center back to JSON so future commands use it
    sv["center_us"] = int(us)
    save_cfg(cfg)
    print(f"[ok] Saved center_us={us} in {CONFIG_FILE}")

if __name__ == "__main__":
    main()
