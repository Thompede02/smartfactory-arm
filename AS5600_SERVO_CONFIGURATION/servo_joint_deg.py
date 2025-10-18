#!/usr/bin/env python3
# Sends joint degrees; maps to servo degrees using JSON ratio/center.
import json, sys, argparse
from smbus2 import SMBus, i2c_msg

CFG="joints_config.json"; I2C_BUS=1
def load(): return json.load(open(CFG))
def get_joint(cfg,name):
    for j in cfg["joints"]:
        if j.get("name")==name: return j
    sys.exit(f"[ERR] Joint '{name}' not found. Available: {[x['name'] for x in cfg['joints']]}")

def send_deg(bus, addr, ch, deg):
    d = max(0, min(180, int(round(deg))))
    bus.i2c_rdwr(i2c_msg.write(addr, bytes([ch & 0xFF, (d>>8)&0xFF, d & 0xFF])))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--joint", required=True)
    ap.add_argument("--deg", type=float, required=True, help="JOINT degrees")
    args=ap.parse_args()

    cfg=load(); j=get_joint(cfg,args.joint); sv=j.get("servo",{})
    addr=int(sv.get("esp32_addr",8)); ch=int(sv.get("channel",0))
    # clamp by joint limits
    jmin=float(sv.get("min_deg",-80.0)); jmax=float(sv.get("max_deg",80.0))
    jdeg=max(jmin, min(jmax, args.deg))
    # map to servo degrees
    center=float(sv.get("center_deg",90.0))
    k=float(sv.get("servo_deg_per_joint_deg",1.0))  # can be negative (direction)
    sdeg = center + k * jdeg
    sdeg = max(float(sv.get("min_servo_deg",0.0)), min(float(sv.get("max_servo_deg",180.0)), sdeg))

    print(f"[info] joint={args.joint} jdeg={args.deg:.1f} → servo={sdeg:.1f} (center={center}, k={k})")
    with SMBus(I2C_BUS) as bus:
        send_deg(bus, addr, ch, sdeg)
    print("[ok] sent")
