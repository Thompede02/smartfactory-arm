#!/usr/bin/env python3
from math import pi
import os
import yaml
from yaml import safe_load
from rclpy import init, spin, shutdown
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray as JointTargets
import board
import busio
from adafruit_pca9685 import PCA9685


class ServoNode(Node):
    def __init__(self):
        super().__init__("servo_node")
        config = self.load_config()
        joints = config["joints"]
        self.joint_arrays(joints)
        self.setup_hardware()
        self.setup_subscription()

    def load_config(self):
        package_dir = os.path.dirname(__file__)
        config_path = os.path.join(package_dir, "ers6_hardware.yaml")

        with open(config_path) as f:
            cfg = safe_load(f)
            return cfg

    def joint_arrays(self, joints):
        self.pca_channels = []
        self.signs = []
        self.scales = []
        self.min_us = []
        self.max_us = []
        self.joint_min = []
        self.joint_max = []
        for j in joints:
            self.pca_channels.append(j["servo_channel"])
            self.min_us.append(float(j.get("servo_min_us", 1000.0)))
            self.max_us.append(float(j.get("servo_max_us", 2000.0)))
            self.signs.append(float(j.get("servo_sign", 1.0)))
            self.scales.append(float(j.get("servo_scale", 1.0)))
            self.joint_min.append(j.get("joint_min_rad", None))
            self.joint_max.append(j.get("joint_max_rad", None))
                    

    def setup_hardware(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c, address=0x40)
        self.pca.frequency = 50.0
        self.period_us = 1_000_000.0 / self.pca.frequency


    def setup_subscription(self):
        topic = "/servo_target_rad"
        self.cmd_sub = self.create_subscription(
            JointTargets,
            topic,
            self.cmd_cb,
            10,
        )



    # Helper for Radian-Ticks Conversion
    def rad_to_ticks(self, idx, angle_rad):
        x_raw = self.signs[idx] * self.scales[idx] * float(angle_rad)

        # per-joint clamp (read from YAML)
        jmin = self.joint_min[idx]
        jmax = self.joint_max[idx]
        if jmin is not None and jmax is not None:
            x = max(jmin, min(jmax, x_raw))
        else:
            x = max(-pi / 2, min(pi / 2, x_raw))

        us_min = self.min_us[idx]
        us_max = self.max_us[idx]

        # normalize x in [jmin..jmax] -> [0..1]
        if jmin is not None and jmax is not None and (jmax - jmin) > 1e-9:
            t = (x - jmin) / (jmax - jmin)
        else:
            t = (x + pi / 2) / pi

        us = us_min + (us_max - us_min) * t

        ticks_f = us * 4096.0 / self.period_us
        ticks = int(ticks_f)
        return max(0, min(4095, ticks))







    def cmd_cb(self, msg):
        for idx, angle in enumerate(msg.data):
            if idx >= len(self.pca_channels):
                continue

            channel = self.pca_channels[idx]
            ticks = self.rad_to_ticks(idx, angle)
            duty = ticks << 4

            self.pca.channels[channel].duty_cycle = duty


def main(args=None):
    init(args=args)
    node = ServoNode()
    try:
        spin(node)
    except KeyboardInterrupt:
        pass
    shutdown()


if __name__ == "__main__":
    main()
