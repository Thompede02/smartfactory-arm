#!/usr/bin/env python3
from smbus2 import SMBus
import time, json, os

I2C_BUS = 1
MUX_ADDR = 0x70
AS5600_ADDR = 0x36
CONFIG_FILE = "joints_config.json"

bus = SMBus(I2C_BUS)

def select_channel(ch):
    # One-hot bitmask (only one channel enabled at a time)
    bus.write_byte(MUX_ADDR, 1 << int(ch))
    # Short settle; 0.3–0.5 ms is usually fine
    time.sleep(0.0004)

def read_status_selected():
    # STATUS 0x0B (assumes channel already selected)
    s = bus.read_byte_data(AS5600_ADDR, 0x0B)
    md = bool(s & 0x20)  # magnet detected
    ml = bool(s & 0x10)  # too weak
    mh = bool(s & 0x08)  # too strong
    return md, ml, mh

def read_raw_angle_selected(reg_base=0x0E):
    # ANGLE at 0x0E/0x0F (RAW_ANGLE is 0x0C/0x0D)
    data = bus.read_i2c_block_data(AS5600_ADDR, reg_base, 2)
    raw12 = ((data[0] << 8) | data[1]) & 0x0FFF
    return raw12 * 360.0 / 4096.0

def calibrated_angle(raw, zero_offset, invert=False):
    val = raw - zero_offset
    if invert:
        val = -val
    val = val % 360.0
    if val > 180.0:
        val -= 360.0
    return val

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
        if "joints" in cfg and isinstance(cfg["joints"], list):
            return cfg
    # fallback template
    return {
        "angle_register": "ANGLE",
        "warn_abs_deg": 170.0,
        "joints": [
            {"name": f"joint{i}", "channel": i, "zero_offset": 0.0, "invert": False}
            for i in range(6)
        ]
    }

if __name__ == "__main__":
    cfg = load_config()
    joints = cfg["joints"]
    reg_name = str(cfg.get("angle_register", "ANGLE")).upper()
    reg_base = 0x0E if reg_name == "ANGLE" else 0x0C  # ANGLE vs RAW_ANGLE
    warn_abs = float(cfg.get("warn_abs_deg", 170.0))

    print("Robot Joint Reader (Ctrl+C to exit)\n")
    try:
        while True:
            parts = []
            for j in joints:
                name = j.get("name", "?")
                ch   = int(j.get("channel", 0))
                z    = float(j.get("zero_offset", 0.0))
                inv  = bool(j.get("invert", False))
                try:
                    # Select this channel once
                    select_channel(ch)

                    # Optional: status (kept for nicer diagnostics)
                    try:
                        md, ml, mh = read_status_selected()
                        status_bits = []
                        if md: status_bits.append("MD")
                        if ml: status_bits.append("ML")
                        if mh: status_bits.append("MH")
                        st = ",".join(status_bits) if status_bits else "--"
                    except Exception:
                        st = "NO_STAT"

                    # Read angle WITHOUT reselecting the channel
                    raw = read_raw_angle_selected(reg_base)
                    ang = calibrated_angle(raw, z, inv)
                    lim = "OK" if abs(ang) <= warn_abs else "⚠️"
                    parts.append(f"{name}@CH{ch}: {ang:7.2f}° [{lim}|{st}]")
                except Exception:
                    parts.append(f"{name}@CH{ch}: ---.--° [ERR]")

            print("\r" + " | ".join(parts) + " " * 6, end="")
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        try:
            # disable all mux channels (optional hygiene)
            bus.write_byte(MUX_ADDR, 0x00)
        except Exception:
            pass
        bus.close()
