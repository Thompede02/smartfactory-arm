#!/usr/bin/env python3
# Fit us_per_deg robustly (handles ±180° wrap) and updates joints_config.json.
import json, time, sys, argparse
from smbus2 import SMBus, i2c_msg

CFG="joints_config.json"; BUS=1; MUX=0x70; AS=0x36

def load(): return json.load(open(CFG))
def save(c): json.dump(c, open(CFG,"w"), indent=2); open(CFG,"a").write("\n")
def getj(cfg,name):
    for j in cfg["joints"]:
        if j["name"]==name: return j
    sys.exit(f"[ERR] joint '{name}' not in {CFG}")

def send_us(bus, addr, ch, us):
    us = max(700, min(2300, int(us)))
    bus.i2c_rdwr(i2c_msg.write(addr, bytes([ch, (us>>8)&0xFF, us & 0xFF])))

def sel(bus,ch): bus.write_byte(MUX, 1<<int(ch)); time.sleep(0.003)

def raw_deg(bus, angle_reg="ANGLE"):
    reg = 0x0E if angle_reg=="ANGLE" else 0x0C
    d = bus.read_i2c_block_data(AS, reg, 2)
    raw = ((d[0]<<8)|d[1]) & 0x0FFF
    return raw * 360.0 / 4096.0

def norm_pm180(x):
    x = (x+180.0) % 360.0
    return x-360.0 if x > 180.0 else x

def calibrated(raw_deg, zero_off, inv):
    v = raw_deg - zero_off
    if inv: v = -v
    return norm_pm180(v)

def ang_diff(a2, a1):
    """smallest signed difference a2 - a1 in (-180,180] degrees"""
    d = (a2 - a1 + 180.0) % 360.0 - 180.0
    return d if d != -180.0 else 180.0

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--joint", default="joint0")
    ap.add_argument("--span", type=int, default=120, help="±span µs around center (smaller avoids wrap)")
    args=ap.parse_args()

    cfg=load(); angle_reg=cfg.get("angle_register","ANGLE")
    j=getj(cfg,args.joint)
    mux=int(j["channel"]); zero=float(j.get("zero_offset",0.0)); inv=bool(j.get("invert",False))
    sv=j.setdefault("servo",{})
    addr=int(sv.get("esp32_addr", 8)); ch=int(sv.get("channel", 0))
    center=int(sv.get("center_us",1500))
    min_us=int(sv.get("min_us",700)); max_us=int(sv.get("max_us",2300))

    u1=max(min_us, min(max_us, center - args.span))
    u2=max(min_us, min(max_us, center + args.span))
    print(f"[info] fitting {args.joint}: u1={u1} µs, u2={u2} µs  (center={center})")

    with SMBus(BUS) as bus:
        send_us(bus, addr, ch, u1); time.sleep(0.4); sel(bus, mux)
        a1 = calibrated(raw_deg(bus, angle_reg), zero, inv)

        send_us(bus, addr, ch, u2); time.sleep(0.4); sel(bus, mux)
        a2 = calibrated(raw_deg(bus, angle_reg), zero, inv)

    da = ang_diff(a2, a1)   # wrap-safe small signed change
    if abs(da) < 0.2:
        sys.exit(f"[ERR] too little motion between {u1} and {u2} (Δ={da:.2f}°). "
                 f"Increase --span or check linkage/free play.")

    us_per_deg = (u2 - u1) / da   # sign encodes direction
    sv["us_per_deg"] = float(us_per_deg)
    save(cfg)

    print(f"[ok] us_per_deg = {us_per_deg:.3f} µs/deg (saved to {CFG})")
    sabs = abs(us_per_deg)
    pos_deg = (max_us - center)/sabs
    neg_deg = (center - min_us)/sabs
    print(f"[info] approx reachable: -{neg_deg:.1f}° .. +{pos_deg:.1f}° before hitting {min_us}/{max_us} µs")
    print(f"[try]  python3 servo_deg.py --joint {args.joint} --deg 30")
